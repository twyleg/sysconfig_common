#!/usr/bin/env bash
# Bootstrap and invoke Ansible; all system configuration lives in the role.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ ${1:-} == --help || ${1:-} == -h ]]; then
    echo 'Usage: setup.sh [ANSIBLE_PLAYBOOK_ARGS ...]'
    echo 'Bootstraps Ansible if absent, then runs the local sysconfig role.'
    echo 'Use --check --diff to preview, or --ask-become-pass if sudo requires a password.'
    exit 0
fi
as_root() {
    if [[ $(id -u) == 0 ]]; then "$@"; else sudo -- "$@"; fi
}
if command -v ansible-playbook >/dev/null 2>&1; then
    ansible_playbook="$(command -v ansible-playbook)"
    ansible_galaxy="$(command -v ansible-galaxy)"
else
    bootstrap_dir="${XDG_CACHE_HOME:-$HOME/.cache}/sysconfig_common/ansible-venv"
    if [[ ! -x $bootstrap_dir/bin/ansible-playbook ]]; then
        source /etc/os-release
        case "$ID" in
            ubuntu|debian|tuxedo)
                as_root apt-get update
                as_root apt-get install -y python3 python3-venv ca-certificates ;;
            arch)
                as_root pacman -Sy --needed --noconfirm python ca-certificates ;;
            *) echo "Unsupported bootstrap distribution: $ID" >&2; exit 1 ;;
        esac
        python3 -m venv "$bootstrap_dir"
        "$bootstrap_dir/bin/python" -m pip install -r "$SCRIPT_DIR/ansible/requirements.txt"
    fi
    ansible_playbook="$bootstrap_dir/bin/ansible-playbook"
    ansible_galaxy="$bootstrap_dir/bin/ansible-galaxy"
fi
# Install alongside the playbook so other projects' collection versions are unaffected.
"$ansible_galaxy" collection install -r "$SCRIPT_DIR/ansible/requirements.yml" -p "$SCRIPT_DIR/ansible/collections"
export ANSIBLE_CONFIG="${ANSIBLE_CONFIG:-$SCRIPT_DIR/ansible/ansible.cfg}"
exec "$ansible_playbook" -i localhost, "$SCRIPT_DIR/ansible/setup.yml" \
    -e "sysconfig_user=$(id -un)" "$@"
