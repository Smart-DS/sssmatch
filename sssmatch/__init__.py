
import os
import sys

cli_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'bin','sssm.py')
if not os.path.exists(cli_path):
    cli_path = os.path.join(sys.prefix,'Scripts','sssm.py')
datasets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),'sssmixes')
models_dir = os.path.join(os.path.dirname(__file__),'models')

class SSSMatchError(Exception): pass
