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

import pandas as pd
import csv
import os

from .DataConfig import ConfigSet

class ScenarioFile(object):
    """
    Class representing individual input data files. Contains methods to parse and format those files based on configs.
    """

    SPATIAL_CUMULATIVE = {
        'id': 'total',
        'label': 'Cumulative'
    }

    TEMPORAL_CUMULATIVE = {
        'id': 'total',
        'label': 'Cumulative'
    }

    def __init__(self, config_set, fp, scenario, attribute, temporal_resolution, spatial_resolution):
        assert isinstance(config_set,ConfigSet)
        self.config_set = config_set

        self.fp = fp
        self.scenario = config_set.scenario_configs.find_by_id(scenario)
        self.attribute = config_set.attribute_configs.find_by_id(attribute)
        self.temporal_resolution = config_set.temporal_configs.find_by_id(temporal_resolution)
        self.spatial_resolution = config_set.spatial_configs.find_by_id(spatial_resolution)

        self.cumulative_spatial = self.spatial_resolution is None or self.spatial_resolution['id'] == 'national'
        self.cumulative_temporal = self.temporal_resolution is None

        self.__data = None
        self.temporal_config = None
        self.spatial_config = None
        self.cumulative_data = None
        self.national_data = None
        self.geom_data = None

    @property
    def scenario_id(self):
        return self.scenario['id']

    @property
    def attribute_id(self):
        return self.attribute['id']

    @property
    def temporal_resolution_id(self):
        return self.temporal_resolution['id']

    @property
    def spatial_resolution_id(self):
        return self.spatial_resolution['id']

    def __repr__(self):
        return "ScenarioFile({},{},{},{},{},{})".format(
            repr(self.config_set),
            repr(self.fp),
            repr(self.scenario_id),
            repr(self.attribute_id),
            repr(self.temporal_resolution_id),
            repr(self.spatial_resolution_id))

    def read(self):
        self.__data = pd.read_csv(self.fp)

        # ETH@20170822 - I think this is mapping state abbreviations to FIPS codes. 
        # I would rather have state abbreviations.
        # with open(os.path.abspath('../data/spatial/state_fips_codes.csv'), 'rU') as f:
        #     reader = csv.DictReader(f)
        #     fips_codes = {row['state']: row['fips'] for row in reader}

        # if 'gid' in list(self.__data.columns):
        #     self.__data = self.__data[self.__data['gid'] != 'MEX']         # Remove Mexico
        #     self.__data['gid'] = self.__data['gid'].map(fips_codes, na_action='ignore')

    def get_data(self):
        if 'time' in self.__data.columns:
            self.__data['time'] = self.__data['time'].astype(str)
        self.__data['value'].round(4)

        additional_columns = list(self.__data.columns.difference(['gid', 'value', 'time']))

        if len(additional_columns) == 1:
            response = {}
            if self.cumulative_spatial:
                grouped = self.__data.groupby(additional_columns[0])
                for name, group in grouped:
                    group = group.drop(additional_columns[0], axis=1)

                    if self.cumulative_temporal:
                        response[name] = {'value': float("{0:.4f}".format(d['value'])) for d in group.to_dict(orient='records')}
                    else:
                        response[name] = {d['time']: float("{0:.4f}".format(d['value'])) for d in group.to_dict(orient='records')}
            else:
                try:
                    spatial_grouped = self.__data.groupby(['gid'])
                except KeyError as e:
                    print(self.fp)
                    print(self.spatial_resolution)
                    raise e
                for spatial_name, spatial_group in spatial_grouped:
                    response[spatial_name] = {
                        self.attribute['id']: {}
                    }
                    spatial_group = spatial_group.drop('gid', axis=1)

                    attr_grouped = spatial_group.groupby(additional_columns[0])
                    for attr_name, attr_group in attr_grouped:
                        attr_group = attr_group.drop(additional_columns[0], axis=1)
                        response[spatial_name][self.attribute['id']][attr_name] = {d['time']: float("{0:.4f}".format(d['value'])) for d in
                                                             attr_group.to_dict(orient='records')}

        else:
            if self.cumulative_spatial:
                if self.cumulative_temporal:
                    response = {'value': float("{0:.4f}".format(d['value'])) for d in
                            self.__data.to_dict(orient='records')}
                else:
                    response = {d['time']: float("{0:.4f}".format(d['value'])) for d in
                            self.__data.to_dict(orient='records')}
            else:
                response = {}
                spatial_grouped = self.__data.groupby(['gid'])
                for spatial_name, spatial_group in spatial_grouped:
                    response[spatial_name] = {}
                    spatial_group = spatial_group.drop('gid', axis=1)

                    if self.cumulative_temporal:
                        response[spatial_name][self.attribute['id']] = {'value': float("{0:.4f}".format(d['value']))
                                                                        for d
                                                                        in spatial_group.to_dict(orient='records')}
                    else:
                        response[spatial_name][self.attribute['id']] = {d['time']: float("{0:.4f}".format(d['value'])) for d
                                                                    in
                                                                    spatial_group.to_dict(orient='records')}

        return response
