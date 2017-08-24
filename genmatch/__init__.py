
import os

cli_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'bin','gm.py')
datasets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),'genmixes')

class GenmatchError(Exception): pass
