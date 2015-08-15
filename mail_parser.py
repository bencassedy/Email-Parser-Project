import os

from email.parser import Parser
from datetime import *
from utils import config
from utils.mongo_utils import init_mongo, write_to_mongo


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


if __name__ == '__main__':
    mongo = init_mongo(config.MONGO_ENRON_COLLECTION)

    for root, subs, files in os.walk(config.MAIL_DIR):
        mails = []
        for filename in files:
            if not filename.endswith('.csv'):
                with open(os.path.join(root, filename), 'r') as fp:
                    message = Parser().parse(fp)
                    mails.append(msg_to_dict(message))

        if mails:
            write_to_mongo(mongo.enron, config.MONGO_ENRON_COLLECTION, mails)
        else:
            continue
