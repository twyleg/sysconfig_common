#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || exit
source "$SCRIPT_DIR/common.sh" || exit

run_test_container "docker.io/library/debian:latest"
