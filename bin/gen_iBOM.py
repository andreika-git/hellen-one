#!/usr/bin/env python
############################################################################################
# Hellen-One: A board rendering script.
#
# here we produde andreika-git-iBom using gerbers, placement and BOM files as input.
# andreika-git-iBom adds 3D view of the PCB into the original https://github.com/openscopeproject/InteractiveHtmlBom
#
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################
#
# based on iBom-template.html produced by https://github.com/openscopeproject/InteractiveHtmlBom
#


import os, sys
import re
import json, csv
import math, copy
import base64
from datetime import datetime


sys.path.append("./bin/InteractiveHtmlBom/InteractiveHtmlBom/core")
from lzstring import LZString

if len(sys.argv) < 12:
    print ("Error! Please specify all the parameters!")
    sys.exit(1)

boardName = sys.argv[1]
revision = sys.argv[2]
renderedPcbDpi = sys.argv[3]

keepoutPath = sys.argv[4]
topSilkPath = sys.argv[5]
bottomSilkPath = sys.argv[6]
renderedPcbPath = sys.argv[7]
bomPath = sys.argv[8]
cplPath = sys.argv[9]
footprintsPath = sys.argv[10]
fixRotationsPath = sys.argv[11]
iBomFilePath = sys.argv[12]

htmlFileName = './bin/iBom-template.html'
inch_to_mm = 25.4


def getFormat(xI, xD, yI, yD, yInvert):
	print ("* Format: ", xI, xD, yI, yD)
	fmt_pat_x = re.compile(r'^([0-9]{'+xI+'})([0-9]{'+xD+'})$')
	fmt_pat_y = re.compile(r'^([0-9]{'+yI+'})([0-9]{'+yD+'})$')
	return [fmt_pat_x, fmt_pat_y, yInvert]

def getCoords(pos, format):
	x = format[0].match(pos[0])
	y = format[1].match(pos[1])
	if x and y:
		x = float(x.group(1) + "." + x.group(2)) * inch_to_mm
		y = float(y.group(1) + "." + y.group(2)) * inch_to_mm
		if format[2]:
			y = format[2] - y
		return [x, y]
	sys.exit('Error! Cannot parse position ' + str(pos))

def getSize(size, format):
	if type(size) is list:
		size = 0.5 * (float(size[0]) + float(size[1]))
	return float(size) * inch_to_mm

