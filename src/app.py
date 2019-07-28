from flask import Flask, session, render_template, request, redirect, g, url_for
import os
from pymongo import MongoClient
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

bdb_root_url = 'http://localhost:9985'
bdb = BigchainDB(bdb_root_url)

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = MongoClient('localhost', 27017)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('user', None)
        db = client['users']
        collection = db['users']
        existing_user = collection.find_one({'name': request.form['username']})
        if request.form['password'] == existing_user['password']:
            session['user'] = request.form['username']
            return redirect(url_for('protected'))
        else:
            return "Invalid Password/Email"

    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = client['users']
        collection = db['users']
        AcType=request.form['AccountType']
        existing_user = collection.find_one({'name': request.form['username']})
        if existing_user is None:
            userkeypair = generate_keypair()
            if AcType == 'Admin':
                UserData= {'data':{
                'ns':'ipdb.scm.admin',
                'link':'Will change when created Admin Type',
                'name':request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}#will change when admin type is created
            elif AcType == 'Mfg':
                UserData= {'data':{
                'ns':'ipdb.scm.mfg',
                'link':'Will change when created Mfg Type',
                'name':request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}#will change when admin type is created
            elif AcType == 'Dealer':
                UserData= {'data':{
                'ns':'ipdb.scm.dealer',
                'link':'Will change when created Mfg Type',
                'name':request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}#will change when admin type is created
            prepared_creation_tx = bdb.transactions.prepare(
                operation='CREATE',
                signers=userkeypair.public_key,
                asset=UserData,
                metadata=UserMetadata,
                )
            fulfilled_creation_tx = bdb.transactions.fulfill(prepared_creation_tx,
private_keys=userkeypair.private_key)
            sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
            login_user = collection.insert_one({'name': request.form['username'], 'password': str(request.form['password']),'trx_id':fulfilled_creation_tx['id'],'pub_key':userkeypair.public_key,'priv_key':userkeypair.private_key, 'AccountType':AcType}) 
            if login_user.acknowledged:
                return redirect(url_for('index'))
        else:
            return 'User Exists'

    return render_template('registeration.html')


@app.route('/usercreated')
def usercreated():
    return render_template('usercreated.html')


@app.route('/protected')
def protected():
    if g.user:
        return render_template('protected.html')

    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']

    return 'Not logged in!'


@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return 'Dropped!'


if __name__ == '__main__':
    app.run(debug=True)

