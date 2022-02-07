#!/usr/bin/env python
############################################################################################
# Hellen-One: A new Board-ID generation script. The result is stored in 'generated' folder.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import csv, sys, re

if len(sys.argv) < 2:
    print ("Error! Please specify a Board+rev name.")
    sys.exit(1)
boardName = sys.argv[1]

board_ids_csv = "board_ids.csv"
resistor_list_csv = "resistors.csv"

# todo: these should match used in gen_hellen_board_id_resistors.py, the firmware and mcu modules
r1 = "R133"
r2 = "R134"
r1_mult = 100

repl_csv = "generated/board_id_" + boardName + ".csv"

def getBoardIdFromResistorIndices(rIdx1, rIdx2):
	global r1_mult
	return rIdx1 * r1_mult + rIdx2

# board_id = R1_IDX * 100 + R2_IDX
def getResistorIndicesFromBoardId(board_id):
	global r1_mult
	rIdx1 = int(board_id / r1_mult)
	rIdx2 = int(board_id % r1_mult)
	return [rIdx1, rIdx2]

def getResistorFromIndex(idx):
    global resistorList
    return resistorList[idx][1]

def getIndexFromResistor(r):
    global resistorList
    for i,row in enumerate(resistorList):
        if (int(row[1]) == r):
            return i
    return -1

def calcNextId(lastId, resistorList):
    global numMajorResistors
    [rIdx1, rIdx2] = getResistorIndicesFromBoardId(lastId)
    rIdx2 += 1
    # todo: add support for the minor resistor series
    if (rIdx2 >= numMajorResistors):
        rIdx1 += 1
        rIdx2 = 0
    if (rIdx1 >= numMajorResistors):
        print ("The limit of Board IDs is reached! Cannot add a new Board ID.")
        sys.exit(2)
    newId = getBoardIdFromResistorIndices(rIdx1, rIdx2)
    return newId

def addNew(boardIdList, boardId, boardName):
    global resistorList, r1, r2
    [rIdx1, rIdx2] = getResistorIndicesFromBoardId(boardId)
    r1Value = getResistorFromIndex(rIdx1)
    r2Value = getResistorFromIndex(rIdx2)
    row = [boardId, r1Value, r2Value, boardName]
    boardIdList.append(row)
    r1Row = resistorList[rIdx1]
    r2Row = resistorList[rIdx2]
    repl = list()
    repl.insert(0, ["# resistor | value | footprint | part_number"])
    repl.append([ r1, r1Row[1], r1Row[2], r1Row[3] ])
    repl.append([ r2, r2Row[1], r2Row[2], r2Row[3] ])
    return repl

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

def saveCsv(fileName, rows):
    rowIdx = 0
    with open (fileName, 'wt') as new_f:
        for row in rows:
            if rowIdx == 0:
                writer = csv.writer(new_f, quoting=csv.QUOTE_NONE, quotechar='"', delimiter=',', lineterminator='\n')
            elif rowIdx == 1:
                writer = csv.writer(new_f, quoting=csv.QUOTE_ALL, quotechar='"', delimiter=',', lineterminator='\n')
            writer.writerow(row)
            rowIdx += 1

print ("Reading board ID list from " + board_ids_csv + "...")
boardIdList = readCsv(board_ids_csv)
print ("Reading resistor list " + resistor_list_csv + "...")
resistorList = readCsv(resistor_list_csv)

numMajorResistors = 0
for row in resistorList:
    # count major resistors
    if (int(row[0]) == 0):
        numMajorResistors += 1

print ("Searching for board IDs...")
lastId = 0
for row in boardIdList:
    bid = int(row[0].strip())
    r1Value = int(row[1].strip())
    r2Value = int(row[2].strip())
    bname = row[3].strip()
    rIdx1 = getIndexFromResistor(r1Value)
    rIdx2 = getIndexFromResistor(r2Value)
    checkBoardId = getBoardIdFromResistorIndices(rIdx1, rIdx2)
    # check integrity & validate resistors
    if (rIdx1 < 0 or rIdx2 < 0 or bid != checkBoardId):
        print ("Wrong boardId #" + str(bid) + " found in the stored list! Please fix the list before adding new records. Aborting...")
        sys.exit(3)
    # maintain uniqueness
    if (bname.lower() == boardName.lower()):
        print ("The board name " + boardName + " already exists in the list! Aborting...")
        sys.exit(4)
    if (bid > lastId):
        lastId = bid

newId = calcNextId(lastId, resistorList)
print ("Created a new board id for " + boardName + ": #" + str(newId))

print ("Adding a new board id to the list...")
repl = addNew(boardIdList, newId, boardName)

print ("Saving the list...")
boardIdList.insert(0, ["# board_id | R1 | R2 | board_name"])
saveCsv(board_ids_csv, boardIdList)

print ("Saving the replacement board id file...")
saveCsv(repl_csv, repl)

print ("Done!")