def readGerber(filePath, yInvert):
	print("* Reading gerber file " + filePath + "...")
	json = []
	apertList = dict()
	apert_circle_pat = re.compile(r'^%ADD([0-9]+)C,([+\-0-9\.]+)(X([+\-0-9\.]+))?\*%$')
	apert_rect_pat = re.compile(r'^%ADD([0-9]+)R,([+\-0-9\.]+)(X([+\-0-9\.]+))?(X([+\-0-9\.]+))?\*%$')
	op_pat  = re.compile(r'^(X([+\-0-9]+))?(Y([+\-0-9]+))?D([0-9]+)\*$')
	format_pat = re.compile(r'^%FSLAX([0-9])([0-9])Y([0-9])([0-9])\*%$')
	cur_x = "0"
	cur_y = "0"
	cur_size = "0"
	cur_aper_type = ""
	inPoly = False
	polyStartPos = []
	polyOutlines = []
	polyPoints = []
	minCoord = [ 99999, 99999 ]
	maxCoord = [ -99999, -99999 ]
	format = getFormat("2", "5", "2", "5", yInvert)
	invertedMask = False
	with open(filePath, 'rt') as f:
		for line in f:
			line = line.strip()
			#print line
			if line == "%LPC*%":
				invertedMask = True
			if line == "%LPD*%":
				invertedMask = False
			fmt = format_pat.match(line)
			if fmt:
				format = getFormat(fmt.group(1), fmt.group(2), fmt.group(3), fmt.group(4), yInvert)
			apertCircle = apert_circle_pat.match(line)
			if apertCircle:
				apertNum = int(apertCircle.group(1))
				apertSize = apertCircle.group(2)
				apertList[apertNum] = ["circle", apertSize]
				# print ("* Aperture C: " + str(apertNum) + " = " + apertSize)
			
			apertRect = apert_rect_pat.match(line)
			if apertRect:
				apertNum = int(apertRect.group(1))
				apertSizeX = apertRect.group(2)
				apertSizeY = apertRect.group(4)
				apertList[apertNum] = ["rect", [apertSizeX, apertSizeY]]
				# print ("* Aperture R: " + str(apertNum) + " = " + apertSizeX + " " + apertSizeY)
			
			op = op_pat.match(line)
			if op:
				x = op.group(2) or cur_x
				y = op.group(4) or cur_y
				op = op.group(5)
				# draw
				if op == "01":
					curCoords = getCoords([x, y], format)
					minCoord[0] = min(curCoords[0], minCoord[0])
					minCoord[1] = min(curCoords[1], minCoord[1])
					maxCoord[0] = max(curCoords[0], maxCoord[0])
					maxCoord[1] = max(curCoords[1], maxCoord[1])

					if inPoly:
						polyPoints.append(curCoords)
					else:
						jsonLine = {"type": "segment", "width": getSize(cur_size, format), "start": getCoords([cur_x, cur_y], format), "end": curCoords}
						json.append(jsonLine)
				# move
				if op == "02":
					if inPoly and len(polyPoints) > 0:
						polyOutlines.append(polyPoints)
						polyPoints = []
				# flash
				if op == "03":
					curCoords = getCoords([x, y], format)
					if cur_aper_type == "circle":
						# todo: approximate with poly?
						jsonCircle = {"type": "circle", "width": 0.2, "start": curCoords, "radius": getSize(cur_size, format) }
						json.append(jsonCircle)
					if cur_aper_type == "rect":
						xS = getSize(cur_size[0], format) / 2
						yS = getSize(cur_size[1], format) / 2
						color = "#fff" if invertedMask else "#aa4"
						jsonPoly = {"type": "polygon", "pos": curCoords, "angle": 0, "color": color, "polygons": [[[-xS, -yS], [xS, -yS], [xS, yS], [-xS, yS]]]}
						json.append(jsonPoly)
				if int(op) > 3:
					a = int(op)
					cur_aper_type = apertList[a][0]
					cur_size = apertList[a][1]
					# print ("* Changing aperture: ", a)
				else:
					cur_x = x
					cur_y = y
			if line == "G36*":	# region begin
				polyStartPos = [ cur_x, cur_y ]
				polyOutlines = []
				polyPoints = []
				inPoly = True
			if line == "G37*":	# region end
				color = "#fff" if invertedMask else "#aa4"
				jsonPoly = {"type": "polygon", "pos": [0, 0], "angle": 0, "color": color, "polygons": []}
				for ol in polyOutlines:
					jsonOutline = []
					for point in ol:
						jsonOutline.append(point)
					jsonPoly["polygons"].append(jsonOutline)
				json.append(jsonPoly)
				inPoly = False
		f.close()
	return { "json": json, "min": minCoord, "max": maxCoord }

def updateBbox(bbox, padXY, padWH):
	bbox[0][0] = min(bbox[0][0], padXY[0] - padWH[0])
	bbox[0][1] = min(bbox[0][1], padXY[1] - padWH[1])
	bbox[1][0] = max(bbox[1][0], padXY[0] + padWH[0])
	bbox[1][1] = max(bbox[1][1], padXY[1] + padWH[1])		
	return bbox

# footprint should be flipped if placed on the bottom side
def getFootprintLayer(fpLayer, frameLayer):
	if fpLayer == "F":
		return frameLayer
	return ("F" if frameLayer == "B" else "B") # flip layer

