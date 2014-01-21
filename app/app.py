from flask import render_template
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.enron
emails = db.test_kaminski

@app.route('/')
@app.route('/index/')
def index():
    return render_template('base.html')

@app.route('/emails/<message_id>/')
def email_detail(message_id):
    # get email from mongodb using query by id
    msg = emails.find_one({'Message-ID': message_id}) 
    return render_template('detail.html', msg=msg)

@app.route('/emails/')
def email_list():
    return render_template('list.html')
