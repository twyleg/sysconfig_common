#!/bin/sh
set -eu

plugin_directory="$(dirname -- "$0")"
mkdir -p "$plugin_directory/bin"
printf 'fixture' > "$plugin_directory/bin/fzf"
chmod +x "$plugin_directory/bin/fzf"
