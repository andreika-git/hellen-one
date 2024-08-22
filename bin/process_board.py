#!/usr/bin/env python
############################################################################################
# Hellen-One: A board processing script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

from __future__ import print_function

import os, sys, shutil, errno
import csv, re
import subprocess

if len(sys.argv) < 5:
	print ("Error! Please specify the board prefix, project base name, frame name, revision and optional [BOM replacement file] and [number of layers].")
	sys.exit(1)

board_prefix = sys.argv[1]
project_base_path = sys.argv[2]
frame_name = sys.argv[3]
frame_rev = sys.argv[4]

if len(sys.argv) > 5:
	bom_replace_csv = sys.argv[5]
else:
	bom_replace_csv = ""

if len(sys.argv) > 6:
	comp_img_offset = sys.argv[6]
else:
	comp_img_offset = "0,0"

num_layers = int(sys.argv[7]) if (len(sys.argv) > 7 and sys.argv[7] != "") else 4

imageDpi = "600"

# these should match the definitions in the parent shell script (create_board.sh)!
project_name = board_prefix + frame_name
board_name = project_name + "-" + frame_rev
project_path = project_base_path + "/boards/" + board_name
bom_replace_csv_path = project_base_path + "/" + bom_replace_csv
frame_path = project_path + "/frame"
board_path = project_path + "/board"
board_path_name = board_path + "/" + board_name
board_misc_path = board_path + "/misc"
board_misc_path_name = board_misc_path + "/" + board_name
merged_gerber_path = board_path + "/gerber"
board_cfg_path = board_path + "/board.cfg"
board_place_path = board_path + "/board_place.txt"
board_tmp_path = merged_gerber_path + "/" + board_name + ".tmp"
board_bom = board_misc_path_name + "-BOM.csv"
board_bom_mfr = board_path_name + "-BOM-JLC.csv"
board_cpl = board_path_name + "-CPL.csv"
board_img = board_path_name + ".png"
board_img_top = board_misc_path_name + "-top.png"
board_img_bottom = board_misc_path_name + "-bottom.png"
board_img_outline = board_misc_path_name + "-outline.png"
board_img_components = board_misc_path_name + "-components.png"
warnings_path = board_path + "/warnings.log"

node_bin = "node"
rotations = "bin/jlc_kicad_tools/cpl_rotations_db.csv"

# the format is: "Module:module_name/module_rev"
pat_module = re.compile(r'Module:([\w\-]+)/([\w\.]+)')

############################################################################################

def write_lines(f, lines):
	if type(lines) == str:
		f.write(lines + "\n")
	else:
		for l in lines:
			f.write(l + "\n")

def print_module(name, prefixPath, moduleName, fileName, isBoard, isBottom):
	prefix = prefixPath + "/" + moduleName
	# swap the layers for bottom-placed modules
	if (isBottom):
		top = "Bottom"
		bottom = "Top"
	else:
		top = "Top"
		bottom = "Bottom"
	with open(fileName, 'a') as file:
		write_lines(file, [
			"[" + name + "]",
			"Prefix = " + prefix,
			"*" + top + "Copper=%(prefix)s.GTL",
			"*" + top + "Soldermask=%(prefix)s.GTS",
			"*" + top + "SolderPasteMask=%(prefix)s.GTP",
			"*" + top + "Silkscreen=%(prefix)s.GTO",
			"*" + bottom + "Copper=%(prefix)s.GBL",
			"*" + bottom + "Soldermask=%(prefix)s.GBS",
			"*" + bottom + "Silkscreen=%(prefix)s.GBO",
			"*Keepout=%(prefix)s.GKO",
			"Drills=%(prefix)s.DRL",
			"drillspth=%(prefix)s.DRL"])
		if (os.path.isfile(prefix + ".GBP")):
			write_lines(file, "*" + bottom + "SolderPasteMask=%(prefix)s.GBP")
		if (num_layers >= 4 and ((os.path.isfile(prefix + ".G1") and os.path.isfile(prefix + ".G2")) or isBoard == 1)):
			write_lines(file, [
				"*InnerLayer2=%(prefix)s.G1",
				"*InnerLayer3=%(prefix)s.G2"])
		if (isBoard == 1):
			write_lines(file, [
				"*" + bottom + "SolderPasteMask=%(prefix)s.GBP",
				"ToolList = %(prefix)s.tmp",
				"Placement = %(prefix)s.tmp",
				"BoardOutline = %(prefix)s.tmp"])
		else:
			write_lines(file, "BoardOutline=%(prefix)s.GM15")

