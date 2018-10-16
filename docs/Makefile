.PHONY: all clean html man

# Saner quoting rules for M4
CQ=echo 'changequote(,)' | cat -
PANDOC_MAN=pandoc -s -f rst -t man --filter pandoc/delink.py
PANDOC_HTML=pandoc -s -f rst -t html --css mailprocessing.css

# Generate manual page title from file name
man_title = $(shell basename $1 | sed 's/\..*//' | tr '[:lower:]' '[:upper:]')

all: man html

html: reference.html index.html

man: imapproc.1 maildirproc.1 mailprocessing.5

%.1: %.1.rst reference/*.rst
	$(CQ) $< | m4 | $(PANDOC_MAN) -o $@ \
	  -V section=1\
		-V title=$(call man_title, $<) \
		-V header="User Commands" \
		-V footer="User Commands"

%.5: %.5.rst reference/*.rst
	$(CQ) $< | m4 | $(PANDOC_MAN) -o $@ \
	  -V section=1\
		-V title=$(call man_title, $<) \
		-V header="User Commands" \
		-V footer="User Commands"

%.html: %.rst reference/*.rst
	$(CQ) $< | m4 | $(PANDOC_HTML) -o $@ -V section=1

clean:
	rm -f *.1 *.5 *.html
