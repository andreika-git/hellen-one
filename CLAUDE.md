# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Hellen One is a toolset for building custom rusEFI ECU PCBs by **merging gerbers of proven, versioned modules into a user-designed "frame" PCB**. The frame (drawn in KiCad) holds mainly the vehicle connector plus module footprints; this repo supplies the modules and the scripts that stitch everything into fab-ready output (merged gerbers, BOM/CPL for JLCPCB, schematic PDF, board renders, interactive HTML BOM).

Board projects live in *separate* repos (e.g. `rusefi/hellen-example`, `rusefi/uaefi`) that include this repo as a `hellen-one` git submodule and call its reusable GitHub workflows. This repo is the shared engine; most day-to-day commits here are data edits (`global-replace.csv`, `board_id/`, module revisions).

Submodules are required (`git submodule update --init --recursive`): `bin/gerbmerge`, `bin/pcb-tools`, `bin/python-combine-pdfs`, `bin/InteractiveHtmlBom`, `board_id/libfirmware`.

## Commands

The scripts hardcode `python3.8` (see `python_bin` in `bin/create_board.sh`, `bin/create_board_with_prefix.sh`, `bin/check_all.sh`). Docker is the supported way to run them locally.

```bash
# Full test run in Docker (what CI does): builds image, runs run_tests.sh
bash step1-build-docker.sh
bash step2-run-docker.sh            # optional arg: alternative script to run instead of run_tests.sh

# Natively (needs python3.8, Xvfb, deps from bin/requirements.txt; check_all.sh is interactive)
bash run_tests.sh
```

`run_tests.sh` starts Xvfb on `:99`, runs `bin/check_all.sh` (dependency checker, prompts to install missing packages), then from `tests/` runs the two pipeline steps on the sample `hellen1test` frame. Expected output is in `tests/boards.EXAMPLE/hellen1test-a/`. There is no unit test suite; the pipeline running end to end is the test.

Run the two steps individually (always from repo root, paths are relative to it):

```bash
# Step 2: import KiCad export (tests/gerber/) into tests/boards/hellen1test-a/frame/
python3 ./bin/copy_from_Kicad.py "frames:hellen" "tests" "../../gerber" "1test" "a"
# Step 3: merge modules and produce tests/boards/hellen1test-a/board/
sh bin/create_board_with_prefix.sh "hellen" "tests" "1test" "a" "bom_replace_hellen1test-a.csv" "0,0"
```

Board repos drive the same thing via `bin/step1_build_hellen-one_docker.sh`, `bin/step2_copy_with_docker.sh`, `bin/step3_create_board_with_docker.sh`, which read `BOARD_PREFIX`, `BOARD_SUFFIX`, `BOARD_REVISION`, `BOARD_LAYERS`, `BOARD_PCB_OFFSET` from the board repo's `revision.txt`.

Other commands:

```bash
# Export gerbers/BOM/CPL/PDF/VRML from a KiCad frame (needs KiCad 10 kicad-cli; reads revision.txt in cwd)
bash kicad/bin/export.sh
# Same thing on the test frame (tests/revision.txt is committed):
cd tests && bash ../kicad/bin/export.sh

# Allocate a new Board-ID: uncomment/add a line in board_id/test.sh, then
cd board_id && bash test.sh        # writes generated/board_id_<name>.csv, updates board_ids.csv and libfirmware/board_id/boards_id.h

# Re-export a KiCad-designed module into modules/<name>/<rev>/ (see kicad/modules/hellen1-*/copy_module_*.bat)
python ./bin/copy_from_Kicad.py "modules" "kicad/modules" "gerber" "wbo" "0.6"
```

## Pipeline architecture

Three stages, each a separate entry point:

1. **KiCad export** (`kicad/bin/export.sh`, requires KiCad 10, runs in GitHub Actions): pure `kicad-cli`, no `pcbnew` Python. Exports gerbers with `--check-zones` (in-memory zone refill, the board file is never modified), drill, positions CSV, schematic PDF and VRML (`pcb export vrml --user-origin` set from the board's `aux_axis_origin`). `kicad/hellen-one-kicad-bom-plugin.py` turns the XML netlist into a `Comment,Designator,Footprint,LCSC Part #` CSV using the `kicad_netlist_reader` shipped with KiCad (`/usr/share/kicad/plugins`, overridable with `KICAD_PLUGINS_DIR`); a `MyComment=DNP` field or the native DNP attribute blanks the LCSC number. Output goes to `gerber/` in the board repo. `kicad-cli` rewrites `*.kicad_prl`; `bin/gha-commit.sh` restores it so it is not committed.

2. **Copy/normalize** (`bin/copy_from_Kicad.py`): copies KiCad gerbers into `boards/<prefix><name>-<rev>/frame/` with Altium/JLC-style extensions (`.GTL/.GBL/.GTO/...`, inner `.G2/.G3` renamed to `.G1/.G2`, Edge.Cuts becomes both `.GKO` and `.GM15`). Rewrites the BOM: footprint names mapped through `kicad/footprints.csv`, library prefix stripped, and any component whose value matches `Module-<name>-<rev>` becomes `Module:<name>/<rev>`. Builds the CPL from the positions file, applying per-footprint rotation corrections from `bin/jlc_kicad_tools/cpl_rotations_db.csv`.

3. **Board creation** (`bin/process_board.py`, invoked by the `create_board*.sh` wrappers): the core. It deletes and recreates `boards/<board>/board/`, then:
   - Scans the frame BOM for `Module:<name>/<rev>` rows. For each, looks up the designator's position in the frame CPL, and pulls gerbers/BOM/CPL/schematic from `modules/<name>/<rev>/`. Multiple instances of one module get `_2`, `_3` designator suffixes. Bottom-side modules get layers swapped, rotation inverted and a vertical flip.
   - Writes a `gerbmerge` config + placement file and runs `bin/gerbmerge/gerbmerge` (coordinates converted mm to inch). Inner layers are only merged when `num_layers >= 4` and the module ships `.G1/.G2`.
   - Runs `bin/process_BOM.py` (merges duplicate part numbers, applies the board's `bom_replace_*.csv`), then `bin/convert_BOM_mfr.py` (drops rows with no part number to produce the `-BOM-JLC.csv`).
   - Merges schematic PDFs, renders top/bottom/outline PNGs via `bin/render_gerber.py` (pcb-tools + cairo), merges module VRML into a 3D model and renders components with ModernGL (`bin/render_vrml/`, needs the Xvfb display), composites the board image, and generates the iBOM with `bin/gen_iBOM.py` using footprints from `ibom-data/`.
   - Zips the merged gerbers.

## Data conventions

- **Module layout**: `modules/<name>/<rev>/<name>.{GTL,GBL,GTS,GBS,GTO,GBO,GTP,GKO,GM15,DRL[,G1,G2,GBP]}`, `<name>-BOM.csv`, `<name>-CPL.csv`, `<name>-schematic.pdf`, `<name>-vrml.wrl`, plus `<name>.kicad_mod`/`.kicad_sym` for use in frames. `.GM15` is the module border; `.GKO` is keepout. Module revisions are immutable: a change means a new revision folder and a `CHANGELOG.md` entry. Module-level designators `M<n>` are stripped when merging.
- **Module sources**: only some modules were designed in KiCad; their sources are in `kicad/modules/hellen1-<name>/`. Others came from Altium (`altium.shared/`).
- **BOM replacement CSVs** (`bom_replace_*.csv` in board repos, `global-replace.csv` and `board_id/generated/*.csv` here) are parsed by `process_BOM.py` with a mini preprocessor: `#include file.csv` (relative to the including file), `#define OLD_LCSC NEW_LCSC` (global part-number substitution), `#` comments, and rows `designator[,designator...],comment,footprint,lcsc` that move designators to a new part (a row with only a designator removes it, i.e. DNP). Non-ASCII characters are a hard error. `global-replace.csv` is the shared substitution list that board repos `#include`; most commits here edit it.
- **Board-ID**: each board revision encodes an ID in two resistors (R133/R134 on the mcu module), `id = R1_index*100 + R2_index` over `board_id/resistors.csv`. `board_ids.csv` is the registry; `gen_hellen_board_id.py` appends the next free ID and writes `generated/board_id_<board>-<rev>.csv` for the board's bom_replace to include. The generated header goes into the `libfirmware` submodule. A BOM whose Board-ID resistors are still `?`/`board_id` fails processing until an ID file is included.
- **Naming**: project name is `<BOARD_PREFIX><BOARD_SUFFIX>` (default prefix `hellen`); board name adds `-<rev>`. Board repos are laid out as `boards/<board>/frame/` (input) and `boards/<board>/board/` (generated, committed by CI).

## CI / reusable workflows

`.github/workflows/test-check-all.yaml` runs two jobs on every push/PR: the Docker pipeline test, and a KiCad 10 job that runs `kicad/bin/export.sh` on `tests/` and diffs the resulting frame BOM/CPL against `tests/boards.EXAMPLE`. `create-board.yaml` and `create-board-checkout-with-token.yaml` are `workflow_call` workflows consumed by board repos: they install KiCad 10 from `ppa:kicad/kicad-10.0-releases`, run `kicad/bin/export.sh`, commit `gerber/`, then run the three Docker steps and commit `boards/`. `bin/gha-commit.sh` does the commit and sets `NOCOMMIT`/`YESCOMMIT`. `custom-board-update-hellen-one-reference.yaml` bumps the `hellen-one` submodule pointer in a board repo.

## Gotchas

- Module rotation in frames is only supported in multiples of 90 degrees.
- Board/module KiCad files must stay loadable by KiCad 10; `kicad-cli` also loads the `.kicad_pro` (net classes affect zone fills), so keep it next to the board.
- Scripts assume cwd is the repo root; `create_board.sh` refuses to run without args and is meant to be called from a user script like `create_hellen_board_example.sh`.
- `process_board.py` wipes the whole `board/` output directory on every run.
- `bin/check_all.sh` is interactive (uses `select`) and will prompt when a dependency is missing; in Docker all deps are preinstalled so it passes silently.
