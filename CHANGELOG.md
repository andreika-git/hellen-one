# Changelog

All notable changes will be documented in this file.

## KiCad 10 toolset
  - Frame export (kicad/bin/export.sh) and the create-board GitHub workflows now require KiCad 10
  - No more pcbnew Python scripting: zones are refilled by 'kicad-cli pcb export gerbers --check-zones', VRML by 'kicad-cli pcb export vrml'; the board file is no longer modified during export
  - hellen-one-kicad-bom-plugin.py uses the kicad_netlist_reader shipped with KiCad and honours the native DNP attribute (in addition to MyComment=DNP)
  - CI runs the KiCad export on the test frame (tests/) with KiCad 10

## knock-0.2
  - now double-sided assembly and smaller dimentions

## vr-discrete-0.2
  - now double-sided assembly and smaller dimentions

## wbo-0.4
  - now integrated CAN transiever
  - now double-sided assembly and smaller dimentions

## mcu-0.7 and mcu144-0.7
  - mcu and mcu144 modules are now 4-layer (4-layer frames required!)
  - Changed Kicad symbol (pin names renamed + added EXTI numbers)
  - 5 more pins exposed (IO5..IO9)

## ign8-0.2
  - Fixed module border misalignment

## mcu-0.6 and mcu144-0.6
  - Added C133, R133, R134 for Board-ID
  - Changed L101 (0805) to F101 (1206)

## Altium Designer (AD) shared files and Board-ID support
  - altium.shared folder
  - board_id folder

## output-0.3
  - TC4427 output protection: Added R312, R316, C301, C302
  - MCU protection from TC4427 failure: Added R311, R314; Changed R307, R308
  - Changed C300 C0805->C0603 (same capacity & voltage rating)
  - Added silkscreen for +12V/+5V supply voltage selection jumpers for push-pull outputs

## added support for custom board prefixes

## added support for bottom-placed modules (beta-version)

## wbo-0.3
  - Added Q601 in TO-220 (TH package) in case if Q600 is not in stock
  - Changed one of the pads in the module footprint: remove one trace from the parent frame and re-fill

## mcu-0.5 and mcu144-0.5
 - Added R132 (5.1k 0603)
 - Changed "MCP6004T-I/ST" to "MCP6004"
 - Changed "8.0 MHz" to "20 MHz" (C112566)