def readFootprint(fpname, frameLayer, footprintsPath, des):
	if not fpname:
		return None
	pat_module = re.compile(r'\s*\((module|footprint)\s+\"?([\w\-\.\:]+)\"?\s+(\(version[^\)]*\))?\s*(\(generator[^\)]*\))?\s*\(layer\s+\"?([FB])')
	pat_pad = re.compile(r'^\s*\(pad\s+\"?([0-9A-Z]+)\"?\s+(\w+)\s+(\w+)\s+\(at\s+([+\-0-9e\.]+)\s+([+\-0-9e\.]+)\s*([+\-0-9\.]+)?\)\s+\(size\s+([+\-0-9\.]+)\s+([+\-0-9\.]+)\)(\s*\(drill\s+([+\-0-9\.]+)\))?\s+\(layer[s]?\s+\"?([^\)]+)\)(\s*\(roundrect_rratio\s+([+\-0-9\.]+)\))?')
	pat_pad_layer = re.compile(r'([^\.]+)\.CU')

	fpFileName = footprintsPath + "/" + fpname + ".kicad_mod"
	print ("* Reading " + fpFileName)
	if not os.path.isfile(fpFileName):
		print("* Error! Footprint NOT FOUND! Skipping " + des)
		return None

	json = {"drawings": [], "pads": []}
	bbox = [[ 9999.0, 9999.0 ], [ -9999.0, -9999.0 ]]
	with open(fpFileName, 'rt') as f:
		# module definition can be multiline
		allFile = f.read()
		f.seek(0)
		module = pat_module.match(allFile)
		if module:
			fpLayer = module.group(5)
			json["layer"] = getFootprintLayer(fpLayer, frameLayer)
		# pad definitions are single-line
		for line in f:
			pad = pat_pad.match(line)
			if pad:
				padIdx = pad.group(1)
				padType = pad.group(2)
				padShape = pad.group(3)
				padX = pad.group(4)
				padY = pad.group(5)
				padRot = pad.group(6) if pad.group(6) else "0"
				padW = pad.group(7)
				padH = pad.group(8)
				padDrill = pad.group(10) if pad.group(10) else "0"
				padLayers = pad.group(11) if pad.group(11) else ""
				padRrect = pad.group(13) if pad.group(13) else "0"
				bbox = updateBbox(bbox, [float(padX), float(padY)], [float(padW) * 0.5, float(padH) * 0.5])
				# process pad layers
				layersList = padLayers.split(" ")
				layers = []
				for l in layersList:
					padLayer = pat_pad_layer.match(l.strip('\" ').upper())
					if padLayer:
						padLayer = padLayer.group(1)
						if padLayer == "*":
							layers.append("F")
							layers.append("B")
						else:
							layers.append(getFootprintLayer(padLayer, frameLayer))
				pad = { 
					"layers": layers,
					"type": ("smd" if padType == "smd" else "th"),
					"pos": [ float(padX), float(padY) ],
					"size": [ float(padW), float(padH) ],
					#"offset": [ 0.0, 0.0 ],
					"angle": float(padRot),
					"shape": padShape
				}
				if padIdx == "1":
					pad["pin1"] = 1
				if padShape == "roundrect":
					pad["radius"] = padRrect
				if padType != "smd":
					pad["drillsize"] = [float(padDrill), float(padDrill)]
				json["pads"].append(pad)
	json["bbox"] = { 
		"relpos": bbox[0], 
		"size": [bbox[1][0] - bbox[0][0], bbox[1][1] - bbox[0][1]], 
	}
	return json

def getPosValue(c):
	return float(c.replace("mm", ""))

def rotate(origin, point, angle):
	# the angle is inverted because the Y-axis is inverted
	angleRad = math.radians(-angle)
	[ox, oy] = origin
	[px, py] = point

	qx = ox + math.cos(angleRad) * (px - ox) - math.sin(angleRad) * (py - oy)
	qy = oy + math.sin(angleRad) * (px - ox) + math.cos(angleRad) * (py - oy)
	return [qx, qy]

