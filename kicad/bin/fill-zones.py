import sys
from pcbnew import LoadBoard, ZONE_FILLER, SaveBoard

b = LoadBoard(sys.argv[1])
bz = b.Zones()
zf = ZONE_FILLER(b).Fill(bz)

SaveBoard(sys.argv[1], b)
