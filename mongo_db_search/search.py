import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import math
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
from datetime import datetime, timedelta
import numpy as np
from mongo_db.mongodb_connection import MongoDBConnection
from dtaidistance import dtw_ndim
from typing import Generator, Tuple

__connection = None
__query = None


class SearchQuery:
    def __init__(
        self,
        data_to_search: dict,
        start: datetime,
        end: datetime,
        interpolation_resolution: timedelta,
        step: int = None,
        result_size: int = 4,
    ):
        """Initializes a SearchQuery with the necessary parameters

        :param data_to_search: dict<CollectionType, list[Dict]> with 1 inner dict = 1 measurement
        :example: {CollectionType.IR_DATA: [{"timestamp": ..., "feature1": 12, "feature2": 2}, {"timestamp": ..., "feature1": 8, "feature2": 7}],
                  CollectionType.MPU_DATA: [{"timestamp": ..., "feature1": 12, "feature2": 2}]}
        :type data_to_search: dict
        :param start: starting time of interval to search in db, a python datetime object
        :type start: datetime
        :param end: end time of interval to search in db, a python datetime object
        :type end: datetime
        :param interpolation_resolution: common interpolation resolution for the different sensor data
        Lower resolution results in potentially lower accuracy, but with better performance
        :type interpolation_resolution: timedelta
        :param step: multiple of interpolation_resolution at which the dtw calculation is done
        None will result in step size equal 1/3 of data_to_search duration
        Step 1 has the highest accuracy, but at high performance costs
        :type step: int, optional
        :param result_size: specifies the number of best results to return, defaults to 4
        :type result_size: int, optional
        :raises exception: raise exception when start time >= end time
        """
        if start >= end:
            raise Exception("Start time >= end time")
        self.selected_features = {
            c_type: list(data_to_search[c_type][0].keys()) for c_type in data_to_search
        }
        self.start = start
        self.end = end
        self.interpolation_resolution = interpolation_resolution
        self.step = step
        self.result_size = result_size
        self.search_range_size = math.ceil((end - start) / interpolation_resolution)
        self.data_to_search = data_to_search


def __get_start_and_end_time(sensor_data: dict) -> Tuple[datetime, datetime]:
    """Get the start and end time from a sensor data dict

    :param sensor_data: CollectionType dict
    :type sensor_data: dict
    :return: tuple of earliest start time and latest end time
    :rtype: Tuple[datetime, datetime]
    """
    start = None
    end = None
    for c_type in sensor_data:
        for i in [0, -1]:
            timestamp = sensor_data[c_type][i]["timestamp"]
            if i == 0 and (start is None or start > timestamp):
                start = timestamp
            if i == -1 and (end is None or end < timestamp):
                end = timestamp
    return start, end


def __timeseries_to_np_array(
    sensor_data: dict, interpolation_resolution: timedelta
) -> np.array:
    """Convert a time series dict to a numpy array

    :param sensor_data: dict<CollectionType, list[Dict]>, see SearchQuery docstring
    :type sensor_data: dict
    :param interpolation_resolution: the timedelta at which interpolation takes place
    :type interpolation_resolution: timedelta
    :return: the transformed time series
    :rtype: np.array
    """

    def assign_arr_values(
        arr: np.array, arr_i: int, feature_i: int, measurement: dict
    ) -> None:
        i = feature_i
        for key in sorted(measurement):
            if key != "timestamp":
                arr[arr_i, i] = measurement[key]
                i += 1

    start, end = __get_start_and_end_time(sensor_data)
    number_of_features = 0
    collection_indices = {}
    feature_indices = {}
    for key in sensor_data:
        collection_indices[key] = 0
        feature_indices[key] = number_of_features
        number_of_features += len(sensor_data[key][0]) - 1
    arr = np.empty(
        (math.ceil((end - start) / interpolation_resolution) + 1, number_of_features),
        dtype=float,
    )
    time_index = start
    arr_i = 0
    while time_index <= end:
        for c_type in sensor_data:
            assigned = False
            collection_indices[c_type]
            while (
                sensor_data[c_type][collection_indices[c_type]]["timestamp"]
                <= time_index
            ):
                if collection_indices[c_type] + 1 < len(sensor_data[c_type]):
                    collection_indices[c_type] = collection_indices[c_type] + 1
                else:
                    assign_arr_values(
                        arr, arr_i, feature_indices[c_type], sensor_data[c_type][-1]
                    )
                    assigned = True
                    break
            if not assigned and collection_indices[c_type] == 0:
                assign_arr_values(
                    arr, arr_i, feature_indices[c_type], sensor_data[c_type][0]
                )
                assigned = True
            if not assigned:
                # Interpolation:
                i = feature_indices[c_type]
                for key in sorted(sensor_data[c_type][collection_indices[c_type]]):
                    if key != "timestamp":
                        arr[arr_i, i] = float(
                            np.interp(
                                x=time_index.timestamp(),
                                xp=[
                                    sensor_data[c_type][collection_indices[c_type] - 1][
                                        "timestamp"
                                    ].timestamp(),
                                    sensor_data[c_type][collection_indices[c_type]][
                                        "timestamp"
                                    ].timestamp(),
                                ],
                                fp=[
                                    sensor_data[c_type][collection_indices[c_type] - 1][
                                        key
                                    ],
                                    sensor_data[c_type][collection_indices[c_type]][
                                        key
                                    ],
                                ],
                            )
                        )
                        i += 1
        time_index += interpolation_resolution
        arr_i += 1
    return arr


