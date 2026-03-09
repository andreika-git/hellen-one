@echo off

bin\openocd.exe -f stm32f0discovery.cfg  -c "init; halt; stm32f1x unlock 0; program wideband_image_with_bl.bin verify exit 0x08000000"