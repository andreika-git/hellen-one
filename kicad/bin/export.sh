#!/bin/env bash

#
# Hellen-One: exports gerbers, drill, positions, BOM, schematic PDF and VRML from a KiCad frame project.
# Requires KiCad 10 (kicad-cli). Reads BOARD_PREFIX/BOARD_SUFFIX from revision.txt in the current folder.
# The board file is never modified: zone refill happens in-memory via 'kicad-cli pcb export gerbers --check-zones'.
#

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

KICAD_CLI="${KICAD_CLI:-kicad-cli}"
PYTHON="${PYTHON:-python3}"

KICAD_VERSION=$($KICAD_CLI version)
KICAD_MAJOR=${KICAD_VERSION%%.*}
echo "Using $KICAD_CLI $KICAD_VERSION"
if [ "$KICAD_MAJOR" -lt 10 ]
then
    echo "KiCad 10 or later is required, found $KICAD_VERSION"
    exit -1
fi

OUT_FOLDER=gerber
mkdir -p $OUT_FOLDER

SCHEMATIC_FILE=$IN.kicad_sch
PCB_FILE=$IN.kicad_pcb
NET_FILE=$OUT_FOLDER/$IN.net

if [ ! -f $SCHEMATIC_FILE ]
then
    echo "[$SCHEMATIC_FILE] schematic does not exist"
    exit -1
fi
if [ ! -f $PCB_FILE ]
then
    echo "[$PCB_FILE] board does not exist"
    exit -1
fi

echo Export PDF from [$SCHEMATIC_FILE] schematic
$KICAD_CLI sch export pdf "$SCHEMATIC_FILE" --no-background-color -o "$OUT_FOLDER/$IN.pdf"

echo Export netlist from [$SCHEMATIC_FILE] schematic into [$NET_FILE]
$KICAD_CLI sch export netlist "$SCHEMATIC_FILE" --format kicadxml -o "$NET_FILE"
echo Run BOM plugin script on [$NET_FILE]
$PYTHON "$DIR/../hellen-one-kicad-bom-plugin.py" "$NET_FILE" "$OUT_FOLDER/$IN.csv"

echo Export Gerbers with zones refilled in-memory
$KICAD_CLI pcb export gerbers --disable-aperture-macros -l "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts,In2.Cu,In1.Cu" --no-x2 --use-drill-file-origin --check-zones "$PCB_FILE" -o $OUT_FOLDER/
echo Export drill file
$KICAD_CLI pcb export drill --map-format ps --drill-origin plot --excellon-zeros-format suppressleading -u "in" "$PCB_FILE" -o $OUT_FOLDER/
echo Export positions file
$KICAD_CLI pcb export pos --format csv --units mm --use-drill-file-origin --bottom-negate-x "$PCB_FILE" -o "$OUT_FOLDER/$IN-all-pos.csv"

echo Getting Drill/Place origin from PCB
X=$(grep "aux_axis_origin" "$PCB_FILE" | tr '	' ' ' | tr -s ' ' | cut -d ' ' -f 3)
Y=$(grep "aux_axis_origin" "$PCB_FILE" | tr '	' ' ' | tr -s ' ' | cut -d ' ' -f 4 | tr -d ')')
if [ ! "$Y" ]; then
    echo "aux_axis_origin is missing in the PCB file"
    exit -1
fi
echo Export VRML using origin $X $Y mm
$KICAD_CLI pcb export vrml --units mm --user-origin "${X}x${Y}mm" --force "$PCB_FILE" -o "$OUT_FOLDER/$IN.wrl"

echo Export done
