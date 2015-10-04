VERSION = $(shell ./maildirproc --version)

all: maildirproc-$(VERSION).tar.bz2 maildirproc-python2-$(VERSION).tar.bz2

DIST_FILES = \
    LICENSE \
    MANIFEST.in \
    NEWS \
    README \
    doc

define build_dist_archive
	rm -rf build/$(1)-$(VERSION)-sdist
	mkdir -p build/$(1)-$(VERSION)-sdist
	cp -r $(DIST_FILES) build/$(1)-$(VERSION)-sdist
	cp $(1) build/$(1)-$(VERSION)-sdist/maildirproc
	cp $(2) build/$(1)-$(VERSION)-sdist/setup.py
	find build/$(1)-$(VERSION)-sdist -name '*~' | xargs -r rm -f
	cd build/$(1)-$(VERSION)-sdist && ./setup.py sdist --formats=bztar
	cp build/$(1)-$(VERSION)-sdist/dist/$(1)-$(VERSION).tar.bz2 .
endef

maildirproc-$(VERSION).tar.bz2: $(DIST_FILES) maildirproc setup.py
	$(call build_dist_archive,maildirproc,setup.py)

maildirproc-python2-$(VERSION).tar.bz2: \
		$(DIST_FILES) maildirproc-python2 setup-python2.py
	$(call build_dist_archive,maildirproc-python2,setup-python2.py)

maildirproc-python2: maildirproc
	cp maildirproc $@.tmp
	3to2 --no-diffs -n -w $@.tmp
	sed -i '1s/python3/python/' $@.tmp
	mv $@.tmp $@

setup.py: setup.py.template
	sed -e 's/%PY_BIN%/python3/g' \
	    -e 's/%PY_VER%/3.x/g' \
	    -e 's/%CLASSIFIERS%/\
    "Programming Language :: Python :: 3",\
    "Programming Language :: Python :: 3.0",\
    "Programming Language :: Python :: 3.1",\
    "Programming Language :: Python :: 3.2",\
    "Programming Language :: Python :: 3.3",\
    "Programming Language :: Python :: 3.4",/' \
	    -e 's/%MDP_NAME%/maildirproc/g' \
	    -e 's/%MDP_VER%/$(VERSION)/g' \
	    $< >$@
	chmod +x $@

setup-python2.py: setup.py.template
	sed -e 's/%PY_BIN%/python/g' \
	    -e 's/%PY_VER%/2.x/g' \
	    -e 's/%CLASSIFIERS%/\
    "Programming Language :: Python :: 2",\
    "Programming Language :: Python :: 2.6",\
    "Programming Language :: Python :: 2.7",/' \
	    -e 's/%MDP_NAME%/maildirproc-python2/g' \
	    -e 's/%MDP_VER%/$(VERSION)/g' \
	    $< >$@
	chmod +x $@

upload: all
	twine upload build/maildirproc-$(VERSION)-sdist/dist/maildirproc-$(VERSION).tar.bz2
	twine upload build/maildirproc-python2-$(VERSION)-sdist/dist/maildirproc-python2-$(VERSION).tar.bz2

clean:
	rm -rf maildirproc*-$(VERSION) build dist MANIFEST *-python2*
	rm -rf *.gz setup.py
	find -name '*~' | xargs rm -f

.PHONY: all clean
