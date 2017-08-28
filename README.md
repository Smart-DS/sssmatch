# genmatch

Apply NREL Standard Scenario generation mixes to arbitrary transmission systems.

## Use

genmatch was designed primarily for use on the command line. The command-line 
interface is accessible through `gm.py`. There are two primary commands:

    - browse
    - match

The `browse` functionality can be used to view the NREL Standard Scenarios data. 
The `match` functionality attempts to create a new generation mix for your 
transmission system based on a very high-level description of your system and 
the chosen standard scenario, standard scenario year, and geography.

The match functionality requires that you submit information on your system's 
nodes and current generation capacity. The intended use case is a system model 
that already exists and works under one specific configuration, for which there 
is a desire to explore a similar system served by a different mix of generator 
types. 
