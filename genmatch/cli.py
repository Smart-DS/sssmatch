import argparse

def cli_parser():
    parser = argparse.ArgumentParser(description='''Place generators by type on 
        an arbitrary transmission system to match NREL Standard Scenarios data 
        specified by scenario and year.''')

    # CLI modes
    #     - view Standard Scenario data
    #     - review match request
    #     - perform match

    return parser

def cli_main():
    parser = cli_parser()
    args = parser.parse_args()

    # Load the NREL standard scenarios data


    # Load the transmission system description
    #     - nodes: location, peak load, generator type exclusions
    #     - lines, including capacity


    # Determine capacity mix


    # Place capacity based on system constraints


    # Write out the match, including input arguments for R2PD
    