WARNING = "\033[93m"  # TODO should be replaced with logging
ENDC = "\033[0m"

seriesToSearch = None  # only for testing will be removed
n = 0


def __cdtw(seq1: np.array, seq2: np.array) -> float:
    """Calls cdtw from the dtaidistance package

    :param seq1: first sequence for comparison
    :type seq1: np.array
    :param seq2: second sequence for comparison
    :type seq2: np.array
    :return: distance between sequences
    :rtype: float
    """
    return dtw_ndim.distance(seq1, seq2, use_c=True, use_pruning=True)


def __fastdtw(seq1: np.array, seq2: np.array) -> float:
    """Calls fastdtw from the fastdtw package

    :param seq1: first sequence for comparison
    :type seq1: np.array
    :param seq2: second sequence for comparison
    :type seq2: np.array
    :return: distance between sequences
    :rtype: float
    """
    dis, p = fastdtw(seq1, seq2, dist=euclidean)
    return dis


def __search(
    seq: np.array,
    distance_function: callable,
    percent_per_step: float,
    gen: Generator,
    duration: timedelta,
) -> dict:
    """Search for similar sequences to a numpy array with a given distance function

    :param seq: numpy array to search for
    :type seq: np.array
    :param distance_function: distance function used for calculation
    :type distance_function: callable
    :param percent_per_step: how much progress will be done in one step
    :type percent_per_step: float
    :param gen: generator for the current time index
    :type gen: Generator
    :param duration: duration of the time series requested from __get_comparison_seq
    :type duration: timedelta
    :return: dict<distance, timestamp> the distance of the time series, starting with the timestamp for the given duration
    :rtype: dict
    """
    d = {}
    percent = 0.0
    print("Progress: ")
    timesum = timedelta(seconds=0)
    for i in gen:
        start = datetime.now()
        seq2 = __get_comparison_seq(i, duration)
        if seq2 is not None:
            d[distance_function(seq, seq2)] = i
        percent += percent_per_step
        print(
            str(int(percent))
            + "%"
            + " estimated time left: "
            + str((timesum / percent) * (100 - percent)),
            end="\r",
        )
        timesum += datetime.now() - start
    print("\nDone")
    return d


def __seq_generator(start: datetime, end: datetime, step: timedelta) -> Generator:
    """Generates the times indices for time series comparisons

    :param start: starting time of interval to search in db, a python datetime object
    :type start: datetime
    :param end: end time of interval to search in db, a python datetime object
    :type end: datetime
    :param step: time interval between two comparisons
    :type step: timedelta
    :yield: current time index
    :rtype: Generator
    """
    current = start
    while current < end:
        yield current
        current += step


def __get_comparison_seq(i: datetime, duration: timedelta) -> np.array:
    """Requests the sequence for comparison

    :param i: current time index at which the sequence should begin
    :type i: datetime
    :param duration: duration of the sequence
    :type duration: timedelta
    :return: returns the sequence if data is found in all CollectionTypes, else return None
    :rtype: np.array
    """
    result = __connection.get_numeric_sensor_data_by_time(
        i, i + duration, __query.selected_features
    )
    for c_type in __query.selected_features:
        if len(result[c_type]) == 0:
            return None
    return __timeseries_to_np_array(result, __query.interpolation_resolution)


def search(query: SearchQuery, connection: MongoDBConnection) -> dict:
    """Search the mongoDB for time series matching the query

    :param query: SearchQuery specifies the search parameters
    :type query: SearchQuery
    :param connection: connection to the mongoDB
    :type connection: MongoDBConnection
    :return: dict<distance, timestamp at which the compared time series begins>, dict of search results sorted by distance
    :rtype: dict
    """
    global __query
    global __connection
    __query = query
    __connection = connection
    seq = __timeseries_to_np_array(query.data_to_search, query.interpolation_resolution)
    step = int(len(seq) / 3) if query.step is None else query.step
    print(
        "This query will run "
        + str(int((query.end - query.start) / (query.interpolation_resolution * step)))
        + " dtw calculations, each with "
        + str(len(seq))
        + " data points"
    )
    p = (step / (query.search_range_size - len(seq))) * 100
    duration = len(seq) * query.interpolation_resolution
    gen = __seq_generator(
        query.start, query.end - duration, query.interpolation_resolution * step
    )
    if dtw_ndim.dtw_cc is None:
        print(
            WARNING
            + "C library for dtw not found, please install (with conda) for better results: "
            "https://dtaidistance.readthedocs.io/en/latest/usage/installation.html"
        )
        print("Using fastdtw approximation instead..." + ENDC)
        d = __search(seq, __fastdtw, p, gen, duration)
    else:
        d = __search(seq, __cdtw, p, gen, duration)
    i = 0
    result = {}
    for k in sorted(d):
        result[k] = d[k]
        if i >= query.result_size:
            break
        i += 1
    return result
