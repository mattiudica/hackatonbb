import pymongo
from pymongo import MongoClient

MONGO_URI = 'mongodb://localhost'

client = MongoClient(MONGO_URI)

db = client['hackaton']
collection = db['platforms']

def insert(data, collection=collection):
    query = collection.insert_one(data)
    if query:
        print(f'Inserte one ok')
        return True
    else:
        print(f'Isenrt one error')
        return False

def insertMany(data, collection=collection ):
    query =  collection.insert_many(data)
    if query:
        print(f'Inserte many ok')
        return True
    else:
        print(f'Isenrt many error')
        return None
    
    