import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import logging
from datetime import timedelta
from zumi.zumi import Zumi
import yaml
from .random_walk import *
from .collect_data import (
    RecordingSession,
    RecordingProps,
    DataSource,
)
from mongo_db.mongodb_connection import MongoDBConnection
from mongo_db.save_in_mongodb import *


def read_config(config_path: str, zumi: Zumi) -> RecordingSession:
    """Read values from a config file and return a new RecordingSession

    :param config_path: Path to a config file
    :type config_path: str
    :param zumi: Zumi Object
    :type zumi: Zumi
    :return: RecordingSession with session values from the config file
    :rtype: RecordingSession
    """
    with open(config_path, "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    logging.basicConfig(level=cfg["logging"]["level"])
    logging.debug("config_path: {}, zumi: {}".format(config_path, zumi))
    return RecordingSession(
        {
            RecordingProps(
                DataSource.SYSTEM,
                timedelta(seconds=cfg["frequencies"]["system"]),
                cfg["number_of_recordings"]["system"],
                timedelta(seconds=cfg["durations"]["system"]),
            ),
            RecordingProps(
                DataSource.INFRARED,
                timedelta(seconds=cfg["frequencies"]["infrared"]),
                cfg["number_of_recordings"]["infrared"],
                timedelta(seconds=cfg["durations"]["infrared"]),
            ),
            RecordingProps(
                DataSource.MPU,
                timedelta(seconds=cfg["frequencies"]["mpu"]),
                cfg["number_of_recordings"]["mpu"],
                timedelta(seconds=cfg["durations"]["mpu"]),
            ),
            RecordingProps(
                DataSource.CAMERA,
                timedelta(seconds=cfg["frequencies"]["camera"]),
                cfg["number_of_recordings"]["camera"],
                timedelta(seconds=cfg["durations"]["camera"]),
            ),
        },
        zumi,
        folder_path=cfg["logs"]["path"],
    )


def load_default_session(zumi: Zumi) -> RecordingSession:
    """Load default session values and return a new RecordingSession

    :param zumi: Zumi object
    :type zumi: Zumi
    :return: RecordingSession with default values
    :rtype: RecordingSession
    """
    logging.basicConfig(level=logging.INFO)
    logging.debug("zumi: {}".format(zumi))
    return RecordingSession(
        {
            RecordingProps(
                DataSource.SYSTEM,
                timedelta(seconds=2),
                50,
                timedelta(seconds=120),
            ),
            RecordingProps(
                DataSource.INFRARED,
                timedelta(seconds=0.5),
                50,
                timedelta(seconds=120),
            ),
            RecordingProps(
                DataSource.MPU,
                timedelta(seconds=0.1),
                50,
                timedelta(seconds=120),
            ),
            RecordingProps(
                DataSource.CAMERA,
                timedelta(seconds=2),
                10,
                timedelta(seconds=120),
            ),
        },
        zumi,
        folder_path="/home/pi/zumi_logging_data",
    )


def start_recording(rc: RecordingSession) -> None:
    """Start a RecordingSession

    :param rc: the RecordingSession to start
    :type rc: RecordingSession
    """
    logging.debug("rc (RecordingSession): {}".format(rc))
    try:
        rc.start()
    except Exception as e:
        stop(zumi)
        logging.error(str(e))


def start_random_walk(
    zumi: Zumi, execution_time: timedelta = timedelta(seconds=120)
) -> None:
    """Start the Zumi random walk

    :param zumi: Zumi object
    :type zumi: Zumi
    :param execution_time: how long the random walk should run, defaults to 120
    :type execution_time: int, optional
    """
    logging.debug("zumi: {}, execution_time: {}".format(zumi, execution_time))
    try:
        random_walk(zumi, execution_time)
    except Exception as e:
        stop(zumi)
        logging.error(str(e))


def save_logs_to_database(
    config_path: str = None, log_path: str = None, mongodb_uri: str = None
) -> None:
    """Save the Zumi logs to a mongodb database

    :param mongodb_uri: the URI of the mongoDB database
    :type mongodb_uri: str
    :param log_path: path where to read the log files from
    :type log_path: str
    """
    if config_path is not None:
        with open(config_path, "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        mongodb_uri = cfg["mongodb"]["uri"]
        log_path = cfg["logs"]["path"]
    logging.debug("mongodb_uri: {}, log_path: {}".format(mongodb_uri, log_path))
    connection = MongoDBConnection(mongodb_uri)
    collections = connection.get_all_collections()
    for ctype in collections:
        transfer_all_json_files(connection, ctype, log_path)
    connection.close()


def stop(zumi: Zumi) -> None:
    """Stop the Zumi in case of errors

    :param zumi: Zumi object
    :type zumi: Zumi
    """
    zumi.stop()
    zumi = Zumi()
    logging.info("Zumi stopped successfully. Nothalt powered by Arian")
    exit()
