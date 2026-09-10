# Some of the modules were designed in KiCAD

If you are designing a new ECU frame see https://github.com/andreika-git/hellen-one/tree/master/modules

doThis folder contains module _source_ files, not reusable resulting frames like [here](../modules).

See https://github.com/andreika-git/hellen-one/wiki/scripts-howto#how-to-create-a-module

## Toolchain

The export scripts in `bin/` target **KiCad 10** (`kicad-cli`). `export.sh` runs from a board repository root
(reads `revision.txt`) and writes `gerber/`: gerbers with zones refilled in-memory, drill, position CSV,
netlist + BOM CSV (via `hellen-one-kicad-bom-plugin.py`), schematic PDF and VRML. The board file itself is not modified.

Local run for the test frame:

```
cd tests && bash ../kicad/bin/export.sh
```

KiCad 8 named the inner layers `In1_Cu.g2` / `In2_Cu.g3`; KiCad 10 uses
`In1_Cu.g1` / `In2_Cu.g2`. Export automatically removes the obsolete filenames
when their replacements exist. To clean an existing board export manually:

```
python3 hellen-one/bin/cleanup_kicad_gerbers.py gerber uaefi-pro --dry-run
python3 hellen-one/bin/cleanup_kicad_gerbers.py gerber uaefi-pro
```

The copy step selects inner layers by full layer name and prefers the KiCad 10
pair, while still accepting a KiCad 8 pair. Regenerate the board outputs after
cleaning an export that contained both versions.
