#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )


CONTAINER_NAME=arch_test

podman rm -f $CONTAINER_NAME

podman run \
    -it \
    -v $SCRIPT_DIR/..:/root/working_dir/ \
    -w /root/working_dir \
    --name $CONTAINER_NAME \
    docker.io/library/debian:latest \
    /usr/bin/bash -c "./setup.sh;/usr/bin/fish"
