##!/bin/bash

set -a
source .env
python3 -m unittest discover tests/
