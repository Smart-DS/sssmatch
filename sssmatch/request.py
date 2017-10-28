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

import copy
from enum import Enum, auto
import logging
import os
from shutil import copyfile
from subprocess import call

import numpy as np
import pandas as pds

from sssmatch import SSSMatchError, models_dir

logger = logging.getLogger(__name__)


class AML(Enum):
    """
    Supported Algebraic Modeling Languages
    """
    GAMS = auto()


class Request(object):

    RESOURCE_INDEPENDENT = ['Biopower','Coal','NG-CC','NG-CT','Nuclear','Oil-Gas-Steam','Storage']
    R2PD_TECHS_MAP = {'Land-based Wind': ['wind'],
                      'Rooftop PV': ['solar','rooftop'],
                      'Utility PV': ['solar','one-axis-tracking']}
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

    @classmethod
    def generators_swapped_columns(cls):
        return ['node_id','from generator type','to generator type','capacity (MW)']


    @property
    def gentypes(self):
        return [gentype for gentype in self.dataset.gentypes if gentype not in self.exclusions]

    @property
    def current_mix(self):
        result = pds.pivot_table(self.generators,
                                 values='capacity (MW)',
                                 index='generator type',
                                 aggfunc=np.sum)
        result.columns = ['Current Capacity (MW)']
        return result


    def drop_default_gendists(self,filename=None):
        """
        Prepopulates a gendists csv and saves it to filename, see fulfill. 
        """
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
        self.summary = self.current_mix.merge(pds.DataFrame(desired_mw),how='outer',left_index=True,right_index=True)
        self.summary.fillna(0.0,inplace=True)
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
            raise SSSMatchError(msg)
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
                    raise SSSMatchError(msg)
                maximum = self.nodes[gentype].sum()
                if desired > maximum:
                    msg = "Unable to create a new generation mix with {} MW {} capacity, ".format(desired,gentype) + \
                          "because the specified maximum supply only {} MW.".format(maximum)
                    raise SSSMatchError(msg)
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


    def fulfill(self,outdir,gendists=None,precision=0,aml=AML.GAMS):
        """
        Arguments:
            - outdir (str) - directory in which to run matching model and place 
              results
            - gendists (str) - path to csv of (gentype_from, gentype_to, 
              distance)
            - precision (int) - number of digits after the decimal point to 
              match desired mix to, in MW
            - aml (AML) - value of the AML enum that corresponds to the 
              algebraic modeling language you would like to use
        """
        if not hasattr(self,'summary'):
            self.preprocess()

        model = None
        if aml == AML.GAMS:
            model = GamsModel(self,outdir)
        assert model is not None, "Choose from one of the available algebraic modeling languages: {}".format(",".join([val.name for val in AML]))

        model.setup(gendists=gendists,precision=precision)
        model.run()
        ret = model.collect_results()
        if not ret:
            raise SSSMatchError('Running the match model {} failed. Examine outputs in {}.'.format(model.MODEL_FILE,outdir))
        self.save_results(outdir)


    def register_results(self,capacity,capacity_added,capacity_kept,
                         capacity_swapped,capacity_removed,distance):
        """
        All of the arguments except for distance are dataframes in the same 
        format as self.generators. Distance is the scalar objective function 
        value.
        """
        self.capacity = capacity
        self.capacity_added = capacity_added
        self.capacity_kept = capacity_kept
        self.capacity_swapped = capacity_swapped
        self.capacity_removed = capacity_removed
        self.distance = distance
        self.compile_result_summary()


    def compile_result_summary(self):
        self.result_summary = copy.deepcopy(self.summary)

        kept_mw = pds.pivot_table(self.capacity_kept,
                                  values='capacity (MW)',
                                  index='generator type',
                                  aggfunc=np.sum)
        kept_mw.columns = ['kept (MW)']
        self.result_summary = self.result_summary.merge(pds.DataFrame(kept_mw),how='outer',left_index=True,right_index=True)

        swapped_out = pds.pivot_table(self.capacity_swapped,
                                      values='capacity (MW)',
                                      index='from generator type',
                                      aggfunc=np.sum)
        swapped_out.columns = ['swapped out (MW)']
        self.result_summary = self.result_summary.merge(pds.DataFrame(swapped_out),how='outer',left_index=True,right_index=True)

        swapped_in = pds.pivot_table(self.capacity_swapped,
                                     values='capacity (MW)',
                                     index='to generator type',
                                     aggfunc=np.sum)
        swapped_in.columns = ['swapped in (MW)']
        self.result_summary = self.result_summary.merge(pds.DataFrame(swapped_in),how='outer',left_index=True,right_index=True)

        added = pds.pivot_table(self.capacity_added,
                                values='capacity (MW)',
                                index='generator type',
                                aggfunc=np.sum)
        added.columns = ['added (MW)']
        self.result_summary = self.result_summary.merge(pds.DataFrame(added),how='outer',left_index=True,right_index=True)

        removed = pds.pivot_table(self.capacity_removed,
                                  values='capacity (MW)',
                                  index='generator type',
                                  aggfunc=np.sum)
        removed.columns = ['removed (MW)']
        self.result_summary = self.result_summary.merge(pds.DataFrame(removed),how='outer',left_index=True,right_index=True)

        final = pds.pivot_table(self.capacity,
                                values='capacity (MW)',
                                index='generator type',
                                aggfunc=np.sum)
        final.columns = ['final (MW)']
        self.result_summary = self.result_summary.merge(pds.DataFrame(final),how='outer',left_index=True,right_index=True)

        self.result_summary.fillna(0.0,inplace=True)

        total = self.result_summary.sum()
        total.name = 'TOTAL'
        self.result_summary = pds.concat([self.result_summary,pds.DataFrame(total).T])
        return


    def save_results(self,outdir):
        assert hasattr(self,'distance'), 'This method can only be run after a successful call to self.fulfill.'
        self.capacity.to_csv(os.path.join(outdir,'new_generators.csv'),index=False)

        details_dir = os.path.join(outdir,'match_details')
        if not os.path.exists(details_dir):
            os.mkdir(details_dir)
        self.capacity.to_csv(os.path.join(details_dir,'capacity.csv'),index=False)
        self.capacity_added.to_csv(os.path.join(details_dir,'capacity_added.csv'),index=False)
        self.capacity_kept.to_csv(os.path.join(details_dir,'capacity_kept.csv'),index=False)
        self.capacity_swapped.to_csv(os.path.join(details_dir,'capacity_swapped.csv'),index=False)
        self.capacity_removed.to_csv(os.path.join(details_dir,'capacity_removed.csv'),index=False)

        for gentype, r2pd_call in self.R2PD_TECHS_MAP.items():
            r2pd_dir = os.path.join(outdir,"_".join(r2pd_call))
            df = self.capacity[self.capacity['generator type'] == gentype][['node_id','capacity (MW)']]
            if df.empty:
                continue
            if not os.path.exists(r2pd_dir):
                os.mkdir(r2pd_dir)
            df.to_csv(os.path.join(r2pd_dir,'generators.csv'),index=False)
            self.nodes.iloc[:,:3].to_csv(os.path.join(r2pd_dir,'nodes.csv'),index=False)
        return        


    def print_report(self):
        print(self.result_summary)


