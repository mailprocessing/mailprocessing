VERSION = $(shell ./maildirproc --version)

all: maildirproc-$(VERSION).tar.gz

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
	tar czf $@ maildirproc-$(VERSION)
	rm -rf maildirproc-$(VERSION)

clean:
	rm -rf maildirproc-$(VERSION)
	find . -name '*~' | xargs rm -f

.PHONY: all clean
