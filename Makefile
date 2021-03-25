VERSION = $(shell grep 'version=' setup.py | cut -d'"' -f 2)
all: test mailprocessing-$(VERSION).tar.bz2

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

docs:
	(cd docs; make)

upload: all
	twine upload build/maildirproc-$(VERSION)-sdist/dist/maildirproc-$(VERSION).tar.bz2

clean:
	rm -rf maildirproc*-$(VERSION) build dist MANIFEST
	rm -rf *.gz
	find . -name '*~' | xargs rm -f

test: run-testsuite
	./run-testsuite

.PHONY: all clean docs test
