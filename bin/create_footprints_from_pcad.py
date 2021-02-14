#!/usr/bin/env python
############################################################################################
# Hellen-One: A footprint library converter script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import sys, re
import time, calendar
#import pprint

if len(sys.argv) < 3:
    print("Error! Please specify the src pcad-ascii file path and dst footprints folder name.")
    sys.exit(1)
pcadFileName = sys.argv[1]
footprintPath = sys.argv[2]

# todo: This is very specific to the source files and should be moved to a separate data file
footprint2refpackage = { 
	"R0603_x4": "R0603-4", 
	"BUTTON-SKRK": "SMD-2_2.9x3.9x1.7", 
	"CONN-USB-B-VERTICAL": "USB-B-VERTICAL", 
	"CONN-MICROSD-472192001": "SDAMB-012",
	"MPX4250AP": "867B", 
	"TSOT-23-6": "TSOT23-6",
	"SOT-26": "SOT23-6",
	"SOT-23-5": "SOT23-5",
	"SOIC16N": "SOIC16",
	"QUARTZ-SMD2012": "SMD2012",
	"QUARTZ-SMD5032": "SMD5032",
	"L-SMMS0650": "SMMS0650",
	"PTC-SMD1206": "SMD1206",
	"SOD-80": "SOD80",
}

pat_root = re.compile(r'^\((\w+)')
pat_padDef = re.compile(r'^\s*\(padStyleDef\s+\"([^\"]+)\"')
pat_viaDef = re.compile(r'^\s*\(viaStyleDef')
pat_padShapeDef = re.compile(r'^\s*\(padShape\s*\((\w+)\s+(\w+)\)\s*\(padShapeType\s+(\w+)\)\s*\(shapeWidth\s+([\w\.]+)\)\s*\(shapeHeight\s+([\w\.]+)\)')
pat_padHoleDef = re.compile(r'^\s*\(holeDiam\s+([\w\.]+)\)')
pat_patternDef = re.compile(r'^\s*\(patternDefExtended')
pat_compDef = re.compile(r'^\s*\(compDef')
pat_patternNameDef = re.compile(r'^\s*\(originalName\s+\"([^\"]+)\"')
pat_pad = re.compile(r'^\s*\(pad\s*\(padNum\s+(\w+)\)\s*\(padStyleRef\s*\"([\w\:]+)\"\)\s*\(pt\s+([+\-\w\.]+)\s+([+\-\w\.]+)\)\s*(\(rotation\s+([0-9\.]+)\))?\)')
pat_num = re.compile(r'^([+\-0-9\.]+)(mil|mm)?$')

isInLibrary = False
isInPattern = False
isInPad = False
curPadName = ""
curPatternName = ""

pads = {}
patterns = {}

shapeLut = {"hole": "circle", "RndRect": "roundrect", "Oval": "oval", "Rect": "rect" }

def getNumber(v):
	if v:
		num = pat_num.match(v)
		if num:
			val = float(num.group(1))
			if (num.group(2) == "mil"):
				val *= 0.0254
			return val
	return 0

with open(pcadFileName, 'rt') as fp:
	for line in fp:
		root = pat_root.match(line)
		if root:
			isInLibrary = True if root.group(1) == "library" else False
			#print("isInLibrary=" + str(isInLibrary))
		if isInLibrary:
			pad = pat_padDef.match(line)
			if pad:
				curPadName = pad.group(1)
				#print("padDef = " + curPadName)
				pads[curPadName] = {"shape": "hole", "width": 0, "height": 0 }
				isInPad = True
			if pat_viaDef.match(line):
				isInPad = False
			if isInPad:
				padHole = pat_padHoleDef.match(line)
				if padHole:
					pads[curPadName]["hole"] = padHole.group(1)
				padShape = pat_padShapeDef.match(line)
				if padShape:
					if getNumber(padShape.group(4)) != 0.0 and getNumber(padShape.group(5)) != 0.0:
						if not "shape" in pads[curPadName] or pads[curPadName]["shape"] == "hole":
							pads[curPadName]["layer"] = padShape.group(2)
							pads[curPadName]["shape"] = padShape.group(3)
							pads[curPadName]["width"] = padShape.group(4)
							pads[curPadName]["height"] = padShape.group(5)
							#pprint.pprint(pads[curPadName])
			if pat_patternDef.match(line):
				isInPattern = True
			if pat_compDef.match(line):
				isInPattern = False
			if isInPattern:
				name = pat_patternNameDef.match(line)
				if name:
					curPatternName = name.group(1)
					patterns[curPatternName] = {"pads":[] }
					print("* Found footprint: " + curPatternName)
				pad = pat_pad.match(line)
				if pad:
					padName = pad.group(2)
					if pads[padName]:
						padObj = pads[padName].copy()
						padObj["id"] = pad.group(1)
						padObj["x"] = pad.group(3)
						padObj["y"] = pad.group(4)
						padObj["rot"] = pad.group(6)
						#pprint.pprint(padObj)
						patterns[curPatternName]["pads"].append(padObj)

for pName in patterns:
	# we have an "external" pretty name for BOM (PackageReference) and Altium's internal footprint name (Footprint), so this is a way to connect them
	if pName in footprint2refpackage:
		referencePackageName = footprint2refpackage[pName]
	else:
		referencePackageName = pName
	print("Saving " + referencePackageName + "...")
	footprintFileName = footprintPath + "/" + referencePackageName + ".kicad_mod"
	with open(footprintFileName, 'w') as fp:
		timestamp = format(int(calendar.timegm(time.gmtime())), 'X')
		fp.write("(module " + pName + " (layer F.Cu) (tedit " + timestamp + ")\n")
		pat = patterns[pName]
		for pad in pat['pads']:
			#pprint.pprint(pad)
			padType = "smd"
			padShape = shapeLut[pad['shape']]
			padHole = getNumber(pad['hole'])
			padAngle = getNumber(pad['rot'])
			x = str(getNumber(pad['x']))
			y = str(-getNumber(pad['y']))	# invert y
			w = str(getNumber(pad['width']))
			h = str(getNumber(pad['height']))
			addAngle = "" if padAngle == 0.0 else (" " + str(padAngle))
			addRrect = ""
			addDrill = ""
			if padShape == "roundrect":
				addRrect = " (roundrect_rratio 0.2)"
			if padHole != 0.0:
				padType = "thru_hole" if pad['shape'] != "hole" else "np_thru_hole"
				addDrill = " (drill " + str(padHole) + ")"
			fp.write("  (pad " + pad['id'] + " " + padType + " " + padShape + " (at " + x + " " + y + addAngle + ") (size " + w + " " + h + ")"+ addDrill +" (layers F.Cu F.Mask)" + addRrect + ")\n")
		fp.write(")\n")

