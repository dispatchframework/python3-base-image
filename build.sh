#!/bin/sh
set -e -x

: ${DOCKER_REGISTRY:="dispatchframework"}

cd $(dirname $0)

FUNKY_VERSION=${1}

IMAGE=${DOCKER_REGISTRY}/python3-base:$(cat version.txt)
docker build --no-cache -t ${IMAGE} --build-arg=FUNKY_VERSION=${FUNKY_VERSION} .
if [ -n "$PUSH" ]; then
    docker push ${IMAGE}
fi
