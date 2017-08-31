from distutils.core import setup
import glob
import os

data_files = []
data_install_dir = os.path.join('Lib','site-packages')
for dirpath, dirnames, filenames in os.walk('genmixes'):
    for filename in filenames:
        data_files.append((os.path.join(data_install_dir,dirpath),os.path.join(dirpath,filename)))
print(data_files)

setup(
    name='genmatch',
    version='0.1.0',
    author='Elaine Hale',
    author_email='elaine.hale@nrel.gov',
    packages=['genmatch', 'sssparser'],
    package_data={'genmatch': ['models/*.csv',
                               'models/*.gms']},
    data_files=data_files,
    scripts=['bin/gm.py'],
    url='https://github.com/Smart-DS/genmatch',
    description='Apply NREL Standard Scenario generation mixes to arbitrary transmission systems.',
    install_requires=open('requirements.txt').read(),
)
