'''
[LICENSE]
Copyright (c) 2017 Alliance for Sustainable Energy, LLC. All rights reserved.

NOTICE: This software was developed at least in part by Alliance for Sustainable Energy, LLC (“Alliance”) under Contract No. DE-AC36-08GO28308 with the U.S. Department of Energy and the U.S. Government retains for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in the software to reproduce, prepare derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, the above government rights notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, the above government rights notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3.  Redistribution of this software, without modification, must refer to the software by the same designation. Redistribution of a modified version of this software (i) may not refer to the modified version by the same designation, or by any confusingly similar designation, and (ii) must refer to the underlying software originally provided by Alliance as “sssmatch”. Except to comply with the foregoing, the term “sssmatch”, or any confusingly similar designation may not be used to refer to any modified version of this software or any modified version of the underlying software originally provided by Alliance without the prior written consent of Alliance.

4.  The name of the copyright holder, contributors, the United States Government, the United States Department of Energy, or any of their employees may not be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER, CONTRIBUTORS, UNITED STATES GOVERNMENT OR UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
[/LICENSE]
'''

import csv
import logging
import os

logger = logging.getLogger(__name__)

FIPS_PATH = '../data/spatial/state_fips_codes.csv'

DEFAULT_SCENARIO_DATA_DIRNAME = 'ScenarioData'


class DataConfig(list):
    """
    Base class for all data configs
    """

    def __init__(self, fp):
        self.fp = fp

        self.headers = None
        self.fetch()

    def fetch(self):
        with open(self.fp, 'rU') as f:
            reader = csv.DictReader(f)

            self.headers = reader.fieldnames
            for row in reader:
                self.append(row)

    @property
    def ids(self):
        return [d['id'] for d in self]

    def find_by_id(self, config_id):

        def id_matches(config_id, candidate):
            if config_id == candidate:
                return True
            elif config_id.startswith('X'):
                return config_id[1:] == candidate
            return False

        try:
            config = next(d for d in self if id_matches(config_id,d['id']))
        except StopIteration:
            logger.error("{} not found in {}".format(config_id, [d['id'] for d in self]))
            config = None

        return config


class ConfigSet(object):
    def __init__(self,dataset_dir,scenario_data_dirname=DEFAULT_SCENARIO_DATA_DIRNAME):
        self.dataset_dir = dataset_dir
        self.scenario_data_dir = os.path.join(self.dataset_dir,scenario_data_dirname)
        # May need to point to FIPS code file as well

        self.scenario_configs = DataConfig(os.path.join(dataset_dir,'scenarios.csv'))
        self.attribute_configs = DataConfig(os.path.join(dataset_dir,'attributes.csv'))
        self.temporal_configs = DataConfig(os.path.join(dataset_dir,'temporal_resolutions.csv'))
        self.spatial_configs = DataConfig(os.path.join(dataset_dir,'spatial_resolutions.csv'))

    def __repr__(self):
        scenario_data_dirname = os.path.basename(self.scenario_data_dir)
        if scenario_data_dirname == DEFAULT_SCENARIO_DATA_DIRNAME:
            return "ConfigSet({})".format(repr(self.dataset_dir))
        return "ConfigSet({},scenario_data_dirname={})".format(repr(self.dataset_dir),repr(scenario_data_dirname))
