#!/bin/bash
#
cd frontend
echo 'Compile statics into dist folder...'
python settings.py $@
echo 'Completed distribution...'
echo 'Done'
cd ..