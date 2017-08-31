import argparse
import logging
import os

import pandas as pds

from sssmatch import datasets_dir, SSSMatchError
from sssparser.ScenariosDataset import ScenariosDataset
from .request import Request, AML

logger = logging.getLogger(__name__)

DEFAULT_DATASET = 'NREL Standard Scenarios 2016'
DEFAULT_SCENARIO = 'Central Scenario'
DEFAULT_GEOGRAPHY = 'national'

def cli_parser():
    parser = argparse.ArgumentParser(description='''Place generators by type on 
        an arbitrary transmission system to match NREL Standard Scenarios data 
        specified by scenario and year.''')

    def add_dataset_argument(parser):
        parser.add_argument('-ds','--dataset',help="""Dataset from 
            which to pull scenarios.""",default=DEFAULT_DATASET)

    def add_genmix_arguments(parser):
        parser.add_argument('scenario_year',help="""Model year on which 
            to base new generation mix.""")
        parser.add_argument('-s','--scenario',help="""Scenario on which to base 
            the new generation mix""",default=DEFAULT_SCENARIO)
        parser.add_argument('-g','--geography',help="""Geography from which to 
            pull generation mix data. If multiple geographies are listed, the 
            union will be taken.""",nargs='+',default=DEFAULT_GEOGRAPHY)
        add_dataset_argument(parser)

    # Define CLI modes
    subparsers = parser.add_subparsers(dest='cmd')
    browse_parser = subparsers.add_parser('browse',help='''Browse NREL Standard 
        Scenarios data.''')
    match_parser = subparsers.add_parser('match',help='''Create and place 
        generation mix for your transmission system based on NREL Standard 
        Scenarios data.''')

    # Define CLI arguments per mode
    # Browse mode - items that can be listed
    browse_subparsers = browse_parser.add_subparsers(dest='what')
    # datasets
    list_datasets_parser = browse_subparsers.add_parser('datasets',
        help='''List available datasets.''')
    # generator types
    list_generator_types_parser = browse_subparsers.add_parser('gentypes',
        help='''List generator types present in the selected dataset.''')
    add_dataset_argument(list_generator_types_parser)
    # years (scenario/model years)
    list_years_parser = browse_subparsers.add_parser('years',
        help='''List scenario years associated with generation mixes.''')
    add_dataset_argument(list_years_parser)
    # scenarios
    list_scenarios_parser = browse_subparsers.add_parser('scenarios',
        help='''List available scenarios in chosen dataset.''')
    add_dataset_argument(list_scenarios_parser)
    # geographies
    list_geographies_parser = browse_subparsers.add_parser('geographies',
        help='''List available geographies in chosen dataset.''')
    add_dataset_argument(list_geographies_parser)
    # generator mixes
    list_generator_mixes_parser = browse_subparsers.add_parser('mixes',
        help='''List a particular generator mix represented in the chosen dataset.''')
    add_genmix_arguments(list_generator_mixes_parser)
    # Browse mode - where to save information as csv
    browse_parser.add_argument('-f','--filename',help='''Where to save listed 
        information in csv format. Default is to print to screen only.''')

    # Match mode - standard scenarios
    add_genmix_arguments(match_parser)

    # Match mode - existing system
    match_parser.add_argument('nodes',help='''Path to csv file describing nodes, 
        or list of tuples describing nodes. Each tuple or each row of the csv file
        should contain (node_id, latitude, longitude, peak load (MW), 
        annual load (GWh), max allowed capacity of each RE type (MW))''')
    match_parser.add_argument('-rt','--re_types',help='''RE types in order they 
        appear in the nodes tuples/csv. RE types must be a subset of the selected 
        dataset's generator types. This only needs to be specified if specifying 
        tuples or csv column names do not match generator types.''',nargs='*')
    match_parser.add_argument('generators',help='''Path to csv file describing 
        existing generators, or list of tuples describing generators. Each tuple 
        or each row of the csv file should contain (node_id, generator type, 
        capacity (MW)). Generator type must match the dataset's generator 
        types.''')
    match_parser.add_argument('-eg','--excluded_gentypes',nargs='*',help='''List 
        of generator types that should not be included in the match results. RE 
        types with no existing unit and no allowed capacity will also be 
        excluded.''') 

    # Match mode - outputs
    match_parser.add_argument('-o','--outdir',default='.',help='''Where to write
        out match information.''')
    match_parser.add_argument('-gd','--gendists',help='''Path to csv file 
        containing rows with (gentype_to, gentype_from, distance). Distances are 
        generally between 0 and 1. A distance of 0 means switching capacity from 
        gentype_to to gentype_from is equivalent to keeping the original 
        generator. A distance of 1 means that such a switch is no better than 
        removing old capacity and placing new capacity with no regard to where 
        the previous generators were. Default is to use default_gendists.csv.''')
    match_parser.add_argument('-p','--precision',type=int,help='''The precision 
        to which the desired capacity is to be matched, in MW. Thus 0 
        corresponds to rounding to the nearest MW, 1 corresponds to the nearest
        100 kW, and 3 is the nearest kW.''',default=0)
    match_parser.add_argument('-a','--aml',type=AML,choices=[val.name for val in AML],
        help='''Algebraic modeling language to use to solve the matching problem.''',
        default=AML.GAMS)

    parser.add_argument('-d','--debug',action='store_true',default=False,
        help="Option to output debug information.")

    return parser

