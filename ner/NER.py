import string
import os
import subprocess
from os import listdir
from os.path import isfile, join
import json
import pickle
import sys
import sklearn_crfsuite
import argparse
import re

crf_model_path = 'ner/crf_models/CRF_sg_window_1_size_1000_clusters_500'
w2v_clusters_path = 'ner/w2v_dicts/sg_window_1_size_1000_clusters_500.pickl'
w2v = pickle.load(open(w2v_clusters_path, "rb"))
crf = pickle.load(open(crf_model_path, "rb"))


def get_mystem_data_from_text(text):
    '''
    Для текста из файла in_path + file
    Создает размеченный Mystem json out_path + file
    '''
    text = text.replace('\n',' ')
    echo = subprocess.Popen(('echo', text), stdout=subprocess.PIPE)
    subprocess.call([
               './ner/mystem',
              '-e UTF-8',
              '-dicgs',
              '--format',
              'json',
              '-',
              'temp'], stdin=echo.stdout)



def get_mystem_data_from_file(file):
    '''
    Для текста из файла in_path + file
    Создает размеченный Mystem json out_path + file
    '''
    with open(in_path + file,'r') as f:
        text = f.read()
        text = text.replace('\n',' ')
    echo = subprocess.Popen(('echo', text), stdout=subprocess.PIPE)
    subprocess.call([
               'ner/mystem',
              '-e UTF-8',
              '-dicgs',
              '--format',
              'json',
              '-',
              out_path + file], stdin=echo.stdout)



def get_data_from_mystem(mystem_result):
    data = [] # список элементами которого являются предложения
    sent = [] # список описывающий предложение, элемент списка, словарь описывающий токен
   
    index = 0
    for element in mystem_result:
        #если текущий элемент не символ конца предложения
        if '\\s' not in element['text']:
            token = {}
            token['text'] = element['text'] # непосредственно сам токен
            token['index'] = index # индекс начала токена в тексте
            index += len(element['text'])
            #если для токена есть анализ
            if 'analysis' in element.keys():
                token['has_analysis'] = True

                #если анализ не пустой
                if len(element['analysis'])!=0:
                    #если в анализе есть грамматика
                    if 'gr' in element['analysis'][0].keys():
                        gram = element['analysis'][0]['gr']
                        token['gram'] = gram
                        token['POS'] = get_pos_from_gram(gram)
                    else:
                        token['gram'] = 'UNKN'
                        token['POS'] = 'UNKN'
                    #если в анализе есть лемма
                    if 'lex' in element['analysis'][0].keys():
                        token['lem'] = element['analysis'][0]['lex']
                    else:
                        token['lem'] = element['text']
                else:
                    token['gram'] = 'UNKN'
                    token['POS'] = 'UNKN'
                    token['lem'] = element['text']

            #если анализа нет
            else:
                token['has_analysis'] = False
                token['gram'] = 'UNKN'
                token['POS'] = 'UNKN'
                token['lem'] = element['text']
            
            #является ли токен пробелом, концом строки и тп
            if element['text'].strip() == '':
                token['whitespace'] = True
            else:
                token['whitespace'] = False
            
            #добавляем токен в конец предложения
            sent.append(token)
        
        # если предложение закончилось
        else:
            data.append(sent) # добавляем предложение в список
            sent = [] # создаем слдующее предложени
    data.append(sent) # добавляем предложение в список

    return data


def get_pos_from_gram(gram):
    '''
    функция извлекающая часть речи
    '''    
    return gram.split(',')[0].split('=')[0]



