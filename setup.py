#!/usr/bin/env python

# This will effectively place satchmo files but there needs to
# be extra work before this would work correctly

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
import os, os.path
import sys

DIRNAME = os.path.dirname(__file__)
APPDIR = os.path.join(DIRNAME, 'satchmo/apps')
if not APPDIR in sys.path:
    sys.path.append(APPDIR)

# Dynamically calculate the version based on django.VERSION.
version = __import__('satchmo_store').__version__
packages = find_packages('satchmo/apps')
packages.append('static')
template_dirs = []
for root, dirs, files in os.walk(APPDIR):
    if root.endswith('templates'):
        template_dirs.append(os.path.join(root,"*.*"))

print template_dirs
print packages
setup(name = "Satchmo",
      version = version,
      author = "Chris Moffitt",
      author_email = "chris@moffitts.net",
      url = "http://www.satchmoproject.com",
      license = "BSD",
      description = "The webshop for perfectionists with deadlines.",
      long_description = "Satchmo is an ecommerce framework created using Django.",
      include_package_data = True,
      zip_safe = False,
      package_dir = {
      '' : 'satchmo/apps',
      'static' : 'satchmo/static'
      },
      package_data = { '': template_dirs },
      packages = packages,
      classifiers = [
      'Development Status :: 4 - Beta',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent', 
      'Topic :: Office/Business',
      ]
)
