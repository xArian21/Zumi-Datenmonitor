import os
from fnmatch import fnmatch
from natsort import natsorted
from bson.json_util import dumps


def __write_json_file(file_path: str, content: list) -> None:
    """Saves a list to a json file

    :param file_path: the target log file including path (no extension)
    :type file_path: str
    :param content: a list of dicts
    :type content: list
    """
    output = [e if isinstance(e, dict) else e.__dict__ for e in content]
    with open(file_path + ".json", "w") as f:
        f.write(dumps(output))


def __get_existing_files(folder_path: str, file_name: str) -> list:
    """Returns a sorted list of all json files matching a string from a folder

    :param folder_path: the target folder containing the log files
    :type folder_path: str
    :param file_name: the name the log files are starting with
    :type file_name: str
    :return: sorted list of matching files
    :rtype: list
    """
    file_list = []
    for filename in os.listdir(folder_path):
        if fnmatch(filename, file_name + "*.json"):
            file_list.append(filename)
    file_list = natsorted(file_list)
    return file_list


def write_datafile(folder_path: str, file_name: str, content: list) -> None:
    """Creates a new data file with increasing index

    :param folder_path: the target folder containing the log files
    :type folder_path: str
    :param file_name: the name the log files are starting with
    :type file_name: str
    :param content: list of dicts that will be saved to a file
    :type content: list
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_list = __get_existing_files(folder_path, file_name)
    if len(file_list) == 0:
        __write_json_file(os.path.join(folder_path, file_name) + "1", content)
    else:
        next_index = int(file_list[-1][len(file_name) : -5]) + 1
        __write_json_file(
            os.path.join(folder_path, file_name) + str(next_index), content
        )
