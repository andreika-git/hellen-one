# TL,DR: 

hellen-one is a toolset to produce custom PCBs by merging gerber files of known proven functional modules into trivial _frame_ PCB with mostly just the main vehicle connector. Gerber export and gerber merging happens in the cloud, i.e. on the github server.

Step 1: fork https://github.com/rusefi/hellen-example/ repo to get github actions and meta files [learn about forking](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)

Step 2: make sure github actions are enabled/enable github actions on your fork

Step 3: replace xxx and yyy in ``revision.txt`` with name of your board. By the way we expect kicad files to be placed in the root folder of the repository.

Step 4: create youboard.kicad_pcb from [proven modules](https://github.com/andreika-git/hellen-one/tree/master/modules) using KiCAD

Step 5: push into github to trigger hellen-one gerber _expert_ and gerber _merge_ (that's where the hellen magic happens! for instance gerber export is taken care 
by [export.sh](https://github.com/andreika-git/hellen-one/blob/master/kicad/bin/export.sh) script which github action would invoke _automatically_. Just watch for the yellow circle to turn into a green checkmark.)

Step 6: (sorry rotation only by factor of 90 degrees at this point)

Step 7: order your using fabrication files from 'boards' folder!

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


### FAQ

#### Q: I do not have any files inside hellen-one folder on my PC

A: That's a problem, you have not cloned submodules. See https://stackoverflow.com/questions/3796927/how-do-i-git-clone-a-repo-including-its-submodules



