from __future__ import print_function
from email.charset import *
from email.header import decode_header
from email.parser import Parser
from email.message import *
from email.encoders import *
from datetime import datetime
import sys, os, json, collections#, pysolr
from types import *
from pymongo import MongoClient
import config


reload(sys)
sys.setdefaultencoding('utf-8')


def date_parser(s):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    wkdy_s, day_s, month_s, yr_s, hms_s, os_s, tz_s = s.split(' ')
    msg_datetime = datetime(int(yr_s), months.index(month_s)+1, int(day_s))
    msg_datetime = str(msg_datetime)
    msg_date, msg_time = msg_datetime.split(' ')
    solr_dt = msg_date+'T'+msg_time+'Z'
    return solr_dt


def msgParser(sourcefile):
    msg = Parser().parse(open(sourcefile,'r'))
    metadata = {}
    for part in msg.walk():
	metadata = dict(part.items())
    metadata = dict((k.lower(), v) for k,v in metadata.iteritems())
    try:
	metadata['message_id'] = metadata.pop('message-id')
    except KeyError:
	pass
    
    try:
        if (msg.get_content_charset() == 'us-ascii') or (msg.get_content_charset() == 'ascii'):
            metadata['body'] = msg.get_payload(decode=1).decode('us-ascii', errors='ignore').encode('utf-8')
        elif msg.get_content_charset() == 'latin-1':
            metadata['body'] = msg.get_payload(decode=1).decode('latin-1', errors='ignore').encode('utf-8')
        elif msg.get_content_charset() == 'ISO-8859-1':
            metadata['body'] = msg.get_payload(decode=1).decode('ISO-8859-1', errors='ignore').encode('utf-8')           
        elif msg.get_content_charset() == 'Windows-1252':
            metadata['body'] = msg.get_payload(decode=1).decode('cp1252', errors='ignore').encode('utf-8')
	elif msg.get_content_charset() == 'ANSI_X3.4-1968':
            metadata['body'] = msg.get_payload(decode=1).decode('ANSI_X3.4-1968', errors='ignore').encode('utf-8')
        elif msg.get_content_charset() == None:
            metadata['body'] = msg.get_payload(decode=1).decode('latin-1', errors='ignore').encode('utf-8')
	elif msg.get_content_charset() == '':
	    metadata['body'] = msg.get_payload(decode=1).decode('latin-1', errors='ignore').encode('utf-8')   
        else:  
            chars = msg.get_param('charset',header='Content-Type')
            metadata['body'] = msg.get_payload(decode=1).decode(chars, errors='ignore')
    except UnicodeDecodeError:
        metadata['body'] = 'decoding error'
    try:
	metadata['date'] = date_parser(str(metadata['date']))
    except KeyError:
	pass
    
    return metadata
    

def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data
    

def mongowriter(new_posts):
    client = MongoClient()
    db = client.test_database_blair
    db.posts.drop()
    posts = db.posts
    posts.insert(new_posts)


def main():

    mails = []
    
    for root, subFolders, files in os.walk(config.ROOTDIR):
        for filename in files:
            if filename.endswith('.csv') == False:
                filePath = os.path.join(root, filename)
                m = msgParser(filePath)
		m = convert(m)
		mails.append(m)

    #solr.add([m])

    
    with open(config.MAILBOX, 'w') as f:
	try:
	    json.dump(mails, f, ensure_ascii=False)
	except UnicodeDecodeError:
	    pass
	f.close()


    #with open(myFile, 'a') as f:
    #r = msgParser(filePath)     
    #r = convert_keys_to_string(r)
    #f.write(str(r).encode('utf-8'))
    #mailbox.close()
    
    
    with open(config.MAILBOX, 'r') as f:
	try:
	    mail_posts = json.load(f)
	except UnicodeDecodeError:
	    pass
	f.close()


    mongowriter(mail_posts)
    
    #maildata = []
    #with open(mailbox) as mbox:
    #    for line in mbox:
    #        maildata.append(json.load(line))
    #mailbox.close()
    #maildata = unicode(maildata, errors='ignore').encode('utf-8')
    #print(maildata)


if __name__ == "__main__":
    main()
    