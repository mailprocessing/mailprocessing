#!/usr/bin/env python3

"""
Pandoc filter for stripping links down to just their titles.
"""

from pandocfilters import toJSONFilter

def striplinks(key, value, format, meta):
  if key == 'Link':
      return(value[1])

if __name__ == "__main__":
  toJSONFilter(striplinks)
