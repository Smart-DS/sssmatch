from functools import reduce
import os
import sys
# import string

# from scoop import futures

from .DataConfig import ConfigSet, DEFAULT_SCENARIO_DATA_DIRNAME
from .ScenarioFile import ScenarioFile


def parse_file_name(s,config_set):
    """
    Parses the filename into the relevant configuration components and returns as a dict
    :param s: filename
    :return: dict
    """
    basename = os.path.splitext(s)[0]
    file_components = basename.split('.')
    file_info = {
        'fp': os.path.abspath(os.path.join(config_set.scenario_data_dir, s)),
        'scenario': file_components[0].strip(),
        'attribute': file_components[1].strip(),
        'temporal_resolution': file_components[2].strip(),
        'spatial_resolution': file_components[3].strip()
    }

    return ScenarioFile(config_set,**file_info)


def group_file_info(l, d):
    """
    Reduce function for grouping file dicts from parse_file_name by scenario
    :param l:
    :param d:
    :return: list
    """

    if d.scenario in [group[0].scenario for group in l]:
        group = next(group for group in l if d.scenario == group[0].scenario)
        group.append(d)
    else:
        l.append([d])

    return l


def parse_dataset(dataset_dir,scenario_data_dirname=DEFAULT_SCENARIO_DATA_DIRNAME):
    config_set = ConfigSet(dataset_dir,scenario_data_dirname=scenario_data_dirname)

    valid_files = filter(lambda fp: not fp.startswith('.'), os.listdir(config_set.scenario_data_dir))
    scenario_files = map(lambda x: parse_file_name(x,config_set), valid_files)
    grouped_scenario_files = reduce(group_file_info, scenario_files, [])

    return config_set, grouped_scenario_files

