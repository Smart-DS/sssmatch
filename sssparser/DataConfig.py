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
