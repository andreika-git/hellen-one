#!/usr/bin/env python
############################################################################################
# Hellen-One: A script to convert a Kicad module footprint (*.kicad_mod) to PCAD .LIA.
# Needed by AD projects to use Kicad-created modules.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys, errno
import csv, re
import glob, shutil

#if len(sys.argv) < 4:
#	print "Error! Please specify the module project folder, module name and rev."
#	sys.exit(1)
#project_base = sys.argv[1]
name = "wbo" # sys.argv[2]
#rev = sys.argv[3]

#base_path = project_base
#src_path = base_path
#dst_path = "modules"

mod_name = "MOD_HELLEN_" + name.upper()

pat_pad = re.compile(r'^\s*\(pad \"([^\"]+)\"\s+(thru_hole|smd)\s+(circle|oval|rect|roundrect)\s+\(at\s+([0-9\.\-]+)\s+([0-9\.\-]+)(\s+([0-9\.\-]+))?\)(\s+\(locked\))?\s+\(size\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)(\s+\(drill\s+([0-9\.\-]+)\))?\s+\(layers\s+\"?(.*?)\.Cu')
pat_line_rect = re.compile(r'^\s*\(fp_(line|rect)\s+\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)\s+\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)\s+\(layer\s+\"([^\"]+)\"\)\s+\(width\s+([0-9\.\-]+)\)(\s+\(fill\s+([a-z]+)\))?')
pat_zone = re.compile(r'^\s*\(zone\s+\(net 0\)\s+\(net_name\s+\"\"\)\s+\(layers\s+\"?(.*?)\.Cu\)')
pat_xy = re.compile(r'^\s*\(xy\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)')

shapeLut = {"circle": "Oval", "roundrect": "RndRect", "oval": "Oval", "rect": "Rect" }

# used by add_zone_line()
class Zone:
	in_zone = False
	zone_first = None
	zone_prev = None
	layer = ""
	lines = None

	def add_line(self, zone_cur):
		if self.zone_prev:
			print ("* adding line (" + self.zone_prev[0] + "," + self.zone_prev[1] + " - " + zone_cur[0] + "," + zone_cur[1] + ")")
			if (self.layer == 'F' or self.layer == '*'):
				self.lines.append([ self.zone_prev[0], self.zone_prev[1], zone_cur[0], zone_cur[1], "F.Zone", "0.1" ])
			if (self.layer == 'B' or self.layer == '*'):
				self.lines.append([ self.zone_prev[0], self.zone_prev[1], zone_cur[0], zone_cur[1], "B.Zone", "0.1" ])
		else:
			self.zone_first = zone_cur
		self.zone_prev = zone_cur

	def open(self, layer, lines):
		self.in_zone = True
		self.layer = layer
		self.lines = lines

	def close(self):
		if self.zone_first:
			self.add_line(self.zone_first)

