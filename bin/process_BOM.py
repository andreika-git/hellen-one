#!/usr/bin/env python
############################################################################################
# Hellen-One: A BOM processing script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

from collections import OrderedDict
import csv, os, sys, re

include_pat = re.compile(r'#include\s+\"?([^\"]+)\"?$')

def checkNonAsciiSymbols(row):
    for r in row:
        try:
            r.encode('ascii')
        except UnicodeEncodeError:
            print ("Error! The following line contains non-ASCII symbols:")
            print (row)
            sys.exit(5)

def read_repl_file(csv_name, repl_base_path, replList):
    print ("Reading replacement list from the CSV file " + csv_name + "...")
    with open(csv_name, 'rt', errors='replace') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            # skip empty lines
            if (len(row) < 1):
                continue
            checkNonAsciiSymbols(row)
            # process includes
            include = include_pat.match(row[0].strip())
            if (include):
                csv_sub_name = os.path.join(repl_base_path, include.group(1))
                if (csv_sub_name != csv_name):
                    read_repl_file(csv_sub_name, repl_base_path, replList)
            # skip comments (this is not strictly CSV-compliant, but useful for our purposes)
            if (row[0].startswith("#")):
                continue
            col0 = row[0].split(",")
            for col in col0:
                subrow = [col.strip(), row[1]]
                if (len(row) > 2):
                    subrow.append(row[2])
                if (len(row) > 3):
                    subrow.append(row[3])
                replList.append(subrow)

def printWarning(text):
    print (text)
    if warningFileName:
        with open(warningFileName, "a") as wf:
            wf.write(text + "\n")

if len(sys.argv) < 2:
    print ("Error! Please specify a BOM file name.")
    sys.exit(1)
fileName = sys.argv[1]

if len(sys.argv) > 2:
    repl_csv = sys.argv[2]
    repl_base_path = os.path.dirname(repl_csv)

if len(sys.argv) > 3:
    warningFileName = sys.argv[3]

print ("Opening BOM file " + fileName + "...")

rows = OrderedDict()
rowDes = OrderedDict()
emptyId = 1

with open(fileName, 'rt', errors='replace') as f:
    reader = csv.reader(f, delimiter=',')
    print ("Searching for duplicates...")
    for row in reader:
        checkNonAsciiSymbols(row)
        row[3] = row[3].strip()
        rowName = row[3]
        row[1] = row[1].split(", ")
        for rDes in row[1]:
            if rDes in rowDes:
                print ("* Error! Duplicate designators found in BOM: " + rDes)
                sys.exit(3)
            rowDes[rDes] = 1
        # all empty names should be saved separately
        if not rowName:
        	rows["_" + str(emptyId)] = row
        	emptyId += 1
        	continue
        if rowName in rows:
            oldRow = rows[rowName]
            if oldRow[0] != row[0]:
            	print ("* Error! Comment mismatch for the part #" + rowName + ": " + oldRow[0] + " != " + row[0])
            	sys.exit(2)
            if oldRow[2] != row[2]:
                printWarning ("* Warning! Footprint mismatch for the part #" + rowName + ": " + oldRow[2] + " != " + row[2])
            print ("* Duplicates found for " + rowName + " (" + row[0] + ")! Merging...")
            row[1] = oldRow[1] + row[1]
        rows[rowName] = row
        #for idx,item in enumerate(row):
        #    print idx , ": ", item

replList = list()
read_repl_file(repl_csv, repl_base_path, replList)

print ("Processing the board replacements...")
for r in replList:
    reDesignator = r[0]
    for rowName in list(rows.keys()):
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

print ("Checking for identical parts with different partnumbers...")
commentAndFootprint = OrderedDict()
for rowName in rows:
    row = rows[rowName]
    cf = row[0] + "_" + row[2]
    if not row[3]:
        continue
    partName = (",".join(row[1])) if (type(row[1]) == list) else row[1]
    if (cf in commentAndFootprint):
        if (commentAndFootprint[cf][1] != row[3]):
            printWarning ("* Warning! Identical parts " + partName + " and " + commentAndFootprint[cf][0] + " (" + cf + ") have different partnumbers: " + row[3] + " and " + commentAndFootprint[cf][1])
    else:
        commentAndFootprint[cf] = [partName, row[3]]

print ("Final checks...")
for rowName in rows:
    row = rows[rowName]
    if (row[0] == '?' and row[3].lower() == 'board_id'):
        partName = (",".join(row[1])) if (type(row[1]) == list) else row[1]
        print ("Error! The components used by Board_ID detection method (" + partName + ") are undefined!")
        print ("  Please include corresponding board definition file (board_id_XXX.csv) to your BOM replacement file.")
        print ("  If your Board_ID is unknown (custom board), just add the following line to the end of your bom_replace file:")
        print ("  #include hellen-one/board_id/board_id_unknown.csv")
        sys.exit(2)


print ("Saving...")
with open (fileName, 'wt') as new_f:
    rowIdx = 0
    for rowName in rows:
        #for idx,item in enumerate(rows[rowName]):
        #    print idx , ": ", item
        if rowIdx == 0:
            writer = csv.writer(new_f, quoting=csv.QUOTE_NONE, quotechar='"', escapechar=None, delimiter=',', lineterminator='\n')
        elif rowIdx == 1:
            writer = csv.writer(new_f, quoting=csv.QUOTE_ALL, quotechar='"', escapechar=None, delimiter=',', lineterminator='\n')
        row = rows[rowName]
        # restore empty names
        if rowName[0] == '_':
        	row[3] = ""
        if type(row[1]) == list:
            row[1] = ", ".join(row[1])
        writer.writerow(row)
        rowIdx += 1
print ("Done!")
