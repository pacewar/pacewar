# setup.py
# Copyright (C) 2014-2016 onpon4 <onpon4@riseup.net>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [],
                    include_files = ["data", "COPYING", "credits.txt",
                                     "pacewar.py", "README.txt", "setup.py"])

if os.name == "nt":
    base = "Win32GUI"
else:
    base = "Console"

executables = [
    Executable("pacewar.py", base=base, compress=True, icon="icon.ico")
]

setup(name = "Pacewar",
      version = "1.6.4",
      description = "A fighting game with lots of ships",
      author = "onpon4",
      author_email = "onpon4@riseup.net",
      classifiers = ["Development Status :: 6 - Mature",
                     "License :: DFSG approved",
                     "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
                     "Natural Language :: English",
                     "Operating System :: OS Independent",
                     "Programming Language :: Python :: 2",
                     "Programming Language :: Python :: 3",
                     "Topic :: Games/Entertainment :: Arcade"],
      license = "GNU General Public License",
      options = dict(build_exe = buildOptions),
      executables = executables)
