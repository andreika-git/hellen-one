#!/bin/env bash

if [ -z "$1" ]; then
  echo "Pass file name without extension"
  exit 1
fi

# Get path of script so we can call python scripts
DIR=$(dirname $0)

IN="$1"

# Copy to backup so we can modify before exporting
cp "$IN.kicad_pcb" "$IN.kicad_pcb.bak"

# Export PDF from schematic
kicad-cli sch export pdf "$IN.kicad_sch" --no-background-color -o "gerber/$IN.pdf"

# Export netlist from schematic, then run BOM plugin script on it.
kicad-cli sch export netlist "$IN.kicad_sch" --format kicadxml -o "gerber/$IN.net"
python "$DIR/../hellen-one-kicad-bom-plugin.py" "gerber/$IN.net" "gerber/$IN.csv"

# Fill zones
python "$DIR/fill-zones.py" "$IN.kicad_pcb"

# Export Gerbers, drill file, and positions file
kicad-cli pcb export gerbers --disable-aperture-macros -l "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts,In2.Cu,In1.Cu" --no-x2 --use-drill-file-origin "$IN.kicad_pcb" -o gerber/
kicad-cli pcb export drill --map-format ps --drill-origin plot --excellon-zeros-format suppressleading -u "in" "$IN.kicad_pcb" -o gerber/
kicad-cli pcb export pos --format csv --units mm --use-drill-file-origin --bottom-negate-x "$IN.kicad_pcb" -o "gerber/$IN-all-pos.csv"

# Get Drill/Place origin from PCB
X=$(grep "aux_axis_origin" "$IN.kicad_pcb" | tr -s ' ' | cut -d ' ' -f 3)
Y=$(grep "aux_axis_origin" "$IN.kicad_pcb" | tr -s ' ' | cut -d ' ' -f 4 | tr -d ')')
# Export VRML
python "$DIR/export-vrml.py" "$IN.kicad_pcb" "$X" "$Y" "gerber/$IN.wrl"

# Restore backup
cp "$IN.kicad_pcb.bak" "$IN.kicad_pcb"
