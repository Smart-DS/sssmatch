# sssmatch

[![PyPI](https://img.shields.io/pypi/v/sssmatch.svg)](https://pypi.python.org/pypi/sssmatch/)
[![Documentation](https://img.shields.io/badge/docs-ready-blue.svg)](http://smart-ds.github.io/sssmatch)

Apply [NREL Standard Scenario](https://www.nrel.gov/analysis/data-tech-baseline.html) 
generation mixes to arbitrary transmission systems.

[Install](#install) | [Documentation](http://smart-ds.github.io/sssmatch) | [Uninstall](#uninstall)

## Install

```
pip install sssmatch
```

or

```
pip install git+https://github.com/Smart-DS/sssmatch.git@master
```

or

```
pip install git+https://github.com/Smart-DS/sssmatch.git@v0.5.0
```

Running the match functionality requires solving an optimization model. 
Currently the model is only implemented in [GAMS](https://www.gams.com/), and 
the model input/output is handled with [gdx-pandas](https://github.com/NREL/gdx-pandas), 
so these are additional dependencies to access full functionality. If you would
like to use the tool, but need support for a different algebraic modeling 
language (AML), please open an issue.

## Uninstall

```
pip uninstall sssmatch
```
