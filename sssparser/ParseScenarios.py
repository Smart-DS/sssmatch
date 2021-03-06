# [LICENSE]
# Copyright (c) 2018 Alliance for Sustainable Energy, LLC. All rights reserved.
# 
# NOTICE: This software was developed at least in part by Alliance for Sustainable Energy, LLC ("Alliance") under Contract No. DE-AC36-08GO28308 with the U.S. Department of Energy and the U.S. Government retains for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in the software to reproduce, prepare derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, the above government rights notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice, the above government rights notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 
# 3.  Redistribution of this software, without modification, must refer to the software by the same designation. Redistribution of a modified version of this software (i) may not refer to the modified version by the same designation, or by any confusingly similar designation, and (ii) must refer to the underlying software originally provided by Alliance as "sssmatch". Except to comply with the foregoing, the term "sssmatch", or any confusingly similar designation may not be used to refer to any modified version of this software or any modified version of the underlying software originally provided by Alliance without the prior written consent of Alliance.
# 
# 4.  The name of the copyright holder, contributors, the United States Government, the United States Department of Energy, or any of their employees may not be used to endorse or promote products derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER, CONTRIBUTORS, UNITED STATES GOVERNMENT OR UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# [/LICENSE]

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

