from datetime import datetime
from pymongo.collection import Collection
from pymongo import ASCENDING


class MongoCollectionWrapper:
    """The super class for all MongoDB collections"""

    def __init__(self, collection: Collection):
        self.collection = collection

    def write_one(self, data: dict) -> bool:
        """Write one object to the zumi database

        :param data: a dict with zumi data
        :type data: dict
        :return: true if transmission was successful, else false
        :rtype: bool
        """
        return self.collection.insert_one(data).inserted_id is not None

    def write_many(self, data: list) -> bool:
        """Write many objects to the zumi database

        :param data: a list of zumi data dicts
        :type data: list
        :return: true if transmission was successful, else false
        :rtype: bool
        """
        return len(self.collection.insert_many(data).inserted_ids) == len(data)


class MongoDBTimeSeriesData(MongoCollectionWrapper):
    """The super class for all MongoDB time series collections"""

    def __init__(self, collection: Collection):
        super().__init__(collection)

    def data_by_timestamp(self, timestamp: datetime) -> dict:
        """Get all sensor data from the time series for a specific timestamp

        :param timestamp: python datetime object
        :type timestamp: datetime
        :return: dict with sensor data
        :rtype: dict
        """
        return self.collection.find_one(
            {
                "timestamp": timestamp,
            }
        )

    def count_by_timestamp(self, timestamp: datetime) -> int:
        """Get the amount of documents stored in a time series for a specific timestamp

        :param timestamp: python datetime object
        :type timestamp: datetime
        :return: amount of documents found
        :rtype: int
        """
        return self.collection.count_documents(
            {
                "timestamp": timestamp,
            }
        )

    def sensor_data_by_time(
        self, timestamp_start: datetime, timestamp_end: datetime, features: list
    ) -> list:
        """Get sensor data from the mongoDB collection between a start and end time, filtered for selected features

        :param timestamp_start: starting time, a python datetime object
        :type timestamp_start: datetime
        :param timestamp_end: end time, a python datetime object
        :type timestamp_end: datetime
        :param features: list of the features to filter
        :type features: list
        :return: list of all matching data
        :rtype: list
        """
        results = []
        cursor = self.collection.find(
            {"timestamp": {"$gte": timestamp_start, "$lte": timestamp_end}},
            {key: True for key in features} | {"_id": False},
        ).sort("timestamp", ASCENDING)
        for sd in cursor:
            results.append(sd)
        return results


class MongoDBSensorData(MongoDBTimeSeriesData):
    """Contains all functions for MongoDB sensor data collections"""

    def __init__(self, collection: Collection):
        super().__init__(collection)

    def sensor_data_by_event(self, sensor: str, ineqs: str, value: float) -> list:
        """Get all sensor data based on the value of a specific sensor

        :param sensor: sensor name
        :type sensor: str
        :param ineqs: greater or smaller than value
        :type ineqs: Literal["<", ">"]
        :param value: value to compare against
        :type value: float
        :return: list of sensor data dictionaries
        :rtype: list
        """
        results = []
        if ineqs == "<":
            cursor = self.collection.find({sensor: {"$lt": value}})
        elif ineqs == ">":
            cursor = self.collection.find({sensor: {"$gt": value}})
        for sd in cursor:
            results.append(sd)
        return results
