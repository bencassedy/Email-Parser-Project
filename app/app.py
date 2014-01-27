from flask import Flask, redirect, render_template, url_for
from pymongo import MongoClient
import config

app = Flask(__name__, static_url_path='')

client = MongoClient()
db = client.enron
emails = db.test_kaminski

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
def email_list():
    flds = config.LIST_VIEW_FIELDS
    msgs = emails.find(fields=flds, limit=200)
    return render_template('list.html', msgs=msgs, flds=flds)

if __name__ == '__main__':
    app.run(debug=True)
