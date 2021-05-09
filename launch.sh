#!/bin/bash

set -e;

DIR=$(dirname $(realpath $0));

if [[ -z "$DIR" ]];
then
    echo Could not determine project directory;
    exit 1;
fi

cd $DIR;
source ./venv/bin/activate
./src/everything.py
