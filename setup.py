from distutils.core import setup
import glob

data_install_dir = 'Lib/site-packages/'
dataset_dirs = glob.glob('genmixes/**')
data_files = []
for dataset_dir in dataset_dirs:
    data_files.append((data_install_dir + dataset_dir,glob.glob(dataset_dir + '/*.csv')))
    for subdir in glob.glob(dataset_dir + '/**'):
        data_files.append((data_install_dir + subdir,glob.glob(subdir + '/*.csv')))

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
