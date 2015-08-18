from elasticsearch import Elasticsearch
from utils import config

es = Elasticsearch()


def prepare_es_index(index_name):
    if es.indices.exists(index=index_name) is False:
        es.indices.create(index=index_name)
    
    # close index to perform the next few operations
    es.indices.close(index=index_name)
    
    # register tokenizer for text search
    es.indices.put_settings(index=index_name, body=config.SETTINGS_BODY)
    
    # store email body field for MLT and advanced analysis
    es.indices.put_mapping(index=index_name, doc_type='email', body=config.MAPPING_BODY)
    
    es.indices.open(index=index_name)


def es_results_to_dict(results):
    """ helper method to convert es search results to python array of dicts

    :param results: the elasticsearch result set object
    :return: python list of dict results
    """
    result_set = []
    if results['hits'] and results['hits']['hits']:
        hits = results['hits']['hits']
        for hit in hits:
            result_set.append(hit['_source'])
    return result_set
