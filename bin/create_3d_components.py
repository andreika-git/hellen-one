#!/usr/bin/env python
############################################################################################
# Hellen-One: A script to create a 3D components view (VRML).
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys, re, math
import configparser
import gzip

### Unfortunately PyVRML97 (vrml.vrml97) is not capable of properly processing Altium-exported VRML-files...

if len(sys.argv) < 3:
    print ("Error! Please specify the place+board files and vrml filename.")
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

print ("* Starting merge of " + str(len(fragments)) + " board fragments...")

outf = gzip.open(fileOutName, 'wb')
outf.write("#VRML V2.0 utf8\n")

pat_hdr = re.compile('^#VRML.*')
pat_idx = re.compile(r'(DEF|USE)\s+(Shape|_)(\w)')
pat_kicad_transform = re.compile(r'DEF\s+(\w+)\s+Transform.*')

fId = 1
for frag in fragments:
	# convert to mm
	off_x_mm = float(frag["x"]) * 25.4
	off_y_mm = float(frag["y"]) * 25.4
	rot = float(frag["rot"])
	fileName = frag["path"] + "-vrml.wrl"
	z_offset = 0
	was_global_transform = False
	fragId = str(fId).zfill(2)
	
	print ("* Adding " + frag["name"] + " (" + fileName + ") at (" + str(off_x_mm) + "," + str(off_y_mm) + "), rot=" + str(rot) + "...")
	with open(fileName, 'rb') as f:
		for line in f:
			line = line.rstrip()
			# skip the headers (we write our own because there should be only 1 header)
			if pat_hdr.match(line):
				continue
			# add global transformation for the module
			if not was_global_transform:
				# for bottom-aligned kicad VRML files, we need to shift them down - to align it with the top surface of the board
				if pat_kicad_transform.match(line):
					print ("* Kicad VRML detected!")
					# the board is 1.6 mm thick?
					# todo: this is a 'hack'
					z_offset = -1.6
				outf.write("DEF TX" + frag["name"].replace('-', '') + " Transform {\n")
				outf.write("  center 0 0 0\n")
				outf.write("  rotation 0 0 1 " + str(math.radians(rot)) + "\n")
				outf.write("  scale 1.0 1.0 1.0\n")
				outf.write("  scaleOrientation 0 0 1 0\n")
				outf.write("  translation " + str(off_x_mm) + " " + str(off_y_mm) + " " + str(z_offset) + "\n")
				outf.write(" children [\n")
				was_global_transform = True
			
			line = pat_idx.sub(r'\g<1> \g<2>' + fragId + '\g<3>', line)
			outf.write(line + "\n")
		f.close()
		if was_global_transform:
			outf.write("] }\n")
	fId = fId + 1

outf.close()

print ("Done!")
