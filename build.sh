#!/bin/bash
#
cd frontend
echo 'Compile statics into dist folder...'
python settings.py $@
echo 'Copying files to cordova...'
cp -rf client/dist client/.apps/cordova/www/client/dist
echo 'Copying files to chrome...'
cp -rf client/dist client/.apps/chrome/client/dist
echo 'Done'
cd ..