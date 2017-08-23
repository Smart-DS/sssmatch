
import logging

import pandas as pds

from genmatch import GenmatchError
from sssparser.DataConfig import DEFAULT_SCENARIO_DATA_DIRNAME
from sssparser.ParseScenarios import parse_dataset

logger = logging.getLogger(__name__)

class SSSDataset(object):
    GENMIX_ATTRIBUTES = ['capacity','generation','genFraction']

    def __init__(self,dataset_dir,scenario_data_dirname=DEFAULT_SCENARIO_DATA_DIRNAME):
        config_set, grouped_files = parse_dataset(dataset_dir,scenario_data_dirname=scenario_data_dirname)
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

    def get_genmix(self,year,scenario_id,geography_ids):
        """
        Return dataframe indexed by generator type and showing select attributes.
        """
        def attribute_label(scenario_file):
            return "{} ({})".format(scenario_file.attribute['label'],
                                    scenario_file.attribute['units'])

        def get_national_data(scenario_file):
            data = scenario_file.get_data()
            return pds.Series([values[year] for gen_type, values in data.items()],
                              index=[gen_type for gen_type in data.keys()],
                              name=attribute_label(scenario_file))

        def get_states_data(scenario_file,states):
            data = scenario_file.get_data()
            result = None
            for state in states:
                state_data = data[state]
                extra_key = list(state_data.keys())[0]
                tmp = pds.Series([values[year] for gen_type, values in state_data[extra_key].items()],
                                 index=[gen_type for gen_type in state_data[extra_key].keys()],
                                 name=attribute_label(scenario_file))
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
            raise GenmatchError("No generation mix availabale for year '{}', scenario_id '{}', geography_ids = '{}'".format(year,scenario_id,geography_ids))
        result = pds.concat(result,axis=1)
        return result
