#!/bin/bash
git add -A
if [ "$1" = "frontend" ]; then
    git commit -m"deploy frontend"
elif [ "$1" = "backend" ]; then
    git commit -m"deploy backend"
elif [ "$1" = "all" ]; then
    git commit -m"deploy all"
fi
git pull

if [ "$1" = "frontend" ] || [ "$1" = "all" ]; then
sh build.sh
fi
git add -A
git commit -m"build"
git push

if [ "$1" = "backend" ] || [ "$1" = "all" ]; then
    appcfg.py update backend/app.yaml --noauth_local_webserver
else
    echo "Just updating frontend..."
fi

if [ "$1" = "frontend" ] || [ "$1" = "all" ]; then
    appcfg.py update frontend/app.yaml --noauth_local_webserver
else
    echo "Just updating backend..."
fi

if [ "$2" = "index" ]; then
    appcfg.py update_dispatch . --noauth_local_webserver
    appcfg.py update_indexes backend --noauth_local_webserver
fi