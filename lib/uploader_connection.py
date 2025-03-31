import os
import pymongo
from dotenv import load_dotenv


class UploaderConnection:
    def __init__(self):
        load_dotenv(".env")
        self.host = os.environ.get("uploader_host")
        self.port = os.environ.get("uploader_port")
        self.database = os.environ.get("uploader_database")
        self.mongo_session = None

    def get_mongo_connection(self):
        mongo_client = pymongo.MongoClient(
            f"mongodb://{self.host}:{self.port}/", serverSelectionTimeoutMS=1200000
        )
        database = mongo_client[self.database]
        self.mongo_session = database

    def get_record_by_file_name(self, file_name: str):
        result = self.mongo_session.packages.find_one({"files": {"$elemMatch": {"$and": [{"fileName": file_name}]}}}, {"_id": 0, "study": 1, "packageType": 1})
        return result

