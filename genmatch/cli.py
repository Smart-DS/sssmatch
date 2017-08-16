import argparse

from genmatch import datasets_dir

DEFAULT_DATASET = 'NREL Standard Scenarios 2016'
DEFAULT_SCENARIO = 'Central Scenario'
DEFAULT_GEOGRAPHY = 'National'

def cli_parser():
    parser = argparse.ArgumentParser(description='''Place generators by type on 
        an arbitrary transmission system to match NREL Standard Scenarios data 
        specified by scenario and year.''')

    def add_dataset_argument(parser):
        parser.add_argument('-ds','--dataset',help="""Dataset from 
            which to pull scenarios.""",default=DEFAULT_DATASET)

    def add_genmix_arguments(parser):
        parser.add_argument('scenario_year',type=int,help="""Model year on which 
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
    add_genmix_arguments(list_generator_mixes_parser)
    # Browse mode - where to save information as csv
    browse_parser.add_argument('-f','--filename',help='''Where to save listed 
        information. Default is to print to screen only.''')

    # Match mode - standard scenarios
    add_genmix_arguments(match_parser)

    # Match mode - existing system

    # Match mode - outputs
    match_parser.add_argument('-o','--outdir',default='.',help='''Where to write
        out match information.''')

    return parser

def cli_main():
    parser = cli_parser()
    args = parser.parse_args()

    # List all available or determine which generation mix dataset is to be 
    # viewed or used
    if args.cmd == 'browse' and args.what == 'datasets':
        for filepath, dirs, files in os.walk(datasets_dir):
            for dirname in dirs:
                print("  " + dirname)
            break
        return
    dataset_dir = os.path.join(datasets_dir,args.dataset)
    if not os.path.exists(dataset_dir):
        raise GenmatchError('No dataset exists in {}. Call genmatch browse datasets to see available datasets.'.format(dataset_dir))

    # Load the chosen generation mix dataset
    

    # Load the transmission system description
    #     - nodes: location, peak load, annual load, max allowed capacity of each RE type
    #     - existing generators: node, type, and capacity
    #     - lines, including capacity


    # Determine capacity mix based on comparing load and capacity by type
    # across user system and multiple standard scenarios


    # Place capacity based on system constraints, with preference for
    # making the smallest possible change as compared to original system


    # Write out the match, including input arguments for R2PD
    
