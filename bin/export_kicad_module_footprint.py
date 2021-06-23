#!/usr/bin/env python
############################################################################################
# Hellen-One: A script to export module footprints from Kicad module projects.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys, errno
import csv, re
import glob, shutil

if len(sys.argv) < 4:
	print "Error! Please specify the module project folder, module name and rev."
	sys.exit(1)
project_base = sys.argv[1]
name = sys.argv[2]
rev = sys.argv[3]

base_path = project_base
src_path = base_path
dst_path = "modules"

pat_symbol = re.compile(r'^(\s+)\(symbol\s+\"([^\"]+)\"(.*)$')
pat_prop = re.compile(r'^(\s+)\(property\s+\"([^\"]+)\"\s+\"([^\"]*)\"(.*)$')
pat_close_symbol = re.compile(r'')
pat_footprint = re.compile(r'^(\s+)\(footprint\s+\"([^\"]+)\"(.*)$')
pat_zone = re.compile(r'^(\s+)\(zone\s+\(net\s+0\)\s+\(net_name\s+\"\"\)\s+\(layer\s+\"([^\"]+)\"\)(.*)$')
pat_text = re.compile(r'^(\s+)\(fp_text\s+([^\s]+)\s+\"([^\"]*)\"(.*)$')

replace_props = { 
	"Reference": "M",
	"Value": "Module-" + name + "-" + rev,
	"Footprint": "hellen-one-" + name + "-" + rev + ":" + name,
}

replace_texts = { 
	"reference": "M",
	"value": "Module-" + name + "-" + rev,
}


def process_schematic(src_name, dst_name):
	with open(src_name, 'rt') as src_f, open(dst_name, 'w') as dst_f:
		in_module = False
		num_symbols = 1
		dst_f.write("(kicad_symbol_lib (version 20201005) (generator kicad_symbol_editor)\n")
		for line in src_f:
			m = pat_symbol.match(line)
			if m:
				if "Mod-Hellen" in m.group(2) and in_module == False:
					print ("* Found symbol " + m.group(2))
					# the close symbol should have the same indent as the open one
					pat_close_symbol = re.compile(r'^' + m.group(1) + '\)')
					line = m.group(1) + "(symbol \"" + name + ":Module-" + name + "-" + rev + "\"" + m.group(3) + "\n"
					dst_f.write(line[2:])
					in_module = True
					continue
				if in_module:
					print ("* replacing symbol " + m.group(2))
					line = m.group(1) + "(symbol \"Module-" + name + "-" + rev + "_" + str(num_symbols) + "_0\"" + m.group(3) + "\n"
					num_symbols += 1
					dst_f.write(line[2:])
					continue
			if in_module:
				p = pat_prop.match(line)
				if p and p.group(2) in replace_props:
					r = replace_props[p.group(2)]
					print ("* setting property " + p.group(2) + " to \"" + r + "\"")
					line = p.group(1) + "(property \"" + p.group(2) + "\" \"" + r + "\"" + p.group(4) + "\n"
				dst_f.write(line[2:])
				if pat_close_symbol.match(line):
					in_module = False
					break
		dst_f.write(")")

def process_pcb(src_name, dst_name):
	global pat_close_symbol
	with open(src_name, 'rt') as src_f, open(dst_name, 'w') as dst_f:
		in_footprint = False
		in_zone = False
		for line in src_f:
			m = pat_footprint.match(line)
			if m:
				if ("Mod-Hellen" in m.group(2) or "MOD_Hellen" in m.group(2) or "MOD_HELLEN" in m.group(2)) and in_footprint == False:
					print ("* Found footprint " + m.group(2))
					# the close symbol should have the same indent as the open one
					pat_close_symbol = re.compile(r'^' + m.group(1) + '\)')
					line = m.group(1) + "(footprint \"module-" + name + "-" + rev + "\"" + m.group(3) + "\n"
					dst_f.write(line[2:])
					in_footprint = True
					continue
			if not in_footprint:
				z = pat_zone.match(line)
				if z and in_zone == False:
					print ("* Found zone " + z.group(2))
					in_zone = True
			if in_footprint:
				if pat_close_symbol.match(line):
					in_footprint = False
					# don't write the footprint close symbol because we might have zones later
					continue
				t = pat_text.match(line)
				if t and t.group(2) in replace_texts:
					r = replace_texts[t.group(2)]
					print ("* setting text " + t.group(2) + " to \"" + r + "\"")
					line = t.group(1) + "(fp_text " + t.group(2) + " \"" + r + "\"" + t.group(4) + "\n"
				line = re.sub("\(net\s+[0-9]+\s+\"[^\"]*\"\)\s+", "", line)
				dst_f.write(line[2:])
			if in_zone:
				if pat_close_symbol.match(line):
					in_zone = False
				# make sure that the keepout is enabled by default
				line = line.replace("(copperpour allowed)", "(copperpour not_allowed)")
				line = line.replace("0.508", "0.2")
				dst_f.write(line)
		dst_f.write(")")

#################################################

print ("Processing the schematic file...")

process_schematic(src_path + "/hellen1-" + name + ".kicad_sch", dst_path + "/" + name + "/" + rev + "/" + name + ".kicad_sym")

print ("Processing the pcb file...")

process_pcb(src_path + "/hellen1-" + name + ".kicad_pcb", dst_path + "/" + name + "/" + rev + "/" + name + ".kicad_mod")

print ("Done!")