def append_cpl(src_fname, dst_fname, x, y, mrot, isBottom, suffix = ""):
	print ("* appending the CPL with offset (" + str(x) + "," + str(y) + ")...")
	with open(src_fname, 'rt') as src_f, open(dst_fname, 'a') as dst_f:
		reader = csv.reader(src_f, delimiter=',')
		i=0
		# skip header
		next(src_f)
		for row in reader:
			if len(row) < 5:
				print ("Error! Wrong format of CPL file " + src_fname)
				sys.exit(3)
			des = row[0]
			cxmm = row[1]
			cymm = row[2]
			lay = row[3]
			rot = row[4]
			# remove module designators
			if (re.match("^M[0-9]+$", des)):
				print ("* (skipping " + des + ")")
				continue
			
			# remove "mm" suffix
			cx = float(cxmm.replace("mm", ""))
			cy = float(cymm.replace("mm", ""))
			
			# rotate the coordinates
			mrot_idx = int(float(mrot) + 360.0) % 360  # can be negative
			rxy = {
				0: lambda cxy: [cxy[0], cxy[1]],
				90: lambda cxy: [-cxy[1], cxy[0]],
				180: lambda cxy: [-cxy[0], -cxy[1]],
				270: lambda cxy: [cxy[1], -cxy[0]],
			}[mrot_idx]([cx, cy])

			# rotate the footprint
			rot = float(rot) + float(mrot)
			rot = str(rot % 360.0)

			# swap layers for bottom-placed modules
			if (isBottom):
				lay = "Bottom" if (lay.lower() == "top") else "Top"
				# invert Y-coordinate (vertical flip)
				rxy[1] = -rxy[1]

			# offset the coordinates
			x_offset = rxy[0] + float(x)
			y_offset = rxy[1] + float(y)
			write_lines(dst_f, des + suffix + "," + str(x_offset) + "mm," + str(y_offset) + "mm," + lay + "," + rot)
			i = i + 1
			print (str(i) + " parts processed...", end = "\r")

def append_bom(src_fname, dst_fname, suffix = ""):
	print ("* appending the BOM...")
	with open(src_fname, 'rt') as src_f, open(dst_fname, 'a') as dst_f:
		reader = csv.reader(src_f, delimiter=',')
		i = 0
		# skip header
		next(src_f)
		for row in reader:
			if len(row) < 4:
				print ("Error! Wrong format of BOM file " + src_fname)
				sys.exit(3)
			comment = row[0]
			des = row[1]
			footprint = row[2]
			lcsc = row[3]

			# process designators
			des_list = des.split(", ")
			new_des_list = []
			for d in des_list:
				# remove module designators
				if (re.match("^M[0-9]+$", d)):
					print ("* (skipping " + d + ")")
					continue
				new_des_list.append(d + suffix)
			if len(new_des_list) < 1:
				continue
			des = ", ".join(new_des_list)

			write_lines(dst_f, "\"" + comment + "\",\"" + des + "\",\"" + footprint + "\",\"" + lcsc + "\"")
			i = i + 1
			print (str(i) + " parts processed...", end = "\r")

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def print_to_file(fileName, mode, lines):
	with open(fileName, mode) as f:
		write_lines(f, lines)

def delete_file(fileName):
	if os.path.exists(fileName):
		os.remove(fileName)

def check_returncode(result):
	# zero code means "success"
	if result:
		print ("\nWhere was an ERROR executing the script! Code=" + str(result))
		sys.exit(result)

############################################################################################

print ("Removing old files of the board...")

try:
	if os.path.exists(board_path):
		shutil.rmtree(board_path)
except OSError as e:
	if e.errno == errno.EEXIST and os.path.isdir(path):
		pass
	else:
		print ("Error: %s - %s." % (e.filename, e.strerror))
		sys.exit(1)

print ("Creating " + board_name + "...")

mkdir_p(board_path)
mkdir_p(board_misc_path)
mkdir_p(merged_gerber_path)

# create configs
print_to_file(board_cfg_path, "w", [
		"[DEFAULT]",
		"projdir = .",
		"",
		"[Options]",
		"ExcellonLeadingZeros = 0",
		"MeasurementUnits = inch",
		"AllowMissingLayers = 1",
		"FixedRotationOrigin = 1",
		"PanelWidth = 19.6",
		"PanelHeight = 15.7"])

# board gerbers
print_module("MergeOutputFiles", merged_gerber_path, board_name, board_cfg_path, 1, 0)

# frame gerbers
print_module(frame_name, frame_path, frame_name, board_cfg_path, 0, 0)

# the frame should always have zero coordinates, matching the left-bottom keepout border
print_to_file(board_place_path, "w", frame_name + " 0.000 0.000")

# add frame's BOM & CPL
print_to_file(board_cpl, "w", ["Designator,Mid X,Mid Y,Layer,Rotation"])
print_to_file(board_bom, "w", ["Comment,Designator,Footprint,LCSC Part #"])

append_cpl(frame_path + "/" + frame_name + "-CPL.csv", board_cpl, "0", "0", "0", 0)
append_bom(frame_path + "/" + frame_name + "-BOM.csv", board_bom)

schem_list = [frame_path + "/" + frame_name + "-schematic.pdf"]

print ("Processing modules...")
modules_list = {}
with open(frame_path + "/" + frame_name + "-BOM.csv", 'r') as bom_f:
	bom_reader = csv.reader(bom_f, delimiter=',')
	# skip header
	next(bom_f)
	for bom_row in bom_reader:
		module = bom_row[0]
		des = bom_row[1]
		footprint = bom_row[2]
		# is it a module?
		mod = pat_module.match(module)
		if mod:
			module_name = mod.group(1)
			module_rev = mod.group(2)
			des_list = des.split(", ")
			for des in des_list:
				print ("  ** Inserting " + module + " into " + des + "...")

				if (module_name in modules_list):
					modules_list[module_name] += 1
					module_suffix = "_" + str(modules_list[module_name])
				else:
					modules_list[module_name] = 1
					module_suffix = ""
				module_unique_name = module_name + module_suffix
			
				# get module coords from the CPL file
				with open(frame_path + "/" + frame_name + "-CPL.csv", 'r') as cpl_f:
					cpl_reader = csv.reader(cpl_f, delimiter=',')
					# skip header
					next(cpl_f)
					for cpl_row in cpl_reader:
						if des == cpl_row[0].strip():
							cxmm = cpl_row[1]
							cymm = cpl_row[2]
							lay = cpl_row[3]
							rot = cpl_row[4]
							xmm = cpl_row[5]
							ymm = cpl_row[6]
							isBottom = (lay == "Bottom")
							# remove "mm" suffix
							x = float(xmm.replace("mm", ""))
							y = float(ymm.replace("mm", ""))
							# convert into inches (the gerber coords are imperial)
							x_inch = x / 25.4
							y_inch = y / 25.4
	
							print ("  ** adding " + module_unique_name + "/" + module_rev + " on " + lay + ", coords: " + str(x_inch) + "\", " + str(y_inch) + "\" (" + str(x) + " mm, " + str(y) + " mm)")

							# add module gerbers
							module_path = "modules/" + module_name + "/" + module_rev
							print_module(module_unique_name, module_path, module_name, board_cfg_path, 0, isBottom)
							# inverse rot (CW<->CCW) for bottom modules
							rot = -float(rot) if (isBottom) else float(rot)
							irot = int(rot + 360.0) % 360
							rotated = ("*rotated" + str(irot)) if (irot != 0) else ""
							if (isBottom):
								rotated += "*flippedV"
							# write abs. coords
							print_to_file(board_place_path, "a", module_unique_name + rotated + " " + str(x_inch) + " " + str(y_inch))

							append_cpl(module_path + "/" + module_name + "-CPL.csv", board_cpl, x, y, rot, isBottom, module_suffix)

							append_bom(module_path + "/" + module_name + "-BOM.csv", board_bom, module_suffix)

							# adding schematics PDF for merging at the end
							if (module_unique_name == module_name):
								schem_list.append(module_path + "/" + module_name + "-schematic.pdf")
							break

print ("* Done!")

print ("Merging gerbers...")
p = subprocess.Popen([sys.executable, "bin/gerbmerge/gerbmerge", 
	"--place-file=" + board_place_path, 
	board_cfg_path], 
	stdin=subprocess.PIPE)
# pass 'y' symbol to the subprocess as if a user pressed 'yes'
p.communicate(input=b'y\n')[0]
check_returncode(p.returncode)

print ("Post-processing BOM...")
try:
	out = subprocess.check_output([sys.executable, "bin/process_BOM.py",
		board_bom,
		bom_replace_csv_path,
		warnings_path], stderr=subprocess.STDOUT)
	print (out.decode('ascii', errors='replace'))
except subprocess.CalledProcessError as e:
	print ("BOM processing error:\n" + e.output.decode('ascii', errors='replace'))
	sys.exit(2)

print ("Convert to the manufacturer's BOM...")
try:
	out = subprocess.check_output([sys.executable, "bin/convert_BOM_mfr.py",
		board_bom,
		board_bom_mfr], stderr=subprocess.STDOUT)
	print (out.decode('ascii', errors='replace'))
except subprocess.CalledProcessError as e:
	print ("Mfr's BOM conversion error:\n" + e.output.decode('ascii', errors='replace'))
	sys.exit(2)

print ("Merging Schematics...")
result = subprocess.call([sys.executable, "bin/python-combine-pdfs/python-combinepdf.py"]
	+ schem_list 
	+ ["-o", board_path_name + "-schematic.pdf"])
check_returncode(result)

print ("Rendering TOP side image...")
result = subprocess.call([sys.executable, "bin/render_gerber.py", 
	merged_gerber_path, 
	board_img_top, 
	"top", 
	imageDpi])
check_returncode(result)

print ("Rendering BOTTOM side image...")
result = subprocess.call([sys.executable, "bin/render_gerber.py", 
	merged_gerber_path, 
	board_img_bottom, 
	"bottom", 
	imageDpi])
check_returncode(result)

print ("Rendering OUTLINE image...")
result = subprocess.call([sys.executable, "bin/render_gerber.py", 
	merged_gerber_path, 
	board_img_outline, 
	"outline", 
	imageDpi])
check_returncode(result)

print ("Merging 3D-models of components...")
result = subprocess.call([sys.executable, "bin/create_3d_components.py", 
	board_place_path, 
	board_cfg_path, 
	board_misc_path_name + "-3D.wrl.gz"])
check_returncode(result)

print ("Rendering a 3D-model of the board components...")
result = subprocess.call([sys.executable, "bin/render_vrml/render_components.py",
	board_misc_path_name + "-3D.wrl.gz", 
	board_img_components, 
	imageDpi])
check_returncode(result)

print ("Creating a composite board image...")
result = subprocess.call([sys.executable, "bin/render_vrml/render_board.py",
	board_img_top, 
	board_img_outline, 
	board_img_components, 
	board_img, 
	comp_img_offset])
check_returncode(result)

print ("Creating an interactive html BOM...")
result = subprocess.call([sys.executable, "bin/gen_iBOM.py",
	project_name,
	frame_rev,
	imageDpi,
	merged_gerber_path + "/" + board_name + ".GKO",
	merged_gerber_path + "/" + board_name + ".GTO",
	merged_gerber_path + "/" + board_name + ".GBO",
	board_img,
	board_bom,
	board_cpl,
	"./ibom-data",
	rotations,
	board_path_name + "-ibom.html"])
check_returncode(result)

print ("Cleaning up...")
delete_file(board_cfg_path)
delete_file(board_place_path)
delete_file(board_tmp_path)

print ("Creating a zip-archive with gerbers...")
shutil.make_archive(board_path_name + "-gerber", "zip", board_path, "gerber")

print ("Board processing done!")

sys.exit(0)
