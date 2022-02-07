#!/usr/bin/env python
############################################################################################
# Hellen-One: This generates the header file needed for the firmware (stored in 'generated').
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import csv, sys, re, datetime

resistor_list_csv = "resistors.csv"
resistors_h = "generated/hellen_board_id_resistors.h"

#todo: maybe make capacitance & board-id multiplier configurable?
capacitance = 1.0
r1_mult = 100

def read_csv(fileName):
    rows = list()
    with open(fileName, 'rt') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            # skip empty lines and comments (this is not strictly CSV-compliant, but useful for our purposes)
            if (len(row) < 1 or row[0].startswith("#")):
                continue
            rows.append(row)
    return rows

date_time = datetime.datetime.now()

# flag, value, footprint, LCSC #
rows = read_csv(resistor_list_csv)

major = list()
minor = list()
for row in rows:
    # (flag = 0(major)/1(minor))
    flag = int(row[0])
    value = int(row[1])
    if (flag == 1):
    	minor.append(value)
    else:
        major.append(value)

majorLastIdx = len(major) - 1
minorLastIdx = len(minor) - 1
majorAndMinorLastIdx = len(major) + len(minor) - 1
numBoardIds = len(major) * (len(major) + len(minor))

with open(resistors_h, 'wt') as f:
    f.write("//\n// was generated automatically by Hellen Board-ID generation tool gen_hellen_board_id_resistors.py " + str(date_time) + "\n//\n\n")
    f.write("#pragma once\n")
    f.write("\n// major_idx = 0.." + str(majorLastIdx) + "\n")
    f.write("#define HELLEN_BOARD_ID_MAJOR_RESISTORS\t")
    for m in major:
    	f.write(str(m) + ", ")
    f.write("\n\n// minor_idx = 0.." + str(minorLastIdx) + "\n")
    f.write("#define HELLEN_BOARD_ID_MINOR_RESISTORS\t")
    for m in minor:
    	f.write(str(m) + ", ")
    f.write("\n\n// C = " + str(capacitance) + "uF\n")
    f.write("#define HELLEN_BOARD_ID_CAPACITOR " + str(capacitance) + "f\n")
    f.write("\n// R1_IDX = 0.." + str(majorLastIdx) + ", R2_IDX = 0.." + str(majorAndMinorLastIdx) + " (max. " + str(numBoardIds) + " boardIds)\n")
    f.write("#define HELLEN_GET_BOARD_ID(R1_IDX, R2_IDX) ((R1_IDX) * " + str(r1_mult) + " + (R2_IDX))\n")
