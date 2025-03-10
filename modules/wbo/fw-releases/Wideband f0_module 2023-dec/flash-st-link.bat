#cd ../../acclivity/initial-canam-mg1/STM32_Programmer_CLI/bin
st-link_cli -c SWD ur -P wideband_image_with_bl.bin -Rst -Run
rem STM32_Programmer_CLI.exe -c SWD -w "../../../../initial-wbo/Wideband f0_module 2023-dec/wideband_image_with_bl.bin" 0x08000000 --verify --start 0x08000000
