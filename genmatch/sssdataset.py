
import logging

from sssparser.DataConfig import DEFAULT_SCENARIO_DATA_DIRNAME
from sssparser.ParseScenarios import parse_dataset

logger = logging.getLogger(__name__)

class SSSDataset(object):
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
