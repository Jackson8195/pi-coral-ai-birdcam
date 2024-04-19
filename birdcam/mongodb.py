import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Get the password from the environment variable
mongodb_password = os.environ["MONGODB_PASSWORD"]

# Construct the URI with the password
uri = "mongodb+srv://jackson8:{}@birdcam.tpshz91.mongodb.net/?retryWrites=true&w=majority&appName=BirdCam".format(mongodb_password)
print("Connection string: ", uri)

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
def mongoDB_connect():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

mongoDB_connect()

db = client["Birds"]
collection = db["BirdVisitors"]

def mongo_insert(visitor, score, date):
    new_record = {"Bird:": visitor, "Score": score, "Date": date}
    collection.insert_one(new_record)