def process_pcb(src_name, dst_name):
	with open(src_name, 'rt') as src_f, open(dst_name, 'w') as dst_f:
		dst_f.write("ACCEL_ASCII \"" + name + ".LIA\"\n\n")
		dst_f.write("(asciiHeader\n  (asciiVersion 3 0)\n)\n\n")

		pad_lib = []
		pads = []
		lines = []
		pad_names = {}

		zone = Zone()

		for line in src_f:
			zon = pat_zone.match(line)
			if zon:
				zone.open(zon.group(1), lines)
				print ("* Zone detected! Layer=" + zone.layer)

			pad = pat_pad.match(line)
			if pad:
				pad_name = pad.group(1)
				pad_type = pad.group(2)
				pad_shape = pad.group(3)
				pad_x = pad.group(4)
				pad_y = str(-float(pad.group(5))) # Kicad->AD: reverse Y-coord
				pad_rot = pad.group(7) or "0"
				pad_w = pad.group(9)
				pad_h = pad.group(10)
				pad_hole = pad.group(12) or "0"
				pad_layers = pad.group(13)
				print ("* pad detected!")
				print ("  name=" + pad_name)
				print ("  type=" + pad_type)
				print ("  shape=" + pad_shape)
				print ("  x=" + pad_x)
				print ("  y=" + pad_y)
				print ("  rot=" + pad_rot)
				print ("  w=" + pad_w)
				print ("  h=" + pad_h)
				print ("  hole=" + pad_hole)
				print ("  layers=" + pad_layers)
				pad_lib_entry = [ pad_type, pad_shape, pad_w, pad_h, pad_hole, pad_layers ]
				if pad_lib_entry not in pad_lib:
					pad_entry_idx = len(pad_lib)
					pad_lib.append(pad_lib_entry)
					print ("* adding pad type #" + str(pad_entry_idx))
				else:
					pad_entry_idx = pad_lib.index(pad_lib_entry)
				if (pad_name in pad_names):
					pad_unique_name = pad_name + "_" + str(pad_names[pad_name])
					pad_names[pad_name] += 1
				else:
					pad_unique_name = pad_name
					pad_names[pad_name] = 1
				pad_entry = [ pad_entry_idx, pad_name, pad_x, pad_y, pad_rot, pad_unique_name ]
				pads.append(pad_entry)
			lin = pat_line_rect.match(line)
			if lin:
				line_type = lin.group(1)
				line_x1 = lin.group(2)
				line_y1 = str(-float(lin.group(3))) # Kicad->AD: reverse Y-coord 
				line_x2 = lin.group(4)
				line_y2 = str(-float(lin.group(5))) # Kicad->AD: reverse Y-coord
				line_layer = lin.group(6)
				line_width = lin.group(7)
				line_fill = lin.group(9)
				print ("* " + line_type + " detected!")
				print ("  (" + line_x1 + "," + line_y1 + " - " + line_x2 + "," + line_y2 + ")")
				print ("  * layer=" + line_layer)
				print ("  * width=" + line_width)
				print ("  * fill=" + (line_fill or "?"))
				if (line_type == "rect"):
					if (line_fill != "none"):
						print ("Error! Filled rects currently not supported!")
						sys.exit(1)
					lines.append([ line_x1, line_y1, line_x2, line_y1, line_layer, line_width ])
					lines.append([ line_x2, line_y1, line_x2, line_y2, line_layer, line_width ])
					lines.append([ line_x2, line_y2, line_x1, line_y2, line_layer, line_width ])
					lines.append([ line_x1, line_y2, line_x1, line_y1, line_layer, line_width ])
				else:
					lines.append([ line_x1, line_y1, line_x2, line_y2, line_layer, line_width ])
			# parse zones and add them as lines on special layers (P-CAD doesn't support zones natively)
			if zone.in_zone:
				xy = pat_xy.match(line)
				if xy:
					zone_point_x = xy.group(1)
					zone_point_y = str(-float(xy.group(2))) # Kicad->AD: reverse Y-coord
					zone.add_line([zone_point_x, zone_point_y])

		# todo: add correct exit-zone conditions
		zone.close()
		
		# add pad entries
		dst_f.write("(library \"Library_1\"\n")
		pi = 0
		for pe in pad_lib:
			dst_f.write("  (padStyleDef \"PAD" + str(pi) + "\"\n")
			dst_f.write("    (holeDiam " + pe[4] + "mm)\n")
			dst_f.write("    (startRange 1)\n    (endRange 2)\n")
			if pe[0] == "smd":
				if pe[5] == "B":
					layers = ["layerNumRef 2"]
				else:
					layers = ["layerNumRef 1"]
			else:
				layers = ["layerNumRef 1", "layerNumRef 2", "layerType Signal"]
			for l in layers:
				dst_f.write("    (padShape (" + l + ") (padShapeType " + shapeLut[pe[1]] + ") (shapeWidth " + pe[2] + "mm) (shapeHeight " + pe[3] + "mm) )\n")
			dst_f.write("  )\n")
			pi += 1

		# add pads
		dst_f.write("  (patternDefExtended \"" + mod_name + "_1\"\n")
		dst_f.write("  (originalName \"" + mod_name + "\")\n")
		dst_f.write("    (patternGraphicsNameRef \"Primary\")\n\n    (patternGraphicsDef\n")
		dst_f.write("      (patternGraphicsNameDef \"Primary\")\n")
		dst_f.write("      (multiLayer\n")
		pi = 1
		for p in pads:
			dst_f.write("        (pad (padNum " + str(pi) + ") (padStyleRef \"PAD" + str(p[0]) + "\") (pt " + p[2] + "mm " + p[3] + "mm) (rotation " + p[4] + ") (defaultPinDes \"" + p[1] + "\"))\n")
			pi += 1
		dst_f.write("      )\n")
		line_layers = [ [ "F.SilkS", 6 ], [ "B.SilkS", 7 ], [ "F.Zone", 12 ], [ "B.Zone", 13 ] ]
		# output lines
		for ll in line_layers:
			dst_f.write("      (layerContents (layerNumRef " + str(ll[1]) + ")\n")
			for l in lines:
				if (l[4] == ll[0]):
					dst_f.write("        (line (pt " + l[0] + "mm " + l[1] + "mm) (pt " + l[2] + "mm " + l[3] + "mm) (width " + l[5] + "mm) )\n")
			dst_f.write("      )\n")
		dst_f.write("    )\n  )\n")
		dst_f.write("  (compDef \"" + mod_name + "_1\"\n    (originalName \"" + mod_name + "\")\n")
		dst_f.write("    (compHeader\n      (sourceLibrary \"\")\n      (numPins " + str(len(pads)) + ")\n      (numParts 1)\n      (refDesPrefix \"\")\n")
		dst_f.write("    )\n")
		for p in pads:
			dst_f.write("    (compPin \"" + p[5] + "\" (partNum 1) (symPinNum 1) (gateEq 0) (pinEq 0) )\n")
		dst_f.write("    (attachedPattern (patternNum 1) (patternName \"" + mod_name + "\")\n")
		dst_f.write("      (numPads " + str(len(pads)) + ")\n")
		dst_f.write("      (padPinMap\n")
		pi = 1
		for p in pads:
			dst_f.write("        (padNum " + str(pi) + ") (compPinRef \"" + p[5] + "\")\n")
			pi += 1
		dst_f.write("      )\n    )\n  )\n)\n")


#################################################

print ("Processing the pcb file...")

#process_pcb(src_path + "/hellen1-" + name + ".kicad_pcb", dst_path + "/" + name + "/" + rev + "/" + name + ".kicad_mod")
process_pcb("wbo.kicad_mod", "wbo.LIA")

print ("Done!")
