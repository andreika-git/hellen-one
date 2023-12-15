# TL,DR: 

hellen-one is a toolset to produce custom PCBs by merging gerber files of known proven functional modules into trivial _frame_ PCB with mostly just the main vehicle connector.

* fork https://github.com/rusefi/hellen-example/ repo to get github actions and meta files
* replace xxx and yyy in ``revision.txt`` with name of your board
* create youboard.kicad_pcb from [proven modules](https://github.com/andreika-git/hellen-one/tree/master/modules) using KiCAD 6 or 7
* push into github to trigger hellen-one gerber expert and gerber merge (that's where the hellen magic happens! for instance gerber export is taken care by [export.sh](https://github.com/andreika-git/hellen-one/blob/master/kicad/bin/export.sh) script which github action would invoke _automatically_. Just watch for the yellow circle to turn into a green checkmark.)
* order your using fabrication files from 'boards' folder!

Please see how some of the open source boards are done and follow the pattern:

## Open Source Boards

* https://github.com/rusefi/alphax-4chan
* https://github.com/rusefi/uaefi
* https://github.com/rusefi/alphax-2chan
* https://github.com/rusefi/hellen154hyundai
* https://github.com/rusefi/hellen121vag
* https://github.com/rusefi/hellen88bmw
* https://github.com/andreika-git/hellen81/

This repository contains all scripts and data to create Hellen One boards for [rusEFI](https://github.com/rusefi/rusefi)!

See also https://github.com/rusefi/rusefi/wiki/Hellen-One-Platform

Hellen One is a DIY PnP ECU board construction toolset.

Do you have a car with a rare or non-standard ECU connector pinout?
Do you want a custom DIY ECU but don't want to design it from scratch?

Then Hellen One is for you!

Please see Hellen One Wiki for more info:

https://github.com/andreika-git/hellen-one/wiki

