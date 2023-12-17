# sysconfig_common

Common configs and a setup script to simplify setup of new systems.

Current configs include:

* fish
* git
* tmux
* vi (nvim)

The setup script handles the following linux distributions:

* Arch Linux
* Debian/Ubuntu

## Testing

The test/ directory includes scripts for different distributions to start up a podman container and the run the setup.sh bash script.
Testing is a little bite overstated here because there are no real test cases with automated testing. It's more of a "Setup a test environment and check manually" approach.
