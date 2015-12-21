#!/bin/bash
STAGE=$1
WHERE=$2
ALSO=$3
if ! which appcfg2.py | grep -q appcfg; then
    echo "you dont have it it"
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