
import os

__all__ = ['cli','request','sssdataset']

cli_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'bin','gm.py')
datasets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),'genmixes')
models_dir = os.path.join(os.path.dirname(__file__),'models')

class GenmatchError(Exception): pass