def readFootprints(bomPath, cplPath, footprintsPath, yInvert):
	json = {"footprints": [], 
		"bom": {
			"both": [], 
			"F": [],
			"B": [], 
			"skipped": []
		}
	}
	bom = {}
	bomlut = []
	footprints = {}
	rotations = {}
	# read rotations csv (to undo weird JLC's angles which are not footprint-oriented)
	with open(fixRotationsPath, 'rt') as f:
		next(f)
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			rotations[row[0]] = float(row[1])
	# read BOM csv
	with open(bomPath, 'rt') as f:
		next(f)
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			if not row[2]:
				print("* Skipping an empty footprint for (" + row[1] + ")...")
				continue
			bb = row[1].split(", ")
			bomlut.append({ "value": row[0], "fp": row[2], "refs": [], "layer": "F" })
			idx = len(bomlut) - 1
			for b in bb:
				bom[b] = { "fp": row[2], "idx": idx }
	# read CPL csv
	with open(cplPath, 'rt') as f:
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			if row[0] in bom:
				fpname = bom[row[0]]["fp"]
				layer = "B" if row[3].strip().lower() == "bottom" else "F"
				idx = bom[row[0]]["idx"]
				# search the stored footprint or load a new one
				if fpname in footprints:
					fprint = footprints[fpname + layer]
				else:
					fprint = readFootprint(fpname, layer, footprintsPath, row[0])
					# if the footprint is not found, we cannot add it to the iBOM
					if not fprint:
						if idx in bomlut:
							bomlut.remove(idx)
						del bom[row[0]]
						continue
					footprints[fpname + layer] = fprint
				fpr = copy.deepcopy(fprint)
				fpr["ref"] = row[0]
				fpr["bbox"]["pos"] = [ getPosValue(row[1]), getPosValue(row[2]) ]
				fpr["bbox"]["angle"] = float(row[4])
				origin = [0, 0]
				rotation = 0
				# reverse the JLC's rotation if this is one of 'special' corrected footprints
				for rot in rotations:
					if re.match(rot, fpname):
						rotation = -rotations[rot]
				fpr["bbox"]["angle"] += rotation
				fpr["bbox"]["pos"][1] = yInvert - fpr["bbox"]["pos"][1]
				for p in range(len(fpr["pads"])):
					# move and rotate the pads according to the CPL data
					fpr["pads"][p]["pos"] = rotate(origin, fpr["pads"][p]["pos"], fpr["bbox"]["angle"])
					fpr["pads"][p]["pos"][0] += fpr["bbox"]["pos"][0]
					fpr["pads"][p]["pos"][1] += fpr["bbox"]["pos"][1]
					fpr["pads"][p]["angle"] += fpr["bbox"]["angle"]
				json["footprints"].append(fpr)
				fid = len(json["footprints"]) - 1
				bomlut[idx]["refs"].append([row[0], fid])
				bomlut[idx]["layer"] = layer

	for b in bomlut:
		refs = b["refs"]
		if len(refs) < 1:
			print ("* Skipping DNP component: " + b["value"])
			continue
		bomItem = [
			len(refs), 
			b["value"], 
			b["fp"],
			refs, 
			[]
		]
		json["bom"][b["layer"]].append(bomItem)
		json["bom"]["both"].append(bomItem)
	return json
	
###################################################################

with open(htmlFileName, 'rt') as f:
	html = f.read()
	f.close()

data = {
	"footprints": [	], 
	"edges": [], 
	"ibom_version": "v2.3", 
	"bom": { }, 
	"silkscreen": { "B": [], "F": [] }, 
	"edges_bbox": {	}, 
	"font_data": { },
	"metadata": { "date": datetime.now().strftime("%Y-%m-%d, %H:%M:%S"), "company": "rusEFI", "revision": revision, "title": "Hellen One: " + boardName }
}

# first, get yInvert
keepout = readGerber(keepoutPath, None)

yInvert = keepout["min"][1] + keepout["max"][1]
keepout = readGerber(keepoutPath, yInvert)

#print json.dumps(edges)
data["edges"] = keepout["json"]
data["edges_bbox"]["minx"] = keepout["min"][0]
data["edges_bbox"]["miny"] = keepout["min"][1]
data["edges_bbox"]["maxx"] = keepout["max"][0]
data["edges_bbox"]["maxy"] = keepout["max"][1]

topSilk = readGerber(topSilkPath, yInvert)
bottomSilk = readGerber(bottomSilkPath, yInvert)
data["silkscreen"] = { "F": topSilk["json"], "B": bottomSilk["json"] }

footprints = readFootprints(bomPath, cplPath, footprintsPath, yInvert)
data["footprints"] = footprints["footprints"]
data["bom"] = footprints["bom"]

print("* Compressing the data...")
jsonText = json.dumps(data)

print("* Adding the pcb image...")
with open(renderedPcbPath, mode='rb') as f:
	renderedPcb = f.read()
	html = html.replace('___PCBDPI___', renderedPcbDpi)
	html = html.replace('___PCBIMAGE___', 'data:image/png;base64,' + base64.b64encode(renderedPcb).decode('ascii'))

print("* Adding the BOM data...")
jsonBase64 = LZString().compressToBase64(jsonText)
html = html.replace('___PCBDATA___', jsonBase64)

print("* Writing the output BOM file...")

with open(iBomFilePath, "wt") as wf:
	wf.write(html)
	wf.close()

print ("Done!")

