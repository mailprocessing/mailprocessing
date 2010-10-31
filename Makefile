VERSION = $(shell ./maildirproc --version)

all: maildirproc-$(VERSION).tar.gz maildirproc-python2-$(VERSION).tar.gz

DIST_FILES = \
    LICENSE \
    NEWS \
    README \
    doc

define build_dist_archive
	rm -rf $(1)-$(VERSION)
	mkdir $(1)-$(VERSION)
	cp -r $(DIST_FILES) $(1)-$(VERSION)
	cp $(1) $(1)-$(VERSION)/maildirproc
	cp $(2) $(1)-$(VERSION)/setup.py
	find $(1)-$(VERSION) -name '*~' | xargs -r rm -f
	tar czf $@ $(1)-$(VERSION)
	rm -rf $(1)-$(VERSION)
endef

maildirproc-$(VERSION).tar.gz: $(DIST_FILES) maildirproc setup.py
	$(call build_dist_archive, maildirproc, setup.py)

maildirproc-python2-$(VERSION).tar.gz: $(DIST_FILES) maildirproc-python2 setup-python2.py
	$(call build_dist_archive, maildirproc, setup.py)

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
    "Programming Language :: Python :: 3.2"/' \
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
    "Programming Language :: Python :: 2.7"/' \
	    -e 's/%MDP_NAME%/maildirproc-python2/g' \
	    -e 's/%MDP_VER%/$(VERSION)/g' \
	    $< >$@
	chmod +x $@

clean:
	rm -rf maildirproc*-$(VERSION) build dist MANIFEST *-python2*
	rm -rf *.gz setup.py
	find -name '*~' | xargs rm -f

.PHONY: all clean
