#! /bin/bash

mkdir -p pi_env
cp requirements.txt pi_env/
cd pi_env

docker run --platform linux/arm64 -v $(pwd):/workspace -it python:3.11-slim /bin/bash -c '
  cd workspace
  python -m venv env
  ls
  source env/bin/activate
  pip install -r requirements.txt
  pip download -d wheels -r requirements.txt
  exit
'
