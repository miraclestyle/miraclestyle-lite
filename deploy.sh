#!/bin/bash
#
git pull

if [ "$1" = "frontend" ] || ["$1" = "all"]
then
sh build.sh
fi

git add -A
git commit -m"deploy"
git push

if [ "$1" = "backend" ] || ["$1" = "all"]
then
    appcfg.py update backend/app.yaml
else
    echo "Just updating backend..."
fi

if [ "$1" = "frontend" ] || ["$1" = "all"]
then
    appcfg.py update frontend/app.yaml
else
    echo "Just updating frontend..."
fi

if [ "$2" = "index" ]
then
    appcfg.py update_dispatch .
    appcfg.py update_indexes backend
fi