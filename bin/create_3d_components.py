#!/usr/bin/env python
############################################################################################
# Hellen-One: A script to create a 3D components view (VRML).
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys, re
import configparser
import gzip

### Unfortunately PyVRML97 (vrml.vrml97) is not capable of properly processing Altium-exported VRML-files...

if len(sys.argv) < 3:
    print "Error! Please specify the place+board files and vrml filename."
    sys.exit(1)
mergePlaceFile = sys.argv[1]
mergeBoardFile = sys.argv[2]
fileOutName = sys.argv[3]

# read board config
config = configparser.ConfigParser()
config.read(mergeBoardFile)

# read place file
fragments = []
with open(mergePlaceFile, 'rb') as fmp:
	for line in fmp:
		m = line.split()
		name_and_rot = m[0].split('*rotated') # split the name and rotation parts
		name = name_and_rot[0]
		rot = name_and_rot[1] if len(name_and_rot) > 1 else "0"
		m = {"name": name, "x": m[1], "y": m[2], "rot": rot, "path": config[name]["Prefix"] }
		fragments.append(m)

print "* Starting merge of " + str(len(fragments)) + " board fragments..."

outf = gzip.open(fileOutName, 'wb')
outf.write("#VRML V2.0 utf8\n")

pat_hdr = re.compile('^#VRML.*')
pat_idx = re.compile(r'(DEF|USE)\s+(Shape|_)(\w)')
pat_trans = re.compile(r'(translation)\s+([+\-0-9\.]+)\s+([+\-0-9\.]+)')

def trans_repl(m):
	x = float(m.group(2))
	y = float(m.group(3))
	return m.group(1) + " " + str(x + off_x_mm) + " " + str(y + off_y_mm)

fId = 1
for frag in fragments:
	# convert to mm
	off_x_mm = float(frag["x"]) * 25.4
	off_y_mm = float(frag["y"]) * 25.4
	# todo: apply module rotations
	rot = float(frag["rot"])
	fileName = frag["path"] + "-vrml.wrl"
	print "* Adding " + frag["name"] + " (" + fileName + ") at (" + str(off_x_mm) + "," + str(off_y_mm) + "), rot=" + str(rot) + "..."
	with open(fileName, 'rb') as f:
		for line in f:
			line = line.rstrip()
			# skip the headers (we write our own because there should be only 1 header)
			if pat_hdr.match(line):
				continue
			fragId = str(fId).zfill(2)
			line = pat_idx.sub(r'\g<1> \g<2>' + fragId + '\g<3>', line)
			line = pat_trans.sub(trans_repl, line)
			outf.write(line + "\n")
		f.close()
	fId = fId + 1

outf.close()

print "Done!"
