# -*- coding: utf-8 -*-

DEFAULT_PORT = 5000
ADDITIVE_FOR_UID = 1000

try:
    from os import getuid

except ImportError:
    def getuid():
        return DEFAULT_PORT - ADDITIVE_FOR_UID

from celery import Celery
from flask import Flask, request, render_template, jsonify
from pprint import pformat
from ner.NER import process_input
import json
import zipfile
import os


app = Flask(__name__)



app.config.update({
    'CELERY_BACKEND': 'mongodb://localhost/celery',
    'CELERY_BROKER_URL': 'amqp://guest:guest@localhost:5672//'
})


def make_celery(app):
    celery = Celery('main', backend=app.config['CELERY_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery


celery = make_celery(app)


@celery.task
def long_running_job(file_name):
    result = ''
    if file_name.split('.')[-1] != 'zip':
        return 'Нужен zip архив!!!'
    with zipfile.ZipFile(file_name) as myzip:
    
        for name in myzip.namelist():
            if name.split('.')[-1] == 'txt':
                with myzip.open(name) as f:
                    text = f.read().decode()
                    result += '<br>'+ name + '<br>'
                    result += process_input(text)
                    result += '<br>' + '=' * 100 + '<br>'                
         
    return result






@app.route("/")
@app.route("/index.html")
def index():
    return render_template(
            'index.html')


@app.route('/process_text', methods=['POST', 'GET'])
def anything():
    text = str(request.form['message'])
    return json.dumps({'status':'OK', 'text':process_input(text)})



@app.route('/uploadajax', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        file_name = './uploads/' + f.filename
        if not os.path.exists('./uploads/'):
            os.makedirs('./uploads/')
        f.save(file_name)
        
        task_id = long_running_job.delay(str(file_name))
        return jsonify({
        
        'task_id': str(task_id)
    }) 


@app.route('/result/<task_id>')
def result(task_id):
    async_result = celery.AsyncResult(task_id)

    return jsonify({
        'ready': async_result.ready(),
        'status': async_result.status,
        'result': async_result.result,
        'task_id': str(async_result.task_id)
    })



if __name__ == "__main__":
    app.run(port=getuid() + 1000, debug=True)
