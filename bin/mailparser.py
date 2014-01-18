from email.parser import Parser
from email.message import Message
from datetime import *
import os
from pymongo import MongoClient

mailpath = open('/Users/bencassedy/projects/enron/enron_mail_20110402/maildir/kaminski-v/sent_items/2524.', 'r')

maildir = '/Users/bencassedy/projects/enron/enron_mail_20110402/maildir/kaminski-v'

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
    chars = msg.get_param('charset',header='Content-Type')
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
    
def mongowriter(new_posts):
    client = MongoClient()
    db = client.enron
    collection = db.test_kaminski
    collection.insert(new_posts)
    
mails = []
        
for root, subFolders, files in os.walk(maildir):
    for filename in files:
        if filename.endswith('.csv') == False:
            filePath = os.path.join(root, filename)
            fp = open(filePath, 'r')
            p = Parser().parse(fp)
            m = msg_to_dict(p)
	mails.append(m)

mongowriter(mails)

