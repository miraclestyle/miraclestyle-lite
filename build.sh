#!/bin/bash
#
cd frontend
echo 'Compile statics into dist folder...'
python settings.py $@
echo 'Completed distribution...'
echo 'Preparing files for google app...'
# todo, actually make logic for google app
echo 'Done'
cd ..