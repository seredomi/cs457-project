##!/bin/bash

set -a
source .env
python3 src/client/client.py "$@"