from flask import Flask, redirect, render_template, url_for, request
from pyelasticsearch import ElasticSearch
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
    email_list.append(email)

es = ElasticSearch('http://localhost:9200/')
es.bulk_index(index='test_kaminski', doc_type='email', docs=email_list, id_field='_id')

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
    return render_template('detail.html', msg=msg)

@app.route('/emails')
@app.route('/emails/')
def email_list(query=None):
    # if no search, return all results, limit to 200 for debugging purposes
    flds = config.LIST_VIEW_FIELDS
    query = request.args.get('search')
    adv_query = request.args.get('adv_search')
    if query is None:
        msgs = emails.find(fields=flds, limit=200)
        total = msgs.count()
    else:
        results = es.search({'query': {'fuzzy_like_this': {'fields': ['Subject', 'body'], 'like_text': query, 'max_query_terms': 12, 'prefix_length': 3}}, 'sort': {'_score': {'order': 'desc'}}}, index='test_kaminski')
        total = results['hits']['total']
        msgs = es_to_dict(results)

    # idea here is to add GET parameter so it looks like /emails?search_type=advanced_search&search=query but it's not working
    #elif request.args['search_type'] is 'adv_search':
    #    results = es.search({'query': {'query_string': {'default_field': 'body', 'query': query}}, 'sort': {'_score': {'order': 'desc'}}}, index='test_kaminski')
    #    total = results['hits']['total']
    #    msgs = es_to_dict(results)
    return render_template('list.html', msgs=msgs, flds=flds, total=total, query=query)

if __name__ == '__main__':
    app.run(debug=True)
