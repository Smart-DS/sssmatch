from distutils.core import setup
import glob

setup(
    name='genmatch',
    version='0.1.0',
    author='Elaine Hale',
    author_email='elaine.hale@nrel.gov',
    packages=['genmatch', 'sssparser'],
    package_data={'genmatch': ['models/*.csv',
                               'models/*.gms']},
    data_files=[('genmixes',glob.glob('genmixes/**/*.csv') + glob.glob('genmixes/**/**/*.csv'))],
    scripts=['bin/gm.py'],
    url='https://github.com/Smart-DS/genmatch',
    description='Apply NREL Standard Scenario generation mixes to arbitrary transmission systems.',
    install_requires=open('requirements.txt').read(),
)
