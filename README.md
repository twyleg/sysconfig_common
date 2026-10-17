# sysconfig_common: native Ansible implementation

The setup logic lives in `roles/sysconfig_common`. Configuration files remain
under `conf/`; Vim plugin declarations are read from `conf/vim/vimrc`.

## Standalone setup

```bash
./setup.sh --ask-become-pass
./setup.sh --check --diff
```

`setup.sh` only bootstraps/locates Ansible, installs the collection requirement,
and runs `ansible/setup.yml` against localhost. It contains no duplicate package,
link, plugin, or shell setup. If Ansible is absent, bootstrap installs Python/venv
prerequisites through apt/pacman and creates a private environment in
`${XDG_CACHE_HOME:-~/.cache}/sysconfig_common/ansible-venv`. Python >=3.10 and
Ansible >=2.16 are required. Bootstrap dependency installation still takes place
when `--check` is passed; check mode applies to the role afterward.

If you already have compatible Ansible, install `ansible/requirements.yml` and
include `roles/sysconfig_common` directly from another playbook. The wrapper is
not involved in that path. It honors an explicit `ANSIBLE_CONFIG`; otherwise it
uses the standalone configuration beside its playbook.

## Role settings

| Variable | Default / purpose |
| --- | --- |
| `sysconfig_user` | Connection user, or gathered local user |
| `sysconfig_home` | Target user's home from passwd |
| `sysconfig_source_dir` | `<home>/dev/sysconfig_common`; managed config snapshot |
| `sysconfig_data_home` | Target environment's XDG data home, or `<home>/.local/share` |
| `sysconfig_manage_system` | `true`; packages, editor alternatives/aliases, login shell |
| `sysconfig_install_plugins` | `true`; vim-plug, plugin repositories, fzf binary |

Existing user configuration paths are preserved; missing links point to the
managed configuration snapshot. Keep that directory after setup. Plugins are
cloned only when missing (`update: false`). The fzf installer uses a `creates`
condition; all other setup operations use Ansible modules. The role changes the
user's login shell to Fish and selects Neovim as the editor on normal full runs.

For a configuration-only preview:

```bash
./setup.sh -e sysconfig_manage_system=false --check --diff
```

## Distribution package lists

Package lists live in `roles/sysconfig_common/vars/packages/`. Each file defines
one `packages` list. The role loads the first existing file in this order:

1. `<distribution>-<full-version>.yml`, for example `Ubuntu-22.04.yml`.
2. `<distribution>-<major-version>.yml`, for example `Debian-13.yml`.
3. `<distribution>.yml`, for example `Ubuntu.yml` or `Archlinux.yml`.

Names match Ansible's gathered distribution facts, including capitalization.
Only one file is loaded; package lists are not merged. If no matching file
exists, setup fails instead of guessing which packages to install. Package
selection is skipped when `sysconfig_manage_system=false`.

Both apt and pacman use the selected `sysconfig_distribution.packages` list.
General settings remain in `defaults/main.yml`.

The Debian and Arch fallback lists retain `tldr`. The Ubuntu fallback uses
`tealdeer`, with `tldr` selected for Ubuntu 22.04. Debian 13 selects `tealdeer`
because [Debian removed tldr in that release](https://www.debian.org/releases/trixie/release-notes/issues.en.html#noteworthy-obsolete-packages).
See also the Ubuntu package listings for [Jammy tldr](https://packages.ubuntu.com/jammy/tldr)
and [tealdeer](https://packages.ubuntu.com/tealdeer).

## Tests

The role creates plugin checkout directories before invoking the Git module.
This also supports container-mounted submodules/worktrees whose `.git` file
points to parent-repository metadata outside the mount: Git's initial remote
checks run from the plugin directory instead of the mounted source checkout.

```bash
python3 -m unittest discover -s tests -v
```

Install PyYAML and Ansible to run the integration test. It uses temporary homes,
real Git and Ansible, local HTTP/plugin fixtures, and disables system changes.
It checks initial convergence, a zero-change second run, preservation of existing
files, check-mode drift reporting, and plugin cloning from a checkout with
unavailable Git metadata. Set `SYSCONFIG_TEST_ANSIBLE` to a specific
ansible-playbook executable if needed. Collection requirements must be installed.
Container smoke scripts exercise full setup on Ubuntu Jammy, Noble, Resolute,
Ubuntu latest, Debian latest, and Arch. Podman must be installed.
Each launcher sources `tests/common.sh`, then calls `run_test_container` with
its image and forwards its command-line options.

```bash
./tests/test_ubuntu_22.04_jammy.sh                # Run setup and remove the container on exit.
./tests/test_ubuntu_22.04_jammy.sh --fish         # Open Fish after successful setup; remove on shell exit.
./tests/test_ubuntu_22.04_jammy.sh --keep         # Retain the stopped container after setup.
./tests/test_ubuntu_22.04_jammy.sh --fish --keep  # Open Fish and retain the container on shell exit.
```

The helper mounts this repository and runs `setup.sh`. Automatic removal also
applies if setup fails, unless `--keep` is set. Each run replaces the previous
container for that image, including one retained with `--keep`; different images
use separate container names.
