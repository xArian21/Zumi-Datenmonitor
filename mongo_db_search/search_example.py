import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from datetime import timedelta, datetime
from search import search, SearchQuery
from mongo_db.mongodb_connection import CollectionType, MongoDBConnection


connection = MongoDBConnection(
    "mongodb://zumi:S55pbxIrkw7M2_1Sxac-w5ZmQrU3fKXk@51.158.177.62:27017/"
)

search_ts = connection.get_numeric_sensor_data_by_time(
    datetime(2021, 11, 27, 19, 35),
    datetime(2021, 11, 27, 19, 36),
    {
        CollectionType.IR_DATA: ["ir_front_left", "ir_front_right", "timestamp"],
        CollectionType.MPU_DATA: [
            "gyro_x_angle",
            "gyro_y_angle",
            "gyro_z_angle",
            "timestamp",
        ],
    },
)

result = search(
    SearchQuery(
        search_ts,
        datetime(2021, 11, 27, 19, 27),
        datetime(2021, 11, 27, 20, 5),
        timedelta(seconds=1),
        2,
        10,
    ),
    connection,
)

for k in result:
    print("distance: " + str(k) + " at time: " + str(result[k]))
