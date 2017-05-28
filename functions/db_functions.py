from pymongo import MongoClient
import os


def mongo_connect_get_app_data_disconnect(mongo_connection_string, app_name, schema_name="nebula", ):
    try:
        client = MongoClient(mongo_connection_string)
        db = client[schema_name]
        collection = db["nebula"]
    except:
        print "error connecting to mongodb"
        os._exit(2)
    try:
        result = collection.find_one({"app_name": app_name})
        client.close()
    except:
        print "error getting app data from mongodb"
        os._exit(2)
    return result