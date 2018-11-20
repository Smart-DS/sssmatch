# Developer How-To

To get all of the development dependencies for Python:

```
pip install -r gdx-pandas/dev/requirements.txt
```

Also, you will need to install

- [pandoc](https://pandoc.org/installing.html)

## Create a new release

1. Update version number, CHANGES.txt, setup.py, LICENSE and header as needed
2. Run [demo notebook](https://github.com/Smart-DS/demos/blob/master/demo_sssmatch_applied_to_rts_gmlc.ipynb) and fix any issues
3. Install from github and make sure demo notebook runs
4. Uninstall the draft package
5. Publish documentation
6. Create release on github
7. Release tagged version on pypi
   

