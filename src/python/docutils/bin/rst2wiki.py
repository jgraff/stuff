#!/usr/bin/python

# Author: Joshua Graff
# Contact: jgraff@ccrypt.org
# Copyright: This module has been placed in the public domain.

import locale
try:
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description
from docutils.writers import wiki

description = ("Generates Wiki documents.  " + default_description)

publish_cmdline(writer=wiki.Writer(), description=description)
