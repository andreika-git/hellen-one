#!/usr/bin/env python
############################################################################################
# Hellen-One: Generates a header file containing the list of Board-IDs.
# The result is stored in 'libfirmware/board_id/boards_id.h' folder.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import csv, sys, os, re, datetime

board_ids_csv = "board_ids.csv"
libdir = "libfirmware/board_id"
board_ids_h = libdir + "/boards_id.h"

date_time = datetime.datetime.now()

def getBoardName(str):
	str = str.replace("-", "_")
	return str.upper()

def readCsv(fileName):
    rows = list()
    with open(fileName, 'rt') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            # skip empty lines and comments (this is not strictly CSV-compliant, but useful for our purposes)
            if (len(row) < 1 or row[0].startswith("#")):
                continue
            rows.append(row)
    return rows

def saveH(fileName, rows):
    with open (fileName, 'wt') as new_f:
        new_f.write("//\n// was generated automatically by Hellen Board-ID generation tool gen_board_ids_h.py " + str(date_time) + "\n//\n\n#pragma once\n\n")
        for row in rows:
            new_f.write("#define BOARD_ID_" + getBoardName(row[3]) + "\t\t\t" + row[0] + "\n")

if not os.path.isdir(libdir):
    print ("Error! Cannot find the destination folder " + libdir + "! Please make sure that 'libfirmware' submodule was initialized by calling 'git submodule update'")
    sys.exit(1)

print ("Reading board ID list from " + board_ids_csv + "...")
boardIdList = readCsv(board_ids_csv)

print ("Saving the header file to " + board_ids_h + "...")
saveH(board_ids_h, boardIdList)

print ("Done!")
