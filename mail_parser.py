import os

from email.parser import Parser
from datetime import *
from pymongo import MongoClient
from utils import config


def date_parser(s):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    wkdy_s, day_s, month_s, yr_s, hms_s, os_s, tz_s = s.split(' ')

    msg_datetime = datetime(int(yr_s), months.index(month_s)+1, int(day_s))
    msg_datetime = str(msg_datetime)
    msg_date, msg_time = msg_datetime.split(' ')
    solr_dt = msg_date+'T'+msg_time+'Z'

    return solr_dt


def msg_to_dict(msg):
    metadata = {}
    chars = msg.get_param('charset', header='Content-Type')
    if chars:
        for k, v in msg.items():
            metadata[k] = v.decode(chars, errors='ignore').encode('utf-8')
        metadata['body'] = msg.get_payload(decode=1).decode(chars, errors='ignore').encode('utf-8')
    try:
        dt = date_parser(metadata['Date'])
        metadata['Date'] = dt
    except KeyError as e:
        pass
    return metadata


def init_mongo(collection_name):
    client = MongoClient()
    db = client.enron
    db.drop_collection(collection_name)
    db.create_collection(collection_name)

    return client


def write_to_mongo(db, collection_name, new_posts):

    db[collection_name].insert(new_posts)
    print "Index has {} docs".format(db[collection_name].count())
    

if __name__ == '__main__':
    mongo = init_mongo(config.ENRON_COLLECTION)

    for root, subs, files in os.walk(config.MAIL_DIR):
        mails = []
        for filename in files:
            if not filename.endswith('.csv'):
                with open(os.path.join(root, filename), 'r') as fp:
                    message = Parser().parse(fp)
                    mails.append(msg_to_dict(message))

        if mails:
            write_to_mongo(mongo.enron, config.ENRON_COLLECTION, mails)
        else:
            continue