class Model(object):
    """
    Base class for optimization models that determine the new, by node and 
    generation type, generation mix for a given power system.
    """ 
    MODEL_FILE = None

    def __init__(self,request,outdir):
        self.request = request
        self.outdir = outdir

    def setup(self,gendists=None,precision=0): 
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)
        copyfile(os.path.join(models_dir,self.MODEL_FILE),os.path.join(self.outdir,self.MODEL_FILE))

        gendists_filename = gendists if gendists is not None else self.request.DEFAULT_GENTYPE_DISTANCE_FILE
        gendists_df = pds.read_csv(gendists_filename)
        gendists_df.columns = ['g','gg','Value']
        gendists_df = gendists_df[gendists_df.g.isin(self.request.gentypes) & gendists_df.gg.isin(self.request.gentypes)]

        desired_capacity_df = pds.DataFrame(self.request.summary['Desired Capacity (MW)'].apply(lambda x: round(x,precision)))
        desired_capacity_df = desired_capacity_df.reset_index()
        desired_capacity_df.columns = ['g','Value']

        return gendists_df, desired_capacity_df

    def run(self): pass

    def collect_results(self): pass


class GamsModel(Model):
    """
    Realization of Model using the GAMS AML. Depends on gdx-pandas, which is 
    a Python package available on github.com.
    """
    MODEL_FILE = 'match_generators.gms'

    def __init__(self,request,outdir):
        super().__init__(request,outdir)

    def setup(self,gendists=None,precision=0):
        gendists_df, desired_capacity_df = super().setup(gendists=gendists,precision=precision)

        from gdxpds.gdx import GdxFile, GdxSymbol, GamsDataType
        with GdxFile() as ingdx:
            # Sets
            ingdx.append(GdxSymbol('n',GamsDataType.Set,dims=['n']))
            df = pds.DataFrame(self.request.nodes['node_id'])
            df['Value'] = True
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g',GamsDataType.Set,dims=['g']))
            df = pds.DataFrame([[g, True] for g in self.request.gentypes],
                               columns=['g','Value'])
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g_indep',GamsDataType.Set,dims=['g']))
            df = pds.DataFrame([[g, True] for g in self.request.gentypes if g in self.request.RESOURCE_INDEPENDENT],
                               columns=['g','Value'])
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g_dep',GamsDataType.Set,dims=['g']))
            df = pds.DataFrame([[g, True] for g in self.request.gentypes if g not in self.request.RESOURCE_INDEPENDENT],
                               columns=['g','Value'])
            ingdx[-1].dataframe = df

            # Parameters
            ingdx.append(GdxSymbol('desired_capacity',GamsDataType.Parameter,dims=['g']))
            ingdx[-1].dataframe = desired_capacity_df

            ingdx.append(GdxSymbol('current_capacity',GamsDataType.Parameter,dims=['n','g']))
            # pivot with sum on capacity in case there are multiple units of type g at node n
            df = pds.pivot_table(self.request.generators,
                                 values='capacity (MW)',
                                 index=['node_id','generator type'],
                                 aggfunc=np.sum)
            df = df.reset_index()
            df.columns = ['n','g','Value']
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('g_dist',GamsDataType.Parameter,dims=['g','gg']))
            ingdx[-1].dataframe = gendists_df

            ingdx.append(GdxSymbol('current_indep_capacity',GamsDataType.Parameter,dims=['n']))
            df = pds.pivot_table(self.request.generators[self.request.generators['generator type'].isin(self.request.RESOURCE_INDEPENDENT)],
                                 values='capacity (MW)',
                                 index=['node_id'],
                                 aggfunc=np.sum)
            df = df.reset_index()
            df.columns = ['n','Value']
            ingdx[-1].dataframe = df

            ingdx.append(GdxSymbol('maximum_capacity',GamsDataType.Parameter,dims=['n','g_dep']))
            data = []
            for g in self.request.gentypes:
                if g in self.request.RESOURCE_INDEPENDENT:
                    continue
                if g in self.request.nodes:
                    tmp = pds.DataFrame(self.request.nodes['node_id'])
                    tmp['g_dep'] = g
                    tmp['Value'] = self.request.nodes[g]
                    data.append(tmp)
            df = pds.concat(data)
            df.columns = ['n','g_dep','Value']
            ingdx[-1].dataframe = df

            ingdx.write(os.path.join(self.outdir,'in.gdx'))

    def run(self):
        curdir = os.getcwd()
        os.chdir(self.outdir)
        call(['gams',self.MODEL_FILE])
        os.chdir(curdir)

    def collect_results(self):
        result_file = os.path.join(self.outdir,'MatchGenerationMix_p.gdx')
        if not os.path.exists(result_file):
            return False

        from gdxpds.gdx import GdxFile
        with GdxFile() as p_gdx:
            p_gdx.read(result_file)

            variables = [('Capacity',self.request.generators_columns()),
                         ('CapacityAdded',self.request.generators_columns()),
                         ('CapacityKept',self.request.generators_columns()),
                         ('CapacitySwapped',self.request.generators_swapped_columns()),
                         ('CapacityRemoved',self.request.generators_columns()),
                         ('Distance',['Level'])]

            capacity_column = self.request.generators_columns()[-1]

            args = []
            for variable_name, column_names in variables:
                p_gdx[variable_name].load()
                tmp = p_gdx[variable_name].dataframe.iloc[:,:(len(column_names))]
                tmp.columns = column_names
                # clear out 0 capacity entries
                if capacity_column in tmp.columns:
                    tmp = tmp[tmp[capacity_column] > 0.0]
                args.append(tmp)

            args[-1] = args[-1]['Level'].values[0]
            self.request.register_results(*args)

        return True
