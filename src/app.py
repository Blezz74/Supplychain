from flask import Flask, session, render_template, request, redirect, g, url_for
from pymongo import MongoClient

myaccount = None
enableBigChain = True

if enableBigChain:
    from bigchaindb_driver import BigchainDB
    from bigchaindb_driver.crypto import generate_keypair
    bdb_root_url = 'http://localhost:9985'
    bdb = BigchainDB(bdb_root_url)

app = Flask(__name__)
app.secret_key = "fbrehsb5786788756gufe785785rvgtejh785785785875785gte78e87657865gyu5456456464r4g4gr4g65"

client = MongoClient('localhost', 27017)

# ['register','protected','usercreated','logout','superadminlogin']

allowed_pages = {
    "Admin": ['protected', 'usercreated', 'logout'],
    "Mfg": ['protected', 'usercreated', 'logout'],
    "Dealer": ['protected', 'usercreated', 'logout'],
    "SuperAdmin": ['logout', 'superadminlogin','createapp','appdetails','displayAllApps'],
}


@app.route('/', methods=['GET', 'POST'])
def index():
    global myaccount
    if request.method == 'POST':
        session.pop('user', None)
        db = client['users']
        collection = db['users']
        existing_user = collection.find_one({'name': request.form['username']})
        if existing_user is not None and request.form['password'] == existing_user['password']:
            session['user'] = request.form['username']
            if existing_user['AccountType'] == 'Admin':
                myaccount = 'Admin'
                return redirect(url_for('protected'))
            elif existing_user['AccountType'] == 'Mfg':
                myaccount = 'Mfg'
                return redirect(url_for('protected'))
            elif existing_user['AccountType'] == 'Dealer':
                myaccount = 'Dealer'
                return redirect(url_for('protected'))
            elif existing_user['AccountType'] == 'SuperAdmin':
                myaccount = 'SuperAdmin'
                return redirect(url_for('superadminlogin'))
        else:
            return "Invalid Password/Email"
    elif request.method == 'GET' and myaccount is not None:
        if myaccount == 'Admin':
            return redirect(url_for('protected'))
        elif myaccount == 'Mfg':
            return redirect(url_for('protected'))
        elif myaccount == 'Dealer':
            return redirect(url_for('protected'))
        elif myaccount == 'SuperAdmin':
            return redirect(url_for('superadminlogin'))

    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = client['users']
        collection = db['users']
        AcType = request.form['AccountType']
        existing_user = collection.find_one({'name': request.form['username']})
        if existing_user is None:
            if enableBigChain:
                userkeypair = generate_keypair()
                tx_pvt_key = userkeypair.private_key
                tx_pub_key = userkeypair.public_key
            else:
                userkeypair = {'private_key': "PRIVATE_KEY",'public_key': "PUBLIC_KEY"}
                tx_pvt_key = userkeypair['private_key']
                tx_pub_key = userkeypair['public_key']
            if AcType == 'Admin':
                UserData = {'data': {
                    'ns': 'ipdb.scm.admin',
                    'link': 'Will change when created Admin Type',
                    'name': request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}  # will change when admin type is created
            elif AcType == 'SuperAdmin':
                UserData = {'data': {
                    'ns': 'ipdb.scm.SuperAdmin',
                    'link': 'Will change when created SuperAdmin Type',
                    'name': request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}  # will change when admin type is created
            elif AcType == 'Mfg':
                UserData = {'data': {
                    'ns': 'ipdb.scm.mfg',
                    'link': 'Will change when created Mfg Type',
                    'name': request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}  # will change when admin type is created
            elif AcType == 'Dealer':
                UserData = {'data': {
                    'ns': 'ipdb.scm.dealer',
                    'link': 'Will change when created Mfg Type',
                    'name': request.form['username']
                },
                }
                UserMetadata = {'email': request.form['email']}  # will change when admin type is created
            if enableBigChain:
                prepared_creation_tx = bdb.transactions.prepare(
                    operation='CREATE',
                    signers=userkeypair.public_key,
                    asset=UserData,
                    metadata=UserMetadata,
                )
                fulfilled_creation_tx = bdb.transactions.fulfill(prepared_creation_tx,
                                                                 private_keys=userkeypair.private_key)
                sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
            else:
                fulfilled_creation_tx = {'id' :  00000000}

            login_user = collection.insert_one(
                {'name': request.form['username'], 'password': str(request.form['password']),
                 'trx_id': fulfilled_creation_tx['id'], 'pub_key': tx_pub_key,
                 'priv_key': tx_pvt_key, 'AccountType': AcType})
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
    global myaccount
    if myaccount is not None and 'protected' in allowed_pages[myaccount]:
        if g.user:
            return render_template('protected.html')
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))


@app.route('/superadminlogin')
def superadminlogin():
    global myaccount
    if myaccount is not None and 'superadminlogin' in allowed_pages[myaccount]:
        if g.user:
            return render_template('superadmin.html', user=g.user)
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))


@app.route('/createapp', methods=['GET', 'POST'])
def create_app():
    if request.method == 'POST':
        AppAsset = {
            'data': {
                'ns': 'ipdb.apps',
                'name': request.form['appname'],
            },
        }

        AppMetadata = {'can_link': request.form['canlink']}
        db = client['users']
        collection = db['users']
        existing_user = collection.find_one({'name': getsession()})
        if existing_user:
            if enableBigChain:
                prepared_creation_tx_App = bdb.transactions.prepare(
                    operation='CREATE',
                    signers=existing_user['pub_key'],
                    asset=AppAsset,
                    metadata=AppMetadata,
                )
                fulfilled_creation_tx_App = bdb.transactions.fulfill(prepared_creation_tx_App,
                                                                     private_keys=existing_user['priv_key'])
                sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx_App)
                AppAsset_id = fulfilled_creation_tx_App['id']
                print("APP Creation Successfull..")
                print(AppAsset_id)
                return redirect(url_for('displayAllApps'))
            else:
                return redirect(url_for('displayAllApps'))
                pass
        else:
            pass
        # if user not found

    elif request.method == 'GET':
        return render_template('createapp.html')

    else:
        pass

@app.route('/displayAllApps', methods=['GET', 'POST'])
def displayAllApps():
    db = client['bigchain']
    collection = db['assets']

    global myaccount
    if myaccount is not None and 'superadminlogin' in allowed_pages[myaccount]:
        if g.user:
            apps=collection.find({'data.ns':'ipdb.apps'})
            appname=[]
            for app in apps:
                appname.append(app['data']['name'])
            return render_template('AllApps.html', user=g.user, apps=appname)
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))




@app.route('/appdetails', methods=['GET'])
def appdetails():
    global myaccount
    if myaccount is not None and 'appdetails' in allowed_pages[myaccount]:
        if g.user:
            return render_template('appdetails.html')
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.before_first_request
def before_first_request():
    global myaccount
    myaccount = None


@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']

    return 'Not logged in!'


@app.route('/logout')
def logout():
    global myaccount
    session.pop('user', None)
    myaccount = None
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