def cli_main():
    parser = cli_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    fmt = '%(asctime)s|%(levelname)s|%(name)s|\n    %(message)s'
    logging.basicConfig(format=fmt,level=log_level) # to console

    def display_browse_info(result,filename):
        if filename is None:
            if isinstance(result,pds.Series):
                for i, value in result.iteritems():
                    print("  " + str(value))
                return
            print(result)
            return
        result.to_csv(filename,index=False,header=True)
        return

    # List all available or determine which generation mix dataset is to be 
    # viewed or used
    if args.cmd == 'browse' and args.what == 'datasets':
        result = []
        for filepath, dirs, files in os.walk(datasets_dir):
            for dirname in dirs:
                result.append(dirname)
            break
        result = pds.Series(result,name="Datasets")
        display_browse_info(result,args.filename)
        return

    dataset_dir = os.path.join(datasets_dir,args.dataset)
    if not os.path.exists(dataset_dir):
        raise SSSMatchError('No dataset exists in {}. Call sssmatch browse datasets to see available datasets.'.format(dataset_dir))

    # Load the chosen generation mix dataset
    dataset = ScenariosDataset(dataset_dir)

    if args.cmd == 'browse':
        # Display dataset information as requested
        result = None
        if args.what == 'gentypes':
            result = pds.Series(dataset.gentypes,name='Generator Type') 
        elif args.what == 'years': 
            result = pds.Series(dataset.years,name='Years')
        elif args.what == 'scenarios': 
            result = pds.Series(dataset.scenarios,name="Scenarios")
        elif args.what == 'geographies': 
            result = pds.Series(dataset.geographies,name="Geographies")
        else:
            assert args.what == 'mixes'
            result = dataset.get_genmix(args.scenario_year,args.scenario,args.geography)

        display_browse_info(result,args.filename)
        return

    assert args.cmd == 'match'

    def load_dataframe(arg):
        if isinstance(arg,str):
            return pds.read_csv(arg)
        return pds.DataFrame(arg)

    # Load the transmission system description
    #     - nodes: node_id, latitude, longitude, peak load (MW), annual load (GWh), max allowed capacity of each RE type (MW)
    nodes = load_dataframe(args.nodes)
    re_types = args.re_types if args.re_types else list(nodes.columns[5:])
    nodes.columns = Request.nodes_columns(re_types)

    #     - existing generators: node, type, and capacity
    generators = load_dataframe(args.generators)
    generators.columns = Request.generators_columns()
    
    # Create the request
    request = Request(nodes,
                      generators,
                      dataset,
                      dataset.get_genmix(args.scenario_year,args.scenario,args.geography),
                      exclusions=args.excluded_gentypes)

    # Place capacity based on system constraints, with preference for
    # making the smallest possible change as compared to original system
    request.preprocess()
    # TODO: Provide mode to let users drop_default_gendists
    # request.drop_default_gendists()
    request.fulfill(args.outdir,
                    gendists=args.gendists,
                    precision=args.precision,
                    aml=args.aml)

    # Write out the match, including input arguments for R2PD
    request.print_report()
    