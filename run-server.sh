##!/bin/bash

set -a
source .env
python3 src/server/server.py "$@"
