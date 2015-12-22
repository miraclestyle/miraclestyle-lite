#!/bin/bash
STAGE=$1
WHERE=$2
ALSO=$3

if [ $# -lt 2 ]
  then
    echo "Not enough arguments supplied. Min 2 needed, max 3. Example run sh deploy.sh testing all"
    exit
fi

if ! which appcfg.py | grep -q appcfg; then
    echo "You do not have appcfg.py in your path, please add so that appcfg.py => points to path/to/appcfg.py:"
    exit
fi

if ! which python | grep -q python; then
    echo "You do not have python in your path... aborting"
    exit
fi

if ! which git | grep -q git; then
    echo "You do not have git in your path... aborting"
    exit
fi

while true; do
    read -p "You are going to deploy to $STAGE, are you sure? y/n?" yn
    case $yn in
        [Yy]* ) echo "Running to $STAGE..."; break;;
        [Nn]* ) echo "Deploy canceled"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

git add -A
if [ "$WHERE" = "frontend" ]; then
    git commit -m"deploy frontend"
elif [ "$WHERE" = "backend" ]; then
    git commit -m"deploy backend"
elif [ "$WHERE" = "all" ]; then
    git commit -m"deploy all"
fi
git pull

if [ "$WHERE" = "frontend" ] || [ "$WHERE" = "all" ]; then
sh build.sh
fi
git add -A
git commit -m"build"
git push

if [ "$STAGE" = "production" ]; then
    python stager.py production
    echo "Using app.yaml production"
elif [ "$STAGE" = "testing" ]; then
    python stager.py testing
    echo "Using app.yaml testing"
fi

if [ "$WHERE" = "backend" ] || [ "$WHERE" = "all" ]; then
    appcfg.py update backend/app.yaml
else
    echo "Just updating frontend..."
fi

if [ "$WHERE" = "frontend" ] || [ "$WHERE" = "all" ]; then
    appcfg.py update frontend/app.yaml
else
    echo "Just updating backend..."
fi

if [ "$3" = "misc" ]; then
    appcfg.py update_dispatch .
    appcfg.py update_indexes backend
    appcfg.py update_queues backend
fi