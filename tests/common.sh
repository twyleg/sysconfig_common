#!/usr/bin/env bash

run_test_container() {
    local image="$1"
    shift

    local start_shell=false
    local keep_container=false
    local tests_directory
    local repository_directory
    local container_name
    # Package configuration must stay unattended even when the container has a terminal.
    local container_command='DEBIAN_FRONTEND=noninteractive ./setup.sh'
    local -a podman_options=(--replace)

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --interactive)
                start_shell=true
                ;;
            --keep)
                keep_container=true
                ;;
            *)
                printf 'Unknown option: %s\nUsage: %s [--interactive] [--keep]\n' "$1" "$0" >&2
                return 2
                ;;
        esac
        shift
    done

    if [[ "$keep_container" == false ]]; then
        podman_options+=(--rm)
    fi

    if [[ "$start_shell" == true ]]; then
        podman_options+=(--interactive --tty)
        container_command+=' && exec /usr/bin/fish'
    fi

    tests_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || return
    repository_directory="$(cd -- "$tests_directory/.." && pwd)" || return

    # Include the image tag so different distribution versions have separate containers.
    container_name="${image##*/}"
    container_name="sysconfig-test-${container_name//:/-}"

    podman run \
        "${podman_options[@]}" \
        --volume "$repository_directory:/root/working_dir/" \
        --workdir /root/working_dir \
        --name "$container_name" \
        "$image" \
        /usr/bin/bash -c "$container_command"
}
