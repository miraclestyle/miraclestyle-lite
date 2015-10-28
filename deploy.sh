#!/bin/bash
#
git pull
sh build.sh
git add -A
git commit -m"deploy"
git push
appcfg.py update backend/app.yaml frontend/app.yaml --no-precompilation
appcfg.py update_dispatch .
appcfg.py update_indexes backend