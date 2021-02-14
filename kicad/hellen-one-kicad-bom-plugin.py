#!/usr/bin/env python
############################################################################################
# Hellen-One: A python script to generate a Hellen-One BOM for a frame from a KiCad generic netlist.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

"""
    @package
    Generate a csv list file.
    Components are sorted by ref
    One component per line
    Fields are (if exist)
    Ref, value, Part, footprint, Datasheet, Manufacturer, Vendor

    Command line:
    python "pathToFile/bom_csv_sorted_by_ref.py" "%I" "%O.csv"
"""

from __future__ import print_function

import csv
import sys
import os

# [andreika]: add kicad plugins path
sys.path.append(os.path.dirname(sys.executable) + "/scripting/plugins")
# Import the KiCad python helper module
import kicad_netlist_reader


# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
net = kicad_netlist_reader.netlist(sys.argv[1])

# Open a file to write to, if the file cannot be opened output to stdout
# instead
try:
    f = open(sys.argv[2], 'w')
except IOError:
    e = "Can't open output file for writing: " + sys.argv[2]
    print( __file__, ":", e, sys.stderr )
    f = sys.stdout

# Create a new csv writer object to use as the output formatter
out = csv.writer(f, lineterminator='\n', delimiter=',', quotechar="\"", quoting=csv.QUOTE_ALL)

# override csv.writer's writerow() to support utf8 encoding:
def writerow( acsvwriter, columns ):
    utf8row = []
    for col in columns:
        utf8row.append( str(col) )
    acsvwriter.writerow( utf8row )

components = net.getInterestingComponents()

# Output a field delimited header line
writerow( out, ['Comment', 'Designator', 'Footprint', 'LCSC Part #'] )

# Output all of the component information (One component per row)
for c in components:
    writerow( out, [c.getValue(), c.getRef(), c.getFootprint(), c.getField("LCSC")])

