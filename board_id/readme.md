Usage: 

1. Add (an uncommented) line with your board name into test.sh and run the script.
  Don't forget to specify the board revision (each revision should have a unique Board ID).

2. Reference (or copy) the generated file (generated/board_id_xxx.csv) to your project and add '#include board_id_xxx.csv' line to the end of your bom_replace_xxx.csv.

3. Comment out the line since we would not need it anymore.
