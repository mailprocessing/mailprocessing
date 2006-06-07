VERSION = $(shell ./maildirproc --version)

all: maildirproc-$(VERSION).tar.gz

DIST_FILES = \
    LICENSE \
    NEWS \
    README \
    maildirproc

EXAMPLE_FILES = \
    examples/sort-spam.rc \
    examples/complex.rc

maildirproc-$(VERSION).tar.gz: $(DIST_FILES) $(EXAMPLE_FILES)
	rm -rf maildirproc-$(VERSION)
	mkdir maildirproc-$(VERSION)
	cp $(DIST_FILES) maildirproc-$(VERSION)
	mkdir maildirproc-$(VERSION)/examples
	cp $(EXAMPLE_FILES) maildirproc-$(VERSION)/examples
	tar czf $@ maildirproc-$(VERSION)
	rm -rf maildirproc-$(VERSION)

clean:
	rm -rf maildirproc-$(VERSION) *.tar.gz
	find . -name '*~' | xargs rm -f

.PHONY: all clean
