import enum
from pymongo import MongoClient
from datetime import datetime
from typing import Dict
from .mongodb_collections import MongoCollectionWrapper, MongoDBTimeSeriesData


class CollectionType(enum.Enum):
    IR_DATA = "ir_data"
    SYSTEM_DATA = "system_data"
    MPU_DATA = "mpu_data"
    CAMERA_DATA = "camera_data"
    SESSION_DATA = "session_data"

    def __lt__(self, other):
        return self.name < other.name


class MongoDBConnection:
    """Configuration class to set the MongoDB uri, the collections to create (as Enum)
    and to request the MongoDBCollection objects to run predefined queries.
    """

    def __init__(self, mongodb_uri):
        self.client = MongoClient(mongodb_uri)
        self.database = self.client.zumi
        self.__collections = {}

        def setup_collections() -> None:
            """Creates the configured collections"""
            for data in CollectionType:
                if data.value not in self.database.list_collection_names():
                    if data.value != "session_data":
                        self.__create_time_series_collection(data.value)
                    else:
                        self.database.create_collection(name=data.value)
                if data.value != "session_data":
                    self.__collections[data] = MongoDBTimeSeriesData(
                        self.database[data.value]
                    )
                else:
                    self.__collections[data] = MongoCollectionWrapper(
                        self.database[data.value]
                    )

        setup_collections()

    def __create_time_series_collection(self, name: str) -> None:
        """Creates mongodb time series collection with unique identifiers: timestamp, session_id

        :param name: name of the time series
        :type name: str
        """
        self.database.create_collection(
            name,
            timeseries={
                "timeField": "timestamp",
                "metaField": "session_id",
                "granularity": "seconds",
            },
        )

    def get_collection_by_type(self, c_type: CollectionType) -> MongoCollectionWrapper:
        """Get the mongoDB connection tied to the specified collection type

        :param c_type: type of mongoDB collection
        :type c_type: CollectionType
        :return: the associated collection from the mongoDB database
        :rtype: MongoCollectionWrapper
        """
        return self.__collections[c_type]

    def get_all_collections(self) -> Dict[CollectionType, MongoCollectionWrapper]:
        """Returns a dict with all collections from the mongoDB database

        :return: dict with CollectionType as key and MongoCollectionWrapper as value
        :rtype: Dict[CollectionType, MongoCollectionWrapper]
        """
        return self.__collections

    def get_numeric_sensor_data_by_time(
        self, timestamp_start: datetime, timestamp_end: datetime, c_types: dict
    ) -> dict:
        """Get selected sensor data from the mongoDB between a start and end time

        :param timestamp_start: starting time, a python datetime object
        :type timestamp_start: datetime
        :param timestamp_end: end time, a python datetime object
        :type timestamp_end: datetime
        :param c_types: a dict containing the CollectionTypes to search for
        :type c_types: dict
        :return: dict containing all found sensor data
        :rtype: dict
        """
        result = {}
        for t in c_types:
            collection = self.__collections[t]
            result[t] = collection.sensor_data_by_time(
                timestamp_start, timestamp_end, c_types[t]
            )
        return result

    def close(self) -> None:
        """Closes the mongoDB connection"""
        self.client.close()
