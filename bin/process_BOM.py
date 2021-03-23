#!/usr/bin/env python
############################################################################################
# Hellen-One: A BOM processing script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

from collections import OrderedDict
import csv, sys, re

if len(sys.argv) < 2:
    print ("Error! Please specify a BOM file name.")
    sys.exit(1)
fileName = sys.argv[1]

if len(sys.argv) > 2:
    repl_csv = sys.argv[2]

print ("Opening BOM file " + fileName + "...")

rows = OrderedDict()
emptyId = 1

with open(fileName, 'rb') as f:
    reader = csv.reader(f, delimiter=',')
    print ("Searching for duplicates...")
    for row in reader:
        rowName = row[3]
        # all empty names should be saved separately
        if not rowName:
        	rows["_" + str(emptyId)] = row
        	emptyId += 1
        	continue
        row[1] = row[1].split(", ")
        if rowName in rows:
            oldRow = rows[rowName]
            if oldRow[0] != row[0]:
            	print ("* Error! Comment mismatch for the part #" + rowName + ": " + oldRow[0] + " != " + row[0])
            	sys.exit(2)
            if oldRow[2] != row[2]:
            	print ("* Warning! Footprint mismatch for the part #" + rowName + ": " + oldRow[2] + " != " + row[2])
            	#sys.exit(3)
            print ("* Duplicates found for " + rowName + " (" + row[0] + ")! Merging...")
            row[1] = oldRow[1] + row[1]
        rows[rowName] = row
        #for idx,item in enumerate(row):
        #    print idx , ": ", item

replList = list()
print ("Reading replacement list from the CSV file " + repl_csv + "...")
with open(repl_csv, 'rb') as f:
    reader = csv.reader(f, delimiter=',')
    for row in reader:
        # skip empty lines and comments (this is not strictly CSV-compliant, but useful for our purposes)
        if (len(row) < 1 or row[0].startswith("#")):
            continue
        replList.append(row)

print ("Processing the board replacements...")
for r in replList:
    reDesignator = r[0]
    for rowName in rows:
        row = rows[rowName]
        if reDesignator in row[1]:
            print ("* Removing " + reDesignator + " from the old row...")
            row[1].remove(reDesignator)
            if not row[1]:
                print ("* Deleting an empty row...")
                del rows[rowName]
    if len(r) < 4:
        continue
    reComment = r[1]
    reFootprint = r[2]
    rePartNumber = r[3]
    # find the matching row by partnumber (if set)
    if rePartNumber:
        if rePartNumber in rows:
            print ("* Adding " + reDesignator + " to another existing row...")
            rows[rePartNumber][1] += [reDesignator]
        else:
            print ("* Appending a new row for " + reDesignator + "...")
            rows[rePartNumber] = [reComment, [reDesignator], reFootprint, rePartNumber]

print ("Saving...")
with open (fileName, 'wb') as new_f:
    rowIdx = 0
    for rowName in rows:
        #for idx,item in enumerate(rows[rowName]):
        #    print idx , ": ", item
        if rowIdx == 0:
            writer = csv.writer(new_f, quoting=csv.QUOTE_NONE, quotechar='"', delimiter=',', lineterminator='\n')
        elif rowIdx == 1:
            writer = csv.writer(new_f, quoting=csv.QUOTE_ALL, quotechar='"', delimiter=',', lineterminator='\n')
        row = rows[rowName]
        # restore empty names
        if rowName[0] == '_':
        	row[3] = ""
        if type(row[1]) == list:
            row[1] = ", ".join(row[1])
        writer.writerow(row)
        rowIdx += 1
print ("Done!")
