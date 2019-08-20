from flask import Flask, session, render_template, request, redirect, g, url_for
from pymongo import MongoClient

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
    "SuperAdmin": ['logout', 'superadminlogin', 'createapp', 'appdetails', 'applist','typeslist','createtype'],
}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('user', None)
        db = client['users']
        collection = db['users']
        existing_user = collection.find_one({'name': request.form['username']})
        if existing_user is not None and request.form['password'] == existing_user['password']:
            session['user'] = request.form['username']
            if existing_user['AccountType'] == 'Admin':
                session['myaccount'] = 'Admin'
                return redirect(url_for('protected'))
            elif existing_user['AccountType'] == 'Mfg':
                session['myaccount'] = 'Mfg'
                return redirect(url_for('protected'))
            elif existing_user['AccountType'] == 'Dealer':
                session['myaccount'] = 'Dealer'
                return redirect(url_for('protected'))
            elif existing_user['AccountType'] == 'SuperAdmin':
                session['myaccount'] = 'SuperAdmin'
                return redirect(url_for('superadminlogin'))
        else:
            return "Invalid Password/Email"
    elif request.method == 'GET':
        # if 'user' not in session:
        #     session.pop('myaccount',None)
        if 'myaccount' in session:
            if session['myaccount'] is not None:
                if session['myaccount'] == 'Admin':
                    return redirect(url_for('protected'))
                elif session['myaccount'] == 'Mfg':
                    return redirect(url_for('protected'))
                elif session['myaccount'] == 'Dealer':
                    return redirect(url_for('protected'))
                elif session['myaccount'] == 'SuperAdmin':
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
                userkeypair = {'private_key': "PRIVATE_KEY", 'public_key': "PUBLIC_KEY"}
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
                fulfilled_creation_tx = {'id': 00000000}

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
    if session['myaccount'] is not None and 'protected' in allowed_pages[session['myaccount']]:
        if g.user:
            return render_template('protected.html')
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))


@app.route('/superadminlogin')
def superadminlogin():
    if session['myaccount'] is not None and 'superadminlogin' in allowed_pages[session['myaccount']]:
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
                'ns': request.form['ns'],
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
                return redirect(url_for('applist'))
            else:
                return redirect(url_for('applist'))
                pass
        else:
            pass
        # if user not found

    elif request.method == 'GET':
        return render_template('createapp.html')

    else:
        pass


@app.route('/appdetails/<appid>', methods=['GET'])
def appdetails(appid):
    if session['myaccount'] is not None and 'appdetails' in allowed_pages[session['myaccount']]:
        if g.user:
            return render_template('appdetails.html', params=appid)
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))


@app.route('/applist', methods=['GET'])
def applist():
    if session['myaccount'] is not None and 'applist' in allowed_pages[session['myaccount']]:
        if g.user:
            # get app list from blockchain and display in list page
            db = client['bigchain']
            collection = db['assets']
            applist = collection.find({"data.ns": "ipdb.apps"})
            print(applist)
            # params = [{
            #     "_id": "5d50087feeaec47dbb9ee008",
            #     "data": {
            #         "ns": "ipdb.apps",
            #         "name": "SCM1"
            #     },
            #     "id": "5f75c5f0a85d9b5d692ee57132f292b3826f3b11425545ff027120ecea415547"
            # },
            #     {
            #         "_id": "5d50087feeaec47dbb9ee008",
            #         "data": {
            #             "ns": "ipdb.apps",
            #             "name": "SCM2"
            #         },
            #         "id": "5hfgnfgnfnff027120ecea415547"
            #     }
            # ]
            return render_template('applist.html', params=applist)
        else:
            return 'Not Valid Token To Access This Page.'
    else:
        return redirect(url_for('index'))

@app.route('/appdetails/<appid>/createtype', methods=['GET','POST'])
def createtype(appid):
    if session['myaccount'] is not None and 'createtype' in allowed_pages[session['myaccount']]:
        #if g.user:
            if request.method == 'POST':
                TypeAsset = {'data': {
                'ns': 'ipdb.apptype.'+request.form['ns'],
                'name': request.form['typename'],
                'link': appid
                },
            }

        #AppMetadata = {'can_link': request.form['canlink']}
                db = client['users']
                collection = db['users']
                existing_user = collection.find_one({'name': getsession()})
                if existing_user:
                    if enableBigChain:
                        prepared_creation_tx_AppType = bdb.transactions.prepare(
                    operation='CREATE',
                    signers=existing_user['pub_key'],
                    asset=TypeAsset,
                    #metadata=AppMetadata,
                    )
                        fulfilled_creation_tx_AppType = bdb.transactions.fulfill(prepared_creation_tx_AppType,
                                                                     private_keys=existing_user['priv_key'])
                        sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx_AppType)
                        AppAsset_id = fulfilled_creation_tx_AppType['id']
                        print("APP Creation Successfull..")
                        print(AppAsset_id)
                        return redirect(url_for('createtype'))
                    else:
                        return redirect(url_for('createtype'))
                        pass
                else:
                    pass
        # if user not found

        #elif request.method == 'GET':
        #    return render_template('createtype.html',params=appid)

    else:
        pass



@app.route('/appdetails/<appid>/typeslist', methods=['GET'])
def typeslist(appid):
    if session['myaccount'] is not None and 'typelist' in allowed_pages[session['myaccount']]:
        if g.user:
            return render_template('typeslist.html',params=appid)

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


# @app.before_first_request
# def before_first_request():
#     global myaccount
#     myaccount = None


@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']

    return 'Not logged in!'


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('myaccount', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
