from pymongo import MongoClient
client = MongoClient('localhost', 27017)


def use_database(name):
    return client[name]


def get_collection_from_db(name,db):
    return db[name]


def find_one_in_collection(key,value,collection):
    return collection.find_one({key : value})
