#!/bin/bash
#
git pull
sh build.sh
git add -A
git commit -m"deploy"
git push
appcfg.py update backend/app.yaml
sleep 5
echo "Waiting for frontend deployment... 5s"
sleep 5
echo "Waiting for frontend deployment... 10s"
sleep 5
echo "Waiting for frontend deployment... 15s"
appcfg.py update frontend/app.yaml
appcfg.py update_dispatch .
appcfg.py update_indexes backend