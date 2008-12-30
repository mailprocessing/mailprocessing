#! /usr/bin/env python

from distutils.core import setup

try:
    from distutils.command.build_scripts import build_scripts_2to3 as build_scripts
except ImportError:
    from distutils.command.build_scripts import build_scripts

VERSION = "0.4"

setup(
    name="maildirproc",
    version=VERSION,
    author="Joel Rosdahl",
    author_email="joel@rosdahl.net",
    license="GNU GPL",
    scripts=["maildirproc"],
    platforms="platform-independent",
    cmdclass={"build_scripts": build_scripts},
    url="http://joel.rosdahl.net/maildirproc/",
    download_url=("http://joel.rosdahl.net/maildirproc/maildirproc-%s.tar.gz" %
                  VERSION),
    description="maildir processor using Python as its configuration language",
    long_description="""maildirproc is a program that processes one or
    several existing mail boxes in the maildir format. It is primarily
    focused on mail sorting -- i.e., moving, copying, forwarding and
    deleting mail according to a set of rules. It can be seen as an
    alternative to procmail, but instead of being a delivery agent
    (which wants to be part of the delivery chain), maildirproc only
    processes already delivered mail. And that's a feature, not a
    bug.""",
    classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Environment :: No Input/Output (Daemon)",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: Unix",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.4",
    "Programming Language :: Python :: 2.5",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Topic :: Communications :: Email",
    "Topic :: Communications :: Email :: Filters",
    ],
    )
