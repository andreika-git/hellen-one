#!/usr/bin/env python
############################################################################################
# Hellen-One: A manufacturer's BOM conversion script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

from collections import OrderedDict
import csv, os, sys, re

if len(sys.argv) < 3:
    print ("Error! Please specify input and output BOM file names.")
    sys.exit(1)
bomFileName = sys.argv[1]
mfrBomFileName = sys.argv[2]

print ("Converting from BOM file " + bomFileName + " to " + mfrBomFileName + "...")

with open(bomFileName, 'rt') as f, open (mfrBomFileName, 'wt') as new_f:
    reader = csv.reader(f, delimiter=',')
    rowIdx = 0
    for row in reader:
        pn = row[3].strip()
        # skip lines with empty P/N
        if not pn:
        	continue
        if rowIdx == 0:
            writer = csv.writer(new_f, quoting=csv.QUOTE_NONE, quotechar='"', escapechar='', delimiter=',', lineterminator='\n')
        elif rowIdx == 1:
            writer = csv.writer(new_f, quoting=csv.QUOTE_ALL, quotechar='"', escapechar='', delimiter=',', lineterminator='\n')
       	writer.writerow(row)
        rowIdx += 1

print ("Done!")
