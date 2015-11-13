#!/bin/bash
#
git pull
sh build.sh
git add -A
git commit -m"deploy"
git push
appcfg.py update backend/app.yaml
appcfg.py update frontend/app.yaml
appcfg.py update_dispatch .
appcfg.py update_indexes backend