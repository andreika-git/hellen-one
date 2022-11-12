TL,DR: please see how some of the open source boards are done and follow the pattern!

* https://github.com/rusefi/alphax-4chan
* https://github.com/rusefi/alphax-2chan
* https://github.com/rusefi/hellen154hyundai
* https://github.com/rusefi/hellen121vag
* https://github.com/rusefi/hellen88bmw
* https://github.com/andreika-git/hellen81/
* https://github.com/rusefi/alphax-8chan

This repository contains all scripts and data to create Hellen One boards for [rusEFI](https://github.com/rusefi/rusefi)!

See also https://github.com/rusefi/rusefi/wiki/Hellen-One-Platform

Hellen One is a DIY PnP ECU board construction toolset.

Do you have a car with a rare or non-standard ECU connector pinout?
Do you want a custom DIY ECU but don't want to design it from scratch?

Then Hellen One is for you!

Please see Hellen One Wiki for more info:

https://github.com/andreika-git/hellen-one/wiki

* * *
docker approach like in most of the sample repos is recommended. If you would rather run these scripts locally, you need a 'bash' environment available natively as Unix/Linux shells.
Or, under Windows, you'll need to install a special environment like MSYS2 (https://www.msys2.org) or Cygwin (https://www.cygwin.com)

Please see "create_hellen_board_example.sh" for basic script usage.

* * *

- ./bin 
	* contains scripts needed to compile a ready-to-fab board file, including: Gerber, BOM+CPL files, board images
- ./modules 
	* contains ready-to-use modules
- ./ibom-data
	* contains a customized footprint library used by iBom generator. Don't use these files for your pcb
- ./create_hellen_board_example.sh
	* is a simple example of using Hellen-One scripts for your own board.
