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

import logging

import pandas as pds

from sssparser import SSSParserError
from .DataConfig import DEFAULT_SCENARIO_DATA_DIRNAME
from .ParseScenarios import parse_dataset

logger = logging.getLogger(__name__)

class ScenariosDataset(object):
    GENMIX_ATTRIBUTES = ['capacity','generation']

    def __init__(self,dataset_dir,scenario_data_dirname=DEFAULT_SCENARIO_DATA_DIRNAME):
        """
        Parameters
        ----------
        dataset_dir : str
            Name of the directory containing the dataset to be examined, e.g. 
            'NREL Standard Scenarios 2016'
        scenario_data_dirname : str
            Directory that holds all of the datasets of interest (e.g. sssmatch/sssmixes)
        """
        config_set, grouped_files = parse_dataset(dataset_dir,scenario_data_dirname=scenario_data_dirname)
        self.__cache = {}
        self.name = scenario_data_dirname
        self.config_set = config_set
        self.grouped_files = grouped_files
        for group in self.grouped_files:
            for f in group:
                f.read()

    @property
    def gentypes(self):
        """
        Assumes generator types can be inferred from ScenarioFiles with 
        attribute_id == 'capacity' and spatial_resolution_id == 'national'.

        Returns
        -------
        list
            List of generator types found in the ScenariosDataset
        """
        gentypes = set()
        for group in self.grouped_files:
            for f in group:
                if f.attribute_id == 'capacity' and f.spatial_resolution_id == 'national':
                    gentypes.update(f.get_data().keys())
        return sorted(list(gentypes))

    @property
    def years(self):
        result = None
        for group in self.grouped_files:
            for f in group:
                if f.attribute_id == 'capacity' and f.spatial_resolution_id == 'national':
                    data = f.get_data()
                    result = list(data[list(data.keys())[0]].keys())
                    break
            if result:
                break
        return result

    @property
    def scenarios(self):
        result = []
        for group in self.grouped_files:
            result.append(group[0].scenario_id)
        return result

    @property
    def geographies(self):
        result = ['national']
        for group in self.grouped_files:
            for f in group:
                if f.attribute_id == 'capacity' and f.spatial_resolution_id == 'states':
                    data = f.get_data()
                    result.extend(list(data.keys()))
                    break
            if len(result) > 1:
                break
        return result

    def _get_data(self,scenario_file):
        key = (scenario_file.scenario_id,scenario_file.attribute_id,scenario_file.spatial_resolution_id)
        if key not in self.__cache:
            self.__cache[key] = scenario_file.get_data()
        return self.__cache[key]

    def get_genmix(self,year,scenario_id,geography_ids):
        """
        Return dataframe indexed by generator type and showing select attributes.

        Arguments:
            - year (string) - a year in self.years
            - scenario_id (string) - a scenario in self.scenarios
            - geogrpahy_id (list of strings) - a subset of self.geographies
        """
        def attribute_label(scenario_file):
            return "{} ({})".format(scenario_file.attribute['label'],
                                    scenario_file.attribute['units'])

        def get_national_data(scenario_file):
            data = self._get_data(scenario_file)
            tmp = []; index = []
            for gen_type, values in data.items():
                tmp.append(values[year])
                index.append(gen_type)
            return pds.Series(tmp,index=index,name=attribute_label(scenario_file))

        def get_states_data(scenario_file,states):
            data = self._get_data(scenario_file)
            result = None
            for state in states:
                state_data = data[state]
                extra_key = list(state_data.keys())[0]
                tmp = []; index = []
                for gen_type, values in state_data[extra_key].items():
                    tmp.append(values[year])
                    index.append(gen_type)
                tmp = pds.Series(tmp,index=index,name=attribute_label(scenario_file))
                if result is None:
                    result = tmp
                    continue
                result = result.add(tmp,fill_value=0.0)
            return result

        result = []
        national = False; states = []
        if 'national' in geography_ids:
            national = True
        else:
            assert 'national' not in geography_ids
            states = geography_ids
        for group in self.grouped_files:
            if (group[0].scenario_id != scenario_id) and (group[0].scenario['label'] != scenario_id):
                continue
            for f in group:
                if f.attribute_id in self.GENMIX_ATTRIBUTES:
                    if national and f.spatial_resolution_id == 'national':
                        result.append(get_national_data(f))
                    elif states and f.spatial_resolution_id == 'states':
                        result.append(get_states_data(f,states))
        if not result:
            raise SSSParserError("No generation mix availabale for year '{}', scenario_id '{}', geography_ids = '{}'".format(year,scenario_id,geography_ids))
        result = pds.concat(result,axis=1)
        # calculate fractions
        original_columns = result.columns
        for col in original_columns:
            attribute_name = col.split(' ')[0]
            result[attribute_name + ' Fraction'] = result[col] / result[col].sum()
        # summarize in a total line
        totals = result.sum()
        totals.name = 'TOTAL'
        result = pds.concat([result,pds.DataFrame(totals).T])
        return result

    def get_timeseries(self,scenario_id,geography_ids):
        """
        Calls self.get_genmix for every year in self.years. Returns a 
        pandas.Series indexed by ['dataset','scenario','geography','year',
        'gentype','variable']. The geography key is ','.join(geography_ids).
        """
        data = []
        for yr in self.years:
            mix = self.get_genmix(yr,scenario_id,geography_ids)
            mix.index.name = 'gentype'
            value_vars = mix.columns
            mix = mix.reset_index()
            mix['dataset'] = self.name
            mix['scenario'] = scenario_id
            mix['geography'] = ','.join(geography_ids)
            mix['year'] = int(yr)
            mix = pds.melt(mix,
                           id_vars=['dataset','scenario','geography','year','gentype'],
                           value_vars=value_vars)
            mix = multi_index(mix,['dataset','scenario','geography','year','gentype','variable'])
            data.append(mix)
        return pds.concat(data)

# Helpers

def multi_index(df, cols):
    result = df.copy()
    result.index = result[cols[0]] if len(cols) == 1 else pds.MultiIndex.from_tuples(list(zip(*[result[col].tolist() for col in cols])),names = cols)
    for col in cols:
        del result[col]
    return result
