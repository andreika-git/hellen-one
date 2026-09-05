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
    Comment, Designator, Footprint, LCSC Part #

    Command line:
    python "pathToFile/hellen-one-kicad-bom-plugin.py "%I" "%P/gerber/%B.csv"
"""

from __future__ import print_function

import csv
import sys
import os

# Locate kicad_netlist_reader.py shipped with KiCad (Linux .deb, macOS bundle, Windows installer).
# KICAD_PLUGINS_DIR can point to it explicitly; 'pip install kicad-netlist-reader' also works.
for plugins_dir in [
        os.environ.get("KICAD_PLUGINS_DIR", ""),
        "/usr/share/kicad/plugins",
        "/usr/local/share/kicad/plugins",
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/plugins",
        os.path.dirname(sys.executable) + "/scripting/plugins"]:
    if plugins_dir and os.path.isdir(plugins_dir) and plugins_dir not in sys.path:
        sys.path.append(plugins_dir)
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

components = net.getInterestingComponents(excludeBOM=True)

# Output a field delimited header line
writerow( out, ['Comment', 'Designator', 'Footprint', 'LCSC Part #'] )

# Output all of the component information (One component per row)
for c in components:
    lcsc = c.getField("LCSC")
    # Do-Not-Populate: either the legacy MyComment=DNP field or the native KiCad DNP attribute
    if (c.getField("MyComment") == "DNP" or (hasattr(c, "getDNP") and c.getDNP())):
        lcsc = ""
    writerow( out, [c.getValue(), c.getRef(), c.getFootprint(), lcsc])

