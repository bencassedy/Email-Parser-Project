from pymongo import MongoClient

mongo_client = MongoClient()


def init_mongo(collection_name):
    db = mongo_client.enron
    db.drop_collection(collection_name)
    db.create_collection(collection_name)

    return mongo_client


def write_to_mongo(db, collection_name, new_posts):

    db[collection_name].insert_many(new_posts, ordered=False)
    print "Index has {} docs".format(db[collection_name].count())
