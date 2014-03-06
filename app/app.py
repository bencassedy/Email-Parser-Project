from flask import Flask, make_response, redirect, render_template, url_for, request
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pymongo import MongoClient
from bson.json_util import dumps, loads
from forms import SearchForm
import config

app = Flask(__name__, static_url_path='')
app.config.from_object('config')

client = MongoClient()
db = client.enron
emails = db.test_kaminski

email_list = []

for email in emails.find():
    #e = dumps(email)
    #e_dict = dict(e)
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

## helper function to sort mongodb keys, for use in search forms
#def keys_to_sorted_list(k):
#    keys = []
#    keys.append(str(emails.distinct(k)))
#    sorted_keys = keys.sort()
#    return sorted_keys

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
        results = es.search(index=config.INDEX, doc_type='email', body={'query': {'fuzzy_like_this': { 'fields': ['Subject', 'body'], 'like_text': query, 'prefix_length': 4, 'max_query_terms': 12, 'boost': 1.2 }}, 'sort': {'_score': {'order': 'desc' }}}, size=100, _source=True, analyze_wildcard=True)
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, flds=flds, total=total, query=query)

@app.route('/email_search', methods=['GET', 'POST'])
#def email_search():
#    form = SearchForm()
#    form.folders.choices = [(f, f) for f in emails.distinct('X-Folder')]
#    form.custodians.choices = [(f, f) for f in emails.distinct('X-Origin')]
#    form.recipients.choices = [(f, f) for f in emails.distinct('To')]
#    if request.method == 'POST' and form.validate():
#        recipients = form.recipients.data
#        recipients = list_to_string(recipients)
#        results = es.search(index=config.INDEX, doc_type='email', body={'filter': {'query': {'match': {'To': {'query': recipients, 'operator': 'OR' }}}}})
#        total = results['hits']['total']
#        msgs = es_to_dict(results)
#        return render_template('list.html', recipients=recipients, msgs=msgs, total=total)
#    return render_template('search_form.html', form=form)
def email_search():
    return make_response(open('templates/search_form.html').read())

@app.route('/emails/adv_search')
def email_adv_search(query=None):

    query = request.args.get('search')
    
# execute advanced boolean search
    if request.args.get('search'):
        results = es.search(index=config.INDEX, doc_type='email', body={'filter': {'query': { 'query_string': { 'default_field': 'body', 'query': query }}}, 'sort': {'_score': {'order': 'desc'}}}, size=100, _source=True, analyze_wildcard=True, default_operator='AND') 
        total = results['hits']['total']
        msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total, query=query)

@app.route('/emails/mlt/<msg_id>/')
def email_mlt(msg_id=None):

# execute More Like This search of single doc to find similar docs
    results = es.mlt(index=config.INDEX, doc_type='email', id=msg_id, mlt_fields=['body'], percent_terms_to_match=0.7, min_doc_freq=1, min_term_freq=1, body={'sort': {'_score': {'order': 'desc'}}})
    total = results['hits']['total']
    msgs = es_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total)

if __name__ == '__main__':
    app.run(debug=True)
