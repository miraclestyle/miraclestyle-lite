#!/bin/bash
#
appcfg.py update backend/app.yaml frontend/app.yaml
appcfg.py update_dispatch .
appcfg.py update_indexes backend