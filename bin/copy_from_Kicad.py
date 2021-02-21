#!/usr/bin/env python
############################################################################################
# Hellen-One: A script to copy exported frame files from Kicad into project.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys, errno
import csv, re
import glob, shutil

if len(sys.argv) < 4:
    print "Error! Please specify the project base folder, name and rev."
    sys.exit(1)
project_base = sys.argv[1]
name = sys.argv[2]
rev = sys.argv[3]

base_path = project_base + "/hellen" + name + "/boards/hellen" + name + "-" + rev
src_path = base_path + "/kicad6/gerber"
dst_path = base_path + "/frame"

src_name = src_path + "/hellen" + name
dst_name = dst_path + "/" + name

fixRotationsPath = "bin/jlc_kicad_tools/cpl_rotations_db.csv"

pat_module = re.compile(r'^[Mm]odule-([\w]+)-([\w\.]+)')

#################################################

print ("Copying frame " + name + "-" + rev + " to the repository (" + dst_path + ")...")

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

mkdir_p(dst_path)

# copy gerbers
gerbers = [ ".GTL", ".GTO", ".GTP", ".GTS", ".GBL", ".GBO", ".GBS", ".GM1", ".DRL"]
for g in gerbers:
	copied = False
	for gPath in glob.glob(src_name + "*" + g):
		print ("* Copying " + name + g + "...")
		# keepout layer is a special case
		if (g == ".GM1"):
			shutil.copyfile(gPath, dst_name + ".GM15")
			shutil.copyfile(gPath, dst_name + ".GKO")
		else:
			shutil.copyfile(gPath, dst_name + g)
		copied = True
	if not copied:
		if (g == ".DRL"):
			print ("* Skipping Drill for " + name + "...")
		else:
			print ("Error! Gerber " + g + " not found for " + name + "!")
			sys.exit(2)

# copy the schematic
shutil.copyfile(src_name + ".pdf", dst_name + "-schematic.pdf")
# copy the VRML 3D components
shutil.copyfile(src_name + ".wrl", dst_name + "-vrml.wrl")

bom = dict()

print ("Copying BOM...")
with open(src_name + ".csv", 'rb') as src_f, open(dst_name + "-BOM.csv", 'w') as dst_f:
	dst_f.write("Comment,Designator,Footprint,LCSC Part #\n")
	reader = csv.reader(src_f, delimiter=',')
	# skip header
	next(src_f)
	for row in reader:
		comment = row[0]
		des = row[1]
		footprint = row[2]
		lcsc = row[3]
		bom[des] = footprint
		print ("* " + des)
		mod = pat_module.match(comment)
		if mod:
			print ("*** Module detected!")
			comment = "Module:" + mod.group(1) + "/" + mod.group(2)
		dst_f.write("\"" + comment + "\",\"" + des + "\",\"" + footprint + "\",\"" + lcsc + "\"\n")

print ("Reading rotations...")
rotations = {}
# read rotations csv (to undo weird JLC's angles which are not footprint-oriented)
with open(fixRotationsPath, 'rb') as f:
	next(f)
	reader = csv.reader(f, delimiter=',')
	for row in reader:
		rotations[row[0]] = float(row[1])

print ("Copying CPL...")
with open(src_name + "-all-pos.csv", 'rb') as src_f, open(dst_name + "-CPL.csv", 'w') as dst_f:
	dst_f.write("Designator,Mid X,Mid Y,Layer,Rotation,Ref-X(mm),Ref-Y(mm)\n")
	reader = csv.reader(src_f, delimiter=',')
	# skip header
	next(src_f)
	for row in reader:
		# Ref,Val,Package,PosX,PosY,Rot,Side
		des = row[0]
		posx = row[3]
		posy = row[4]
		rot = float(row[5])
		side = row[6]
		print ("* " + des)
		if bom[des]:
			for r in rotations:
				if re.match(r, bom[des]):
					rot += rotations[r]
					rot = rot % 360.0
					print ("* fixing rotations for " + des)
		side = side.capitalize() 
		dst_f.write(des + "," + posx + "mm," + posy + "mm," + str(rot) + "," + side + "," + posx + "mm," + posy + "mm\n")

print ("Done!")
