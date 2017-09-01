from distutils.core import setup
import glob
import os

data_files = []
data_install_dir = os.path.join('Lib','site-packages')
curdir = None
for dirpath, dirnames, filenames in os.walk('sssmixes'):
    for filename in filenames:
        if curdir is None or dirpath != curdir:
            data_files.append((os.path.join(data_install_dir,dirpath),[]))
            curdir = dirpath
        data_files[-1][1].append(os.path.join(dirpath,filename))

setup(
    name='sssmatch',
    version='0.2.0',
    author='Elaine Hale',
    author_email='elaine.hale@nrel.gov',
    packages=['sssmatch', 'sssparser'],
    package_data={'sssmatch': ['models/*.csv',
                               'models/*.gms']},
    data_files=data_files,
    scripts=['bin/sssm.py'],
    url='https://github.com/Smart-DS/sssmatch',
    description='Apply NREL Standard Scenario generation mixes to arbitrary transmission systems.'
)
