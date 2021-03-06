from flask import Flask, make_response, redirect, render_template, url_for, request, jsonify
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pymongo import MongoClient
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from forms import SearchForm
import config
import json

app = Flask(__name__, static_url_path='')
app.config.from_object('config')

client = MongoClient()
db = client.enron
emails = db.test_kaminski
email_tags = db.test_tags

email_list = []

for email in emails.find():
    email['_id'] = str(email['_id'])
    action = {
            "_index": config.INDEX,
            "_type": "email",
            "_id": email['_id'],
            "_source": email
            }
    email_list.append(action)

es = Elasticsearch()

if es.indices.exists(index=config.INDEX) is False:
    es.indices.create(index=config.INDEX)

# close index to perform the next few operations
es.indices.close(index=config.INDEX)

# register tokenizer for text search
es.indices.put_settings(index=config.INDEX, body=config.SETTINGS_BODY)

# store email body field for MLT and advanced analysis
es.indices.put_mapping(index=config.INDEX, doc_type='email', body=config.MAPPING_BODY)

es.indices.open(index=config.INDEX)

helpers.bulk(es, email_list)

# convert es search results to python array of dicts
def es_to_dict(results):
    resultset  = []
    if results['hits'] and results['hits']['hits']:
        hits = results['hits']['hits']
        for hit in hits:
            resultset.append(hit['_source'])
    return resultset


# helper function to stringify lists for es queries
def list_to_string(lst):
    new_list = []
    for l in lst:
        l = str(l)
        new_list.append(l)
    word_list = str(new_list).replace('[', '').replace(']', '').replace('\'', '')
    word_list = word_list.encode('utf-8')
    return word_list

@app.route('/')
@app.route('/index')
def index():
    db_name = emails.full_name
    return render_template('landing.html', db_name=db_name)


# get email from mongodb using query by id
@app.route('/email/<message_id>/')
def email_detail(message_id):
    msg = emails.find_one({'_id': ObjectId(message_id)}) 
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

# execute fuzzy keyword search
    elif request.args.get('search'):
        results = es.search(index=config.INDEX, 
                            doc_type='email', 
                            body={
                                  'query': {
                                        'fuzzy_like_this': { 
                                              'fields': ['Subject', 'body'], 
                                              'like_text': query, 
                                              'prefix_length': 4, 
                                              'max_query_terms': 12, 
                                              'boost': 1.2 
                                              }
                                        }, 
                                  'sort': {
                                      '_score': {
                                          'order': 'desc' 
                                          }
                                      }
                                  }, 
                            size=200, 
                            _source=True, 
                            analyze_wildcard=True
                            )
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, flds=flds, total=total, query=query)

# redirect to static page for angularJS functionality
@app.route('/email_search', methods=['GET', 'POST'])
def email_search():
    return make_response(open('app/static/search_form.html').read())


# execute advanced boolean search
@app.route('/emails/adv_search')
def email_adv_search(query=None):

    query = request.args.get('search')
    
    if request.args.get('search'):
        results = es.search(index=config.INDEX, 
                            doc_type='email', 
                            body={
                                  'filter': {
                                      'query': { 
                                          'query_string': { 
                                              'default_field': 'body', 
                                              'query': query 
                                              }
                                          }
                                      }, 
                                   'sort': {
                                       '_score': {
                                           'order': 'desc'
                                           }
                                       }
                                   }, 
                            size=200, 
                            _source=True, 
                            analyze_wildcard=True, 
                            default_operator='AND'
                            ) 
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total, query=query)

@app.route('/emails/mlt/<msg_id>/')
def email_mlt(msg_id=None):

# execute More Like This search of single doc to find similar docs
    results = es.mlt(index=config.INDEX, 
                     doc_type='email', 
                     id=msg_id, 
                     mlt_fields=['body'], 
                     percent_terms_to_match=0.7, 
                     min_doc_freq=1, 
                     min_term_freq=1, 
                     body={
                         'sort': {
                             '_score': {
                                 'order': 'desc'
                                 }
                             }
                         }
                     )
    total = results['hits']['total']
    msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total)

# view and add tags to tag collection
@app.route('/tags', methods=['GET', 'POST'])
def manage_tags():
    if request.method == 'POST':
        tag = json.loads(request.data)
        email_tags.insert(tag)
        return jsonify({'success': True})
    if request.method == 'GET':
        tags = email_tags.find()
        return dumps(tags)

# apply tags to documents


# delete tags
@app.route('/tags_delete', methods=['POST'])
def delete_tags():
    tags = json.loads(request.data)
    for tag in tags:
        email_tags.remove({'name': tag['name']})
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
