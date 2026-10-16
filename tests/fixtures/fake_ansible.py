#!/usr/bin/env python3
"""Record wrapper invocations without installing dependencies or running Ansible."""
import json
import os
from pathlib import Path
import sys

command_name = Path(sys.argv[0]).name
call = [command_name, *sys.argv[1:]]
log_path = Path(os.environ["SYSCONFIG_TEST_CALLS"])

with log_path.open("a") as output:
    output.write(json.dumps(call) + "\n")
