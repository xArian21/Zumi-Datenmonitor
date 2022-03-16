import time
from .data_classes import *
from .file_writer import write_datafile
from threading import Thread
from enum import Enum
from time import sleep
from datetime import timedelta
from .zumi_sensor_connectivity import SensorConnectivity
import uuid
import logging


class DataSource(Enum):
    """The several existing data sources which can be collected"""

    INFRARED = "INFRARED"
    SYSTEM = "SYSTEM"
    MPU = "MPU"
    CAMERA = "CAMERA"


class RecordingProps:
    """Takes the DataSource, the time step (datetime.timedelta) between recordings, the number of recordings until saving,
    and the run_time (datetime.timedelta) until termination"""

    def __init__(
        self,
        data_source: DataSource,
        time_step: timedelta,
        number_of_recordings: int,
        timeout: timedelta,
    ):
        logging.debug(
            "data_source: {}, time_step: {}, number_of_recordings: {}, timeout: {}".format(
                data_source, time_step, number_of_recordings, timeout
            )
        )
        self.data_source = data_source
        self.time_step = time_step
        self.number_of_recordings = number_of_recordings
        self.run_time = timeout

    def __dict__(self):
        return {
            "data_source": self.data_source.value,
            "time_step": str(self.time_step),
            "timeout": str(self.run_time),
        }


"""Specifies the file names in which the data is collected"""
FILE_NAMES = {
    DataSource.SYSTEM: "system_data",
    DataSource.INFRARED: "ir_data",
    DataSource.MPU: "mpu_data",
    DataSource.CAMERA: "camera_data",
}


class RecordingSession:
    """Takes a set of RecordingProps, which specifies the sensor types to record,
    the time step and the number of records until saving and besides the zumi object it takes the file path to store
    the recorded data"""

    def __init__(
        self,
        recording_props: set,
        zumi,
        folder_path: str,
        session_name: str = "unnamed",
    ):
        logging.debug(
            "recording_props: {}, folder_path: {}, session_name: {}".format(
                recording_props, folder_path, session_name
            )
        )
        self.session_id = str(uuid.uuid4())
        self.recording_props = recording_props
        self.sensor_connectivity = SensorConnectivity(zumi, self.session_id)
        self.folder_path = folder_path
        self.session_name = session_name

    def __get_sensor_data(self, data_source: DataSource) -> TimeseriesData:
        """Gets the sensor data for a specific data source

        :param data_source: a specified data source
        :type data_source: DataSource
        :return: a time series data class object with sensor data
        :rtype: TimeseriesData
        """
        logging.debug("data_source: {}".format(data_source))
        if data_source == DataSource.SYSTEM:
            return self.sensor_connectivity.get_system_data()
        if data_source == DataSource.INFRARED:
            return self.sensor_connectivity.get_infrared_data()
        if data_source == DataSource.MPU:
            return self.sensor_connectivity.get_mpu_data()
        if data_source == DataSource.CAMERA:
            return self.sensor_connectivity.get_camera_data()

    def __collect_sensor_data(self, recording_props: RecordingProps) -> None:
        """Collects sensor data and saves it (in another thread).

        :param recording_props: RecordingProps object containing the sensor to log
        and the specified recording session properties
        :type recording_props: RecordingProps
        """
        timeout = time.time() + recording_props.run_time.seconds
        while True:
            if time.time() >= timeout:
                break
            collected_data = []
            for _ in range(recording_props.number_of_recordings):
                if time.time() >= timeout:
                    break
                collected_data.append(
                    self.__get_sensor_data(recording_props.data_source)
                )
                sleep(recording_props.time_step.microseconds * 0.000001)
            self.__store_data(
                collected_data,
                self.folder_path,
                FILE_NAMES[recording_props.data_source],
            )

    def __store_data(self, data: list, folder_path: str, file_name: str) -> None:
        """Saves data to a folder in a new thread

        :param data: a list of TimeseriesData objects / a session object
        :type data: list
        :param folder_path: target log folder
        :type folder_path: str
        :param file_name: the name the log files will start with
        :type file_name: str
        """
        logging.debug("folder_path: {}, file_name: {}".format(folder_path, file_name))
        Thread(target=lambda: write_datafile(folder_path, file_name, data)).start()

    def start(self) -> None:
        """Start the RecordingSession"""
        self.__store_data(
            [
                {
                    "session_id": self.session_id,
                    "session_name": self.session_name,
                    "sensor_config": [p.__dict__() for p in self.recording_props],
                }
            ],
            self.folder_path,
            "session_data",
        )
        for rp in self.recording_props:
            Thread(target=lambda: self.__collect_sensor_data(rp)).start()
