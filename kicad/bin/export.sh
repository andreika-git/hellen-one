#!/bin/env bash

# Get path of script so we can call python scripts
DIR=$(dirname $0)

set -e

. revision.txt

IN="$BOARD_PREFIX$BOARD_SUFFIX"

echo "Working on [$IN] based on BOARD_PREFIX [$BOARD_PREFIX] and BOARD_SUFFIX [$BOARD_SUFFIX]"

if [ -z "$IN" ]
then
      echo "variables not set in revision.txt? \$IN is empty"
	exit -1
fi

OUT_FOLDER=gerber
mkdir -p $OUT_FOLDER

# Copy to backup so we can modify before exporting
cp "$IN.kicad_pcb" "$IN.kicad_pcb.bak"

SCHEMATIC_FILE=$IN.kicad_sch
PCB_FILE=$IN.kicad_pcb
NET_FILE=$OUT_FOLDER/$IN.net

if [ ! -f $SCHEMATIC_FILE ]
then
    echo "[$SCHEMATIC_FILE] schematic does not exist make sure at least KiCAD 6.0"
    exit -1
fi
echo Export PDF from [$SCHEMATIC_FILE] schematic
kicad-cli sch export pdf "$SCHEMATIC_FILE" --no-background-color -o "gerber/$IN.pdf"

echo Export netlist from [$SCHEMATIC_FILE] schematic into [$NET_FILE]
kicad-cli sch export netlist "$SCHEMATIC_FILE" --format kicadxml -o "$NET_FILE"
echo Run BOM plugin script on [$NET_FILE]
python "$DIR/../hellen-one-kicad-bom-plugin.py" "$OUT_FOLDER/$IN.net" "$OUT_FOLDER/$IN.csv"

echo Fill zones
python "$DIR/fill-zones.py" "$PCB_FILE"

echo Export Gerbers, drill file, and positions file
kicad-cli pcb export gerbers --disable-aperture-macros -l "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts,In2.Cu,In1.Cu" --no-x2 --use-drill-file-origin "$PCB_FILE" -o gerber/
echo Export drill file
kicad-cli pcb export drill --map-format ps --drill-origin plot --excellon-zeros-format suppressleading -u "in" "$PCB_FILE" -o gerber/
echo Export positions file
kicad-cli pcb export pos --format csv --units mm --use-drill-file-origin --bottom-negate-x "$PCB_FILE" -o "gerber/$IN-all-pos.csv"

echo Getting Drill/Place origin from PCB
X=$(grep "aux_axis_origin" "$PCB_FILE" | tr '	' ' ' | tr -s ' ' | cut -d ' ' -f 3)
Y=$(grep "aux_axis_origin" "$PCB_FILE" | tr '	' ' ' | tr -s ' ' | cut -d ' ' -f 4 | tr -d ')')
if [ ! "$Y" ]; then
    echo "aux_axis_origin is missing in the PCB file"
    exit -1
fi
echo Export VRML using $X $Y
python "$DIR/export-vrml.py" "$PCB_FILE" "$X" "$Y" "gerber/$IN.wrl"

echo Restore PCB backup
cp "$IN.kicad_pcb.bak" "$PCB_FILE"
