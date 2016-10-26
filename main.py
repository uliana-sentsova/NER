# -*- coding: utf-8 -*-
try:
    from os import getuid

except ImportError:
    def getuid():
        return 4000

from flask import Flask, request, render_template, jsonify
from pprint import pformat
from ner.NER import process_input
import json
app = Flask(__name__)


@app.route("/")
@app.route("/index.html")
def index():
    return render_template(
            'index.html')


@app.route('/process_text', methods=['POST', 'GET'])
def anything():
    text = str(request.form['message'])
    return json.dumps({'status':'OK', 'text':process_input(text)})



if __name__ == "__main__":
    app.run(port=getuid() + 1000, debug=True)
