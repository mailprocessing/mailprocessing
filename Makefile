VERSION = $(shell grep 'version=' setup.py.template | cut -d'"' -f 2)
all: mailprocessing-$(VERSION).tar.bz2

DIST_FILES = \
    LICENSE \
    MANIFEST.in \
    NEWS \
    README \
    docs

define build_dist_archive
	rm -rf build/
	./setup.py sdist
endef

mailprocessing-$(VERSION).tar.bz2: $(DIST_FILES) mailprocessing setup.py
	$(call build_dist_archive,mailprocessing,setup.py)

setup.py: setup.py.template
	sed -e 's/%PY_BIN%/python3/g' \
	    -e 's/%PY_VER%/3.x/g' \
	    -e 's/%CLASSIFIERS%/\
    "Programming Language :: Python :: 3",\
    "Programming Language :: Python :: 3.0",\
    "Programming Language :: Python :: 3.1",\
    "Programming Language :: Python :: 3.2",\
    "Programming Language :: Python :: 3.3",\
    "Programming Language :: Python :: 3.4",\
    "Programming Language :: Python :: 3.5",\
    "Programming Language :: Python :: 3.6",/' \
	    -e 's/%MDP_NAME%/mailprocessing/g' \
	    $< >$@
	chmod +x $@

upload: all
	twine upload build/maildirproc-$(VERSION)-sdist/dist/maildirproc-$(VERSION).tar.bz2

clean:
	rm -rf maildirproc*-$(VERSION) build dist MANIFEST
	rm -rf *.gz setup.py
	find -name '*~' | xargs rm -f

.PHONY: all clean
