#!/usr/bin/env bash

run_test_container() {
    local image="$1"
    local tests_directory
    local repository_directory
    local container_name

    tests_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || return
    repository_directory="$(cd -- "$tests_directory/.." && pwd)" || return

    # Include the image tag so different distribution versions have separate containers.
    container_name="${image##*/}"
    container_name="sysconfig-test-${container_name//:/-}"

    podman run \
        --interactive \
        --tty \
        --replace \
        --volume "$repository_directory:/root/working_dir/" \
        --workdir /root/working_dir \
        --name "$container_name" \
        "$image" \
        /usr/bin/bash -c './setup.sh; /usr/bin/fish'
}
