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
    return app.send_static_file('index.html')

@app.route('/email/<message_id>/')
def email_detail(message_id):
    # get email from mongodb using query by id
    msg = emails.find_one({'Message-ID': message_id}) 
    return render_template('detail.html', msg=msg)

@app.route('/emails')
def email_list(query=None):
    query = request.args.get('search')
    # if no search, return all results, limit to 200 for debugging purposes
    flds = config.LIST_VIEW_FIELDS
    if query == None:
        msgs = emails.find(fields=flds, limit=200)
        total = msgs.count()
    else:
        results = es.search({'query': {'match': {'_all': query}}, 'sort': {'_score': {'order': 'desc'}}}, index='test_kaminski')
        total = results['hits']['total']
        msgs = es_to_dict(results)
    return render_template('list.html', msgs=msgs, flds=flds, total=total)

@app.route('/search')
def email_search():
    pass
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)
