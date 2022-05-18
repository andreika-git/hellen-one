# run virtual framebuffer
Xvfb :99 -screen 0 640x480x24 -nolisten tcp &

# run all dependency checks
./bin/check_all.sh

cd tests

# execute step2
./step2_copy_hellen1test.sh

# execute step3
./step3_create_hellen1test.sh 
