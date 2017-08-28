from distutils.core import setup

setup(
    name='genmatch',
    version='0.1.0',
    author='Elaine Hale',
    author_email='elaine.hale@nrel.gov',
    packages=['genmatch', 'sssparser'],
    scripts=['bin/gm.py'],
    package_data={'genmixes': ['genmixes/**/*.csv']
                  'genmatch.models': ['genmatch/models/*.csv',
                                      'genmatch/models/*.gms']},
    url='https://github.com/Smart-DS/genmatch',
    description='Apply NREL Standard Scenario generation mixes to arbitrary transmission systems.',
    install_requires=open('requirements.txt').read(),
)
