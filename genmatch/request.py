import copy
import logging
import os
from shutil import copyfile
from subprocess import call

import numpy as np
import pandas as pds

from genmatch import GenmatchError, models_dir

logger = logging.getLogger(__name__)

class Request(object):

    RESOURCE_INDEPENDENT = ['Biopower','Coal','NG-CC','NG-CT','Nuclear','Oil-Gas-Steam','Storage']
    DEFAULT_GENTYPE_DISTANCE_FILE = os.path.join(models_dir,'default_gendists.csv')

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

    def drop_default_gendists(self,filename=None):
        data = []
        for g in self.gentypes:
            for gg in self.gentypes:
                if gg == g:
                    continue
                if gg not in self.RESOURCE_INDEPENDENT or \
                   (g in self.RESOURCE_INDEPENDENT and gg in self.RESOURCE_INDEPENDENT):
                    data.append([g,gg,0.0])
                else:
                    data.append([g,gg,1.0])
        if filename is None:
            filename = self.DEFAULT_GENTYPE_DISTANCE_FILE
        pds.DataFrame(data,columns=['g','gg','Value']).to_csv(filename,index=False)

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
        assert self._resource_dependent_test()
        
    def _resource_independent_test(self):
        totals = self.summary[self.summary.index.isin(self.RESOURCE_INDEPENDENT)].sum()
        if totals['Desired Capacity (MW)'] > totals['Current Capacity (MW)']:
            msg = "Unable to create a new generation mix that has more " + \
                  "resource-independent capacity than the current system." + \
                  "Resource-independent generation types are: {}.".format(self.RESOURCE_INDEPENDENT) + \
                  "Current and desired capacity of this sort is:\n{}".format(totals)
            raise GenmatchError(msg)
        logger.debug("Resource-independent generation types are: {}.".format(self.RESOURCE_INDEPENDENT) + \
                     "Current and desired capacity of this sort is:\n{}".format(totals))
        return True

    def _resource_dependent_test(self):
        for gentype in self.summary.index:
            if gentype in self.RESOURCE_INDEPENDENT:
                continue
            desired = self.summary.loc[gentype,'Desired Capacity (MW)']
            current = self.summary.loc[gentype,'Current Capacity (MW)']
            if desired > current:
                if gentype not in self.nodes:
                    msg = "Unable to create a new generation mix with {} MW {} capacity,".format(desired,gentype) + \
                          "because there is only {} MW in current capacity, ".format(current) + \
                          "and no maximum quantity is specified for each node."
                    raise GenmatchError(msg)
                maximum = self.nodes[gentype].sum()
                if desired > maximum:
                    msg = "Unable to create a new generation mix with {} MW {} capacity, ".format(desired,gentype) + \
                          "because the specified maximum supply only {} MW.".format(maximum)
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

    def fulfill(self,outdir,gendists=None,precision=0):
        """
        Arguments:
            - outdir (str) - directory in which to run matching model and place results
            - precision (int) - number of digits after the decimal point to match desired mix to, in MW
        """
        if not hasattr(self,'summary'):
            self.preprocess()

        if not os.path.exists(outdir):
            os.mkdir(outdir)

        # TODO: Give user the option of algebraic modeling language
        from gdxpds.gdx import GdxFile, GdxSymbol, GamsDataType

        with GdxFile() as ingdx:
            # Sets
            ingdx.append(GdxSymbol('n',GamsDataType.Set,dims=['n']))
            df = pds.DataFrame(self.nodes['node_id'])
            df['Value'] = True
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g',GamsDataType.Set,dims=['g']))
            df = pds.DataFrame([[g, True] for g in self.gentypes],
                               columns=['g','Value'])
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g_indep',GamsDataType.Set,dims=['g']))
            df = pds.DataFrame([[g, True] for g in self.gentypes if g in self.RESOURCE_INDEPENDENT],
                               columns=['g','Value'])
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g_dep',GamsDataType.Set,dims=['g']))
            df = pds.DataFrame([[g, True] for g in self.gentypes if g not in self.RESOURCE_INDEPENDENT],
                               columns=['g','Value'])
            ingdx[-1].dataframe = df

            # Parameters
            ingdx.append(GdxSymbol('desired_capacity',GamsDataType.Parameter,dims=['g']))
            df = pds.DataFrame(self.summary['Desired Capacity (MW)'].apply(lambda x: round(x,precision)))
            df = df.reset_index()
            df.columns = ['g','Value']
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('current_capacity',GamsDataType.Parameter,dims=['n','g']))
            # pivot with sum on capacity in case there are multiple units of type g at node n
            df = pds.pivot_table(self.generators,
                                 values='capacity (MW)',
                                 index=['node_id','generator type'],
                                 aggfunc=np.sum)
            df = df.reset_index()
            df.columns = ['n','g','Value']
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g_dist',GamsDataType.Parameter,dims=['g','gg']))
            gendists_filename = gendists if gendists is not None else self.DEFAULT_GENTYPE_DISTANCE_FILE
            df = pds.read_csv(gendists_filename)
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('current_indep_capacity',GamsDataType.Parameter,dims=['n']))
            df = pds.pivot_table(self.generators[self.generators['generator type'].isin(self.RESOURCE_INDEPENDENT)],
                                 values='capacity (MW)',
                                 index=['node_id'],
                                 aggfunc=np.sum)
            df = df.reset_index()
            df.columns = ['n','Value']
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('maximum_capacity',GamsDataType.Parameter,dims=['n','g_dep']))
            dep_gentypes = [g for g in self.gentypes if g not in self.RESOURCE_INDEPENDENT]
            df = pds.pivot_table(self.generators[self.generators['generator type'].isin(dep_gentypes)],
                                 values='capacity (MW)',
                                 index=['node_id','generator type'],
                                 aggfunc=np.sum)
            df = df.reset_index()
            df.columns = ['n','g','Value']
            ingdx[-1].dataframe = df

            ingdx.write(os.path.join(outdir,'in.gdx'))

        model_file = 'match_generators.gms'
        copyfile(os.path.join(models_dir,model_file),os.path.join(outdir,model_file))

        curdir = os.getcwd()
        os.chdir(outdir)
        call(['gams',model_file])
        os.chdir(curdir)
