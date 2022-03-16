from .mongodb_connection import CollectionType, MongoDBConnection
import os
import glob
from bson.json_util import loads
import json


def transfer_all_json_files(
    connection: MongoDBConnection, ctype: CollectionType, target_folder: str
) -> None:
    """transfers all JSON files from a specified folder to mongoDB

    :param connection: the mongoDB connection class
    :type connection: MongoDBConnection
    :param ctype: filters the log files for this specific connection type
    :type ctype: CollectionType
    :param target_folder: path to the folder containing the log files
    :type target_folder: str
    """
    files = glob.glob(os.path.join(target_folder, "{}*.json".format(ctype.value)))
    collection = connection.get_collection_by_type(ctype)
    successful = 0
    for file_name in files:
        with open(file_name, "r") as f:
            try:
                data = loads(f.read())
            except json.decoder.JSONDecodeError as e:
                print(str(e))
                print("Failed to save: " + file_name)
                continue
        for d in data:
            if "timestamp" not in d:
                if collection.write_one(d):
                    successful += 1
                else:
                    print("Failed to save: " + file_name)
            else:
                if not collection.data_by_timestamp(d["timestamp"]):
                    if collection.write_one(d):
                        successful += 1
                    else:
                        print("Failed to save: " + file_name)
    print(str(successful) + "measurements of " + str(len(files)) + " files saved")
