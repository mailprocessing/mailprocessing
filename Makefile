VERSION = $(shell ./maildirproc --version)

all: maildirproc-$(VERSION).tar.gz maildirproc-python3

DIST_FILES = \
    LICENSE \
    NEWS \
    README \
    maildirproc \
    doc

maildirproc-$(VERSION).tar.gz: $(DIST_FILES) $(EXAMPLE_FILES)
	rm -rf maildirproc-$(VERSION)
	mkdir maildirproc-$(VERSION)
	cp -r $(DIST_FILES) maildirproc-$(VERSION)
	find maildirproc-$(VERSION) -name .svn | xargs rm -rf
	find . -name '*~' | xargs rm -f
	tar czf $@ maildirproc-$(VERSION)
	rm -rf maildirproc-$(VERSION)

maildirproc-python3: maildirproc
	cp maildirproc $@.tmp
	2to3 --no-diffs -n -w $@.tmp
	sed -i '1s/python/python3/' $@.tmp
	mv $@.tmp $@

clean:
	rm -rf maildirproc-$(VERSION) build dist MANIFEST maildirproc-python3
	find . -name '*~' | xargs rm -f

.PHONY: all clean
