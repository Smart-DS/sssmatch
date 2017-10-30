# sssmatch

Apply NREL Standard Scenario generation mixes to arbitrary transmission systems.

[Install](#install) | [Use](#use) | [Uninstall](#uninstall)


## Use

sssmatch was designed primarily for use on the command line. The command-line 
interface is accessible through `sssm.py`. There are two primary commands:

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

Once `sssmatch` is installed, the CLI can be accessed with `sssm.py` or 
`python /your/path/to/PythonXX/Scripts/sssm.py`, and has a fully documented help 
menu. For a more detailed example, please see 
[demo_sssmatch_applied_to_rts_gmlc.ipynb](https://github.com/Smart-DS/demos/blob/master/demo_sssmatch_applied_to_rts_gmlc.ipynb).


## Install

```
pip install git+https://github.com/Smart-DS/sssmatch.git@master
```

or

```
pip install git+https://github.com/Smart-DS/sssmatch.git@v0.4.0
```


## Uninstall

```
pip uninstall sssmatch
```