def word2features(sent, i, w2v_clust=False):
    word = sent[i]['text']
    postag = sent[i]['POS']

    lem =sent[i]['lem']
        
    features = {
        'bias': 1.0,
        'word.lem': lem,
        'word[-3:]': lem[-3:],
        'word[-2:]': lem[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'postag': postag
        
                
    }
    if w2v_clust:
        features.update({
            'w2v_clust':str(w2v.get(lem+'_'+postag,-1)) })
                
    if i > 0:
        word1 = sent[i-1]['text']
        postag1 = sent[i-1]['POS']
       
        lem1 =sent[i-1]['lem']
        features.update({
            '-1:word.lem':lem1,
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
            '-1:postag': postag1
            
        })
    else:
        features['BOS'] = True
        
    if i < len(sent)-1:
        word1 = sent[i+1]['text']
        postag1 = sent[i+1]['POS']
        
        lem1 =sent[i+1]['lem']
        features.update({
            '+1:word.lem': lem1,
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
            '+1:postag': postag1
            
        })
    else:
        features['EOS'] = True
                
    return features


def sent2features(sent,w2v=False):
    return [word2features(sent, i, w2v) for i in range(len(sent))]
 
def sent2labels(sent):
    return [word['BIO'] for word in sent]



def createParser ():
    parser = argparse.ArgumentParser()
    # Путь, где лежит коллекция текстов
    parser.add_argument('-i', '--input', default='ner/texts/')
    # Папка с результатами
    parser.add_argument('-o', '--output', default='ner/NER/')
    # Испоьзовать w2v кластеры
    parser.add_argument('-c','--clusters', default = True)
    # Путь к CRF-модели
    parser.add_argument('-m','--model', default = 'ner/crf_models/CRF_sg_window_1_size_1000_clusters_500')
    # Путь к словарю слово-кластер
    parser.add_argument('-d','--dictionary', default = 'v')
    # Путь к папке с BIO разметкой
    parser.add_argument('-b', '--bio', default = 'ner/BIO/')
    # Путь к папке с файлами обработанными Mystem
    parser.add_argument('-p', '--parsed', default = 'ner/parsed/')

    
    return parser



def check_folder(path):
    '''добавляет в конце пути "/" если его нeт'''
    return path if path[-1]=='/' else path + '/'

def main():
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    USE_W2V_CLUSTERS = namespace.clusters

    crf_model_path = namespace.model

    w2v_clusters_path = namespace.dictionary

    in_path = check_folder(namespace.input)

    dialog_ner_path = check_folder(namespace.output)


    BIO_path = check_folder(namespace.bio) 
    out_path = check_folder(namespace.parsed) 



    if USE_W2V_CLUSTERS:
        w2v = pickle.load( open( w2v_clusters_path, "rb" ) )




    if not os.path.exists(dialog_ner_path):
        os.makedirs(dialog_ner_path)




    if not os.path.exists(out_path):
        os.makedirs(out_path)



    if not os.path.exists(BIO_path ):
        os.makedirs(BIO_path )




    files = sorted([f for f in listdir(in_path) if isfile(join(in_path, f)) and f[-1]!='~'])


    #обрабатываем наши фалы mystem
    for file in files:
        get_mystem_data_from_text(file)



    #загрузка crf модели
    crf = pickle.load( open( crf_model_path, "rb" ) )



    #извлекаем данные из файлов сгенерированныз Mystem
    for file in files:
        with open(out_path + file, 'r') as f:
            json_text = json.load(f)
        base_data = get_data_from_mystem(json_text)

        data = []
        #удаляем пробельные токены
        for i in range(len(base_data)):
            sent=[]
            for j in range(len(base_data[i])):
                if not base_data[i][j]['whitespace']:
                    sent.append(base_data[i][j])
            data.append(sent)
        
        #извлекаем именованные сущности
        X_test= [sent2features(s,USE_W2V_CLUSTERS) for s in data]
        y_pred = crf.predict(X_test)

        #создаем файлы с BIO разметкой
        with open(BIO_path+file,'w') as f:
            for i in range(len(data)):
                for j in range(len(data[i])):
                    data[i][j]['BIO']= y_pred[i][j]
                    f.write('{}\t{}\t{}\n'.format(data[i][j]['text'],data[i][j]['BIO'],data[i][j]['index']))

        #создаем файлы с разметкой  FactRuEval 2016
        with open((dialog_ner_path+file).rsplit('.',1)[0]+'.task1','w') as f:
            for i in range(len(data)):
                j=0
                while j < len(data[i]):
                    if data[i][j]['BIO'].startswith('B_'):

                        in_tag = data[i][j]['BIO'].replace('B','I')

                        NE={
                            'type':data[i][j]['BIO'].split('_')[1].upper(),
                            'index': data[i][j]['index'],
                            'len':len(data[i][j]['text'])    
                        }
                        j+=1
                        while j < len(data[i]) and data[i][j]['BIO'] == in_tag:
                            NE['len'] +=len(data[i][j]['text']) + data[i][j]['index'] -data[i][j-1]['index'] - len(data[i][j-1]['text'])
                            j+=1

                        f.write('{} {} {}\n'.format(NE['type'],NE['index'],NE['len']))
                    else:
                        j+=1


def process_input(text):

    #обрабатываем наши фалы mystem
    get_mystem_data_from_text(text)


    #извлекаем данные из файлов сгенерированныз Mystem
    
    json_text = json.load(open('temp'))
    base_data = get_data_from_mystem(json_text)
    data = []
    #удаляем пробельные токены
    for i in range(len(base_data)):
        sent=[]
        for j in range(len(base_data[i])):
            if not base_data[i][j]['whitespace']:
                sent.append(base_data[i][j])
        data.append(sent)
    
    #извлекаем именованные сущности
    X_test= [sent2features(s,True) for s in data]
    y_pred = crf.predict(X_test)

    #создаем файлы с BIO разметкой
    labeled_text = []
    for i in range(len(data)):
        for j in range(len(data[i])):
            data[i][j]['BIO']= y_pred[i][j]
            labeled_text.append((data[i][j]['text'], data[i][j]['BIO']))

    # преобразуем последовательность в html
    html = ['<p id="result_text">']
    tag = False
    log = open('log.txt', 'w', encoding='utf8')
    for i in range(len(labeled_text)):
        word, label = labeled_text[i]
        # print(repr(word))
        # if word == ',\n' or word == '. ':
        #     word = word.rstrip()
        log.write(word + '\n')
        sep = ''
        # if i != len(labeled_text) -1 and labeled_text[i+1][0] in string.punctuation:
        #     sep = ''
        if (" " not in word and i != len(labeled_text)-1 and ' ' not in labeled_text[i+1][0]
            and labeled_text[i+1][0] not in string.punctuation):
            sep = ' '
        if label == 'O':
            if tag:
                html.append('</mark>')
            tag = False
            html.append(word + sep)


        else:
            if label.startswith('B_'):
                if tag:
                    html.append('</mark>')
                tag = True
                html.append('<mark class="{}">'.format(label[2:]))
                html.append(word + sep)
            else:
                html.append(word + sep)
    if tag:
        html.append('</mark>')
    html.append('</p>')
    html = re.sub('[\r\n]', '<br/>', ''.join(html))
    log.write(repr(html))
    log.close()
    return html

if __name__ == '__main__':
    main()
