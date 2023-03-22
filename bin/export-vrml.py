import sys
from pcbnewTransition.pcbnew import LoadBoard, EXPORTER_VRML

b = LoadBoard(sys.argv[1])
e = EXPORTER_VRML(b)

# X and Y of Drill/Place origin are passed as parameters
x = float(sys.argv[2])
y = float(sys.argv[3])

e.ExportVRML_File(b.GetProject(), None, sys.argv[4], 1.0, False, True, None, x, y)
