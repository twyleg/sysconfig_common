#!/usr/bin/env bash
# Bootstrap and invoke Ansible; all system configuration lives in the role.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
bootstrap_directory="${XDG_CACHE_HOME:-$HOME/.cache}/sysconfig_common/ansible-venv"
ansible_playbook_command=''
ansible_galaxy_command=''

show_help() {
    echo 'Usage: setup.sh [ANSIBLE_PLAYBOOK_ARGS ...]'
    echo 'Bootstraps Ansible if absent, then runs the local sysconfig role.'
    echo 'Use --check --diff to preview, or --ask-become-pass if sudo requires a password.'
}

run_as_root() {
    if [[ $(id -u) == 0 ]]; then
        "$@"
    else
        sudo -- "$@"
    fi
}

install_bootstrap_dependencies() {
    source /etc/os-release

    case "$ID" in
        ubuntu|debian|tuxedo)
            run_as_root apt-get update
            run_as_root apt-get install -y \
                python3 \
                python3-venv \
                ca-certificates
            ;;
        arch)
            run_as_root pacman -Sy --needed --noconfirm \
                python \
                ca-certificates
            ;;
        *)
            echo "Unsupported bootstrap distribution: $ID" >&2
            return 1
            ;;
    esac
}

create_ansible_environment() {
    if [[ -x "$bootstrap_directory/bin/ansible-playbook" ]]; then
        return 0
    fi

    install_bootstrap_dependencies

    python3 -m venv "$bootstrap_directory"
    "$bootstrap_directory/bin/python" -m pip install \
        -r "$SCRIPT_DIR/ansible/requirements.txt"
}

find_or_install_ansible() {
    if command -v ansible-playbook >/dev/null 2>&1; then
        ansible_playbook_command="$(command -v ansible-playbook)"
        ansible_galaxy_command="$(command -v ansible-galaxy)"
    else
        create_ansible_environment
        ansible_playbook_command="$bootstrap_directory/bin/ansible-playbook"
        ansible_galaxy_command="$bootstrap_directory/bin/ansible-galaxy"
    fi
}

install_collection_dependencies() {
    # Install beside the playbook so other projects keep their own collections.
    "$ansible_galaxy_command" collection install \
        -r "$SCRIPT_DIR/ansible/requirements.yml" \
        -p "$SCRIPT_DIR/ansible/collections"
}

run_local_playbook() {
    local user_name

    user_name="$(id -un)"

    # Respect an explicit caller setting, otherwise use the standalone config.
    export ANSIBLE_CONFIG="${ANSIBLE_CONFIG:-$SCRIPT_DIR/ansible/ansible.cfg}"

    exec "$ansible_playbook_command" \
        -i localhost, \
        "$SCRIPT_DIR/ansible/setup.yml" \
        -e "sysconfig_user=$user_name" \
        "$@"
}

main() {
    if [[ ${1:-} == --help || ${1:-} == -h ]]; then
        show_help
        exit 0
    fi

    find_or_install_ansible
    install_collection_dependencies
    run_local_playbook "$@"
}

main "$@"
