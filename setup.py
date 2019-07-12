#! /usr/bin/env python3
# -*-python-*-

from setuptools import setup, find_packages
from mailprocessing.version import PKG_VERSION

setup(
    name="mailprocessing",
    version=PKG_VERSION,
    author="Joel Rosdahl",
    author_email="joel@rosdahl.net",
    maintainer="Johannes Grassler",
    maintainer_email="johannes@btw23.de",
    license="GNU GPL 2.0",
    entry_points={
      'console_scripts': [
        'maildirproc=mailprocessing.cmd.maildir:main',
        'imapproc=mailprocessing.cmd.imap:main'
        ]
    },
    packages=find_packages(),
    platforms="platform-independent",
    url="http://mailprocessing.github.io/mailprocessing",
    description="maildir and IMAP processor/filter using Python 3.x as its configuration language",
    long_description="""The mailprocessing library contains two executables:
maildirproc and imapproc. maildirproc processes one or several \
several existing mail boxes in the maildir format. It is primarily \
focused on mail sorting -- i.e., moving, copying, forwarding and \
deleting mail according to a set of rules. It can be seen as an \
alternative to procmail, but instead of being a delivery agent \
(which wants to be part of the delivery chain), maildirproc only \
processes already delivered mail. And that's a feature, not a \
bug. imapproc does the same thing for IMAP folders.""",
    classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Environment :: No Input/Output (Daemon)",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: Unix",
    "Programming Language :: Python",

    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Topic :: Communications :: Email",
    "Topic :: Communications :: Email :: Filters",
    ],
    )
