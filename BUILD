For frontend builds requirements are:

python2.7
node
npm
gulp

how to install on ubuntu with apt-get

sudo apt-get install nodejs
sudo ln -s `which nodejs` /usr/bin/node
sudo apt-get install npm
npm install gulp -g

if you do not have python 2.7

sudo apt-get install python

go to frontend/.node
npm install


sh deploy.sh arg1 arg2 arg3
arg1 => possible choices are "production" and "testing"
arg2 => possible choices are "all" "frontend" "backend"
arg3 => message for git commit
arg4 => possible choices are "misc"

first argument changes app.yaml to production or testing
second argument deploys to frontend, backend or both
third argument will be used as a commit message
fourth argument will also upload dispatch, taskqueue entries, indexes

so running
sh deploy.sh production all "fix stuff" misc will deploy to production backend and frontend along with other .yaml files
sh deploy.sh testing all "fix stuff again" misc will deploy to testing backend and frontend along with other .yaml files

etc...
along with other things, script will commit to bitbucket and perform build that will compile all static files accordingly