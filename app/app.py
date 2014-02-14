from flask import Flask, redirect, render_template, url_for, request
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pymongo import MongoClient
from bson.json_util import dumps, loads
import config

app = Flask(__name__, static_url_path='')

client = MongoClient()
db = client.enron
emails = db.test_kaminski

email_list = []

for email in emails.find():
    #e = dumps(email)
    #e_dict = dict(e)
    email['_id'] = str(email['_id'])
    action = {
            "_index": "test_kaminski",
            "_type": "email",
            "_id": email['_id'],
            "_source": email
            }
    email_list.append(action)

es = Elasticsearch()
helpers.bulk(es, email_list)

# convert es search results to python array of dicts
def es_to_dict(results):
    resultset  = []
    if results['hits'] and results['hits']['hits']:
        hits = results['hits']['hits']
        for hit in hits:
            resultset.append(hit['_source'])
    return resultset

@app.route('/')
@app.route('/index')
def index():
    db_name = emails.full_name
    return render_template('landing.html', db_name=db_name)

@app.route('/email/<message_id>/')
def email_detail(message_id):
    # get email from mongodb using query by id
    msg = emails.find_one({'Message-ID': message_id}) 
    msg_id = str(msg['_id'])
    return render_template('detail.html', msg=msg)

@app.route('/emails')
@app.route('/emails/')
def email_list(query=None, msg_id=None):

    flds = config.LIST_VIEW_FIELDS
    query = request.args.get('search')

# if no search, return all results, limit to 200 for debugging purposes
    if query is None:
        msgs = emails.find(fields=flds, limit=200)
        total = msgs.count()

# execute basic keyword search
    elif request.args.get('search'):
        results = es.search(index='test_kaminski', doc_type='email', body={'query': { 'query_string': { 'default_field': 'body', 'query': query }}, 'sort': {'_score': {'order': 'desc'}}}, size=100, _source=True, analyze_wildcard=True, default_operator='AND') 
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, flds=flds, total=total, query=query)

@app.route('/emails/adv_search')
def email_adv_search(query=None):

    query = request.args.get('search')
    
# execute advanced boolean search
    if request.args.get('search'):
        results = es.search(index='test_kaminski', doc_type='email', body={'query': {'more_like_this': { 'fields': ['Subject', 'body'], 'like_text': query, 'percent_terms_to_match': 0.6, 'min_term_freq': 1, 'min_doc_freq': 1, 'max_query_terms': 12, 'boost': 1.2 }}, 'sort': {'_score': {'order': 'desc' }}}, size=100, _source=True, analyze_wildcard=True)
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total, query=query)

@app.route('/emails/mlt')
def email_mlt(query=None, msg_id=None):

    query = request.args.get('search')
    msg = emails.find_one({'_id': msg_id })

# execute More Like This search of single doc to find similar docs
# Note: In order to use the mlt feature a mlt_field needs to be either be stored, store term_vector or source needs to be enabled.
    if request.args.get('search'):
        results = es.mlt(index='test_kaminski', doc_type='email', id=msg_id)
        #query = msg['body']
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total, query=query)

if __name__ == '__main__':
    app.run(debug=True)
