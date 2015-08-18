from elasticsearch import helpers
from utils.config import MONGO_ENRON_DB, MONGO_ENRON_COLLECTION, ES_INDEX
from utils.elasticsearch_utils import es, prepare_es_index
from utils.mongo_utils import mongo_client


def build_es_action_list():
    """ convert email records stored in mongodb to elasticsearch-formatted actions,
    which contain the type of action along with the record itself

    :return: list of es-formatted insert actions
    """
    db = mongo_client[MONGO_ENRON_DB]
    emails = db[MONGO_ENRON_COLLECTION]

    email_list = []

    for email in emails.find():
        email['_id'] = str(email['_id'])  # map mongo_id to es_id

        action = {
            "_index": ES_INDEX,
            "_type": 'email',
            "_id": email['_id'],
            "_source": email
        }
        email_list.append(action)

    return email_list


if __name__ == '__main__':
    prepare_es_index(ES_INDEX)

    es_actions_list = build_es_action_list()
    helpers.bulk(es, es_actions_list)

    # this took about 10 minutes on my mac
    print "Mongo to Elasticsearch bridge operation complete"
