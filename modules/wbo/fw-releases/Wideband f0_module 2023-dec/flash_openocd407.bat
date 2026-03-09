@echo off

bin\openocd.exe -f stm32f0discovery.cfg  -c "program wideband_image_with_bl.bin verify reset exit 0x08000000"