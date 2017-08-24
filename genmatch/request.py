import copy
import logging

import numpy as np
import pandas as pds

from genmatch import GenmatchError

logger = logging.getLogger(__name__)

class Request(object):

    RESOURCE_INDEPENDENT = ['Biopower','Coal','NG-CC','NG-CT','Nuclear','Oil-Gas-Steam','Storage']

    def __init__(self,nodes,generators,dataset,desired_mix,exclusions=[]):
        self.nodes = nodes
        self.generators = generators
        self.dataset = dataset
        self.original_desired_mix = desired_mix
        self.exclusions = exclusions if exclusions is not None else []

    @classmethod
    def nodes_columns(cls,re_types):
        return ['node_id','latitude','longitude','peak load (MW)','annual load (GWh)'] + list(re_types)

    @classmethod
    def generators_columns(cls):
        return ['node_id','generator type','capacity (MW)']

    @property
    def gentypes(self):
        return [gentype for gentype in self.dataset.gentypes if gentype not in self.exclusions]

    @property
    def current_mix(self):
        result = pds.pivot_table(self.generators,
                                 values='capacity (MW)',
                                 index='generator type',
                                 aggfunc=np.sum)
        result.name = 'Current Capacity (MW)'
        return result

    def preprocess(self):
        self.desired_mix = copy.deepcopy(self.original_desired_mix)
        del self.desired_mix['Capacity Fraction']; del self.desired_mix['Generation Fraction']

        # filter desired_mix
        self.desired_mix = self.desired_mix[self.desired_mix.index.isin(self.gentypes)]

        # scale desired_mix
        self.system_load = self.nodes['annual load (GWh)'].sum() / 1000.0
        self.genmix_generation = self.annual_useable_generation(
            self.original_desired_mix,
            self.gentypes)
        self.scale_factor = self.system_load / self.genmix_generation
        logger.info("System load is {:.3f} TWh. ".format(self.system_load) + 
                    "The generation mix is based on {:.3f} TWh of useable generation. ".format(self.genmix_generation) + 
                    "Thus the generation mix capacities will be scaled by a factor of {}.".format(self.scale_factor))
        self.desired_mix = self.desired_mix * self.scale_factor

        # determine if request is at all feasible
        desired_mw = self.desired_mix['Capacity (GW)'] * 1000.0
        desired_mw.name = 'Desired Capacity (MW)'
        self.summary = pds.DataFrame(self.current_mix).merge(pds.DataFrame(desired_mw),how='outer',left_index=True,right_index=True)
        logger.info("Request summary:\n{}".format(self.summary))

        assert self._resource_independent_test()
        # HERE -- resource-dependent must either have enough already in place, 
        # or have sufficient maximum capacities.
        
    def _resource_independent_test(self):
        totals = self.summary[self.summary.index.isin(self.RESOURCE_INDEPENDENT)].sum()
        if totals['Desired Capacity (MW)'] > totals['Current Capacity (MW)']:
            msg = "Unable to create a new generation mix that has more " + \
                  "resource-independent capacity than the current system." + \
                  "Resource-independent generation types are: {}.".format(self.RESOURCE_INDEPENDENT) + \
                  "Current and desired capacity of this sort is:\n{}".format(totals)
            raise GenmatchError(msg)
        return True

    @classmethod
    def annual_useable_generation(cls,genmix,gentypes):
        """
        Returns the useable generation in TWh for genmix.
        """
        result = genmix[genmix.index.isin(gentypes)]['Generation (TWh)'].sum()
        if 'Curtailment' in genmix.index:
            result += genmix.loc['Curtailment','Generation (TWh)']
        return result
