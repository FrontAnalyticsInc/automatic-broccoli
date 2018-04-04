
# flake8: noqa

import sys

# check for missing dependencies and Python version
hard_dependencies = ["scipy", "numpy", "pandas", "pandas_profiling"]
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append(dependency)

if missing_dependencies:
    raise ImportError(
        f"Missing required dependencies {missing_dependencies}"
    )
del hard_dependencies, dependency, missing_dependencies

PY3 = float(sys.version[0:3]) >= 3.6
if not PY3:
    raise EnvironmentError("Python version 3.6 or greater is needed")

# load needed functionality
from auto_broccoli.auto_broccoli import AutoBroccoli
from auto_broccoli.database import DBInterface
from auto_broccoli.utils import *


# module level doc-string
__doc__ = """
Automatic Broccoli - going beyond manual EDA
=====================================================================
**Automatic Broccoli ** builds on the strengths of tools like Pandas 
and Pandas Profiling to identify not only the type of column, but its 
analytical possibilities, especially in relation to the other columns present.
  

Main Features
-------------
Here are a few things it can currently do:
  - Identification of analytical types of columns.
  - Creation of fake /customizable datasets for testing
  - Outputs insights to CSV or to a database table
  - Runs a series of statisical tests and allows you to filter out findings that aren't 
    statistically significant at a significance threshold you select.
"""