#!/bin/bash
function default_deploy {
   dev_appserver.py backend/app.yaml frontend/app.yaml dispatch.yaml  --port=9982 --require_indexes=yes --log_level=debug $@
}

function default_wipe_deploy {
   dev_appserver.py backend/app.yaml frontend/app.yaml dispatch.yaml  --port=9982 --require_indexes=yes --log_level=debug --clear_datastore=yes $@
}

function myself_deploy {
   dev_appserver.py backend/app.yaml frontend/app.yaml dispatch.yaml  $@
}
PS3='Dev server config: '
options=("default server startup" "default server startup + data whipe" "start server with your own arguments" "quit")
select opt in "${options[@]}"
do
    case $opt in
        "default server startup")
            default_deploy
            break;;
        "default server startup + data whipe")
            default_wipe_deploy
            break;;
        "start server with your own arguments")
            myself_deploy
            break;;
        "quit")
            break
            ;;
        *) echo invalid option;;
    esac
done