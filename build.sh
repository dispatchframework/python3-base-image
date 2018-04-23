#!/bin/sh
set -e -x

cd $(dirname $0)

docker build -t dispatchframework/python3-base:0.0.3 .
