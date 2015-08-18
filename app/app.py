from flask import Flask, make_response, redirect, render_template, url_for, request, jsonify

from bson.json_util import dumps, loads
from bson.objectid import ObjectId
import json
from utils.config import MONGO_ENRON_DB, MONGO_ENRON_COLLECTION, LIST_VIEW_FIELDS, ES_INDEX
from utils.elasticsearch_utils import es, es_results_to_dict
from utils.mongo_utils import mongo_client

app = Flask(__name__, static_url_path='')
app.config.from_object('utils.config')

db = mongo_client[MONGO_ENRON_DB]
emails = db[MONGO_ENRON_COLLECTION]
email_tags = db['test_tags']


def list_to_string(lst):
    """ helper function to stringify lists for es queries

    :param lst: list of queries
    :return: string representation of query list param
    """
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

    display_fields = LIST_VIEW_FIELDS
    query = request.args.get('search')

    # if no search, return all results, limit to 200 for debugging purposes
    if query is None:
        msgs = emails.find(projection=display_fields, limit=200)
        total = msgs.count()

    # execute fuzzy keyword search
    elif request.args.get('search'):
        results = es.search(index=ES_INDEX,
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
        msgs = es_results_to_dict(results)

    return render_template('list.html', msgs=msgs, flds=display_fields, total=total, query=query)

# redirect to static page for angularJS functionality
@app.route('/email_search', methods=['GET', 'POST'])
def email_search():
    return make_response(open('static/search_form.html').read())


# execute advanced boolean search
@app.route('/emails/adv_search')
def email_adv_search(query=None):

    query = request.args.get('search')
    
    if request.args.get('search'):
        results = es.search(index=ES_INDEX,
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
        msgs = es_results_to_dict(results)

    return render_template('list.html', msgs=msgs, total=total, query=query)

@app.route('/emails/mlt/<msg_id>/')
def email_mlt(msg_id=None):

    # execute More Like This search of single doc to find similar docs
    results = es.mlt(index=ES_INDEX,
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
    msgs = es_results_to_dict(results)

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
