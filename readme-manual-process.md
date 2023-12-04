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
