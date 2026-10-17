"""Verify package-file selection with real Ansible and no package installation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROLE_DIRECTORY = REPOSITORY_ROOT / "roles/sysconfig_common"
ANSIBLE_COMMAND = os.environ.get(
    "SYSCONFIG_TEST_ANSIBLE",
    shutil.which("ansible-playbook") or "",
)


@unittest.skipUnless(ANSIBLE_COMMAND, "Install Ansible or set SYSCONFIG_TEST_ANSIBLE")
class PackageSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="sysconfig packages ")
        self.addCleanup(temporary_directory.cleanup)
        self.temporary_directory = Path(temporary_directory.name)

    def run_selection_cases(self, role_directory, cases):
        hosts = {}
        for case_name, case in cases.items():
            hosts[case_name] = {
                "ansible_connection": "local",
                "test_distribution_facts": {
                    "distribution": case["distribution"],
                    "distribution_version": case["version"],
                    "distribution_major_version": case["major_version"],
                },
                "expected_package": case["expected_package"],
                "expected_package_count": case.get("expected_package_count"),
            }

        inventory_file = self.temporary_directory / "inventory.json"
        inventory_file.write_text(json.dumps({"all": {"hosts": hosts}}, indent=2))
        playbook = [{
            "name": "Select packages without configuring the system",
            "hosts": "all",
            "gather_facts": False,
            "tasks": [
                {
                    "name": "Supply the distribution facts for this test case",
                    "ansible.builtin.set_fact": {
                        "ansible_facts": "{{ test_distribution_facts }}",
                    },
                },
                {
                    "name": "Run the role's package-file loader",
                    "ansible.builtin.include_role": {
                        "name": str(role_directory),
                        "tasks_from": "load_packages",
                    },
                },
                {
                    "name": "Check the selected package list",
                    "ansible.builtin.assert": {
                        "that": [
                            "expected_package in sysconfig_distribution.packages",
                            "expected_package_count == none or sysconfig_distribution.packages | length == expected_package_count",
                        ],
                    },
                },
            ],
        }]
        playbook_file = self.temporary_directory / "select.json"
        playbook_file.write_text(json.dumps(playbook, indent=2))
        environment = {
            **os.environ,
            "ANSIBLE_CONFIG": str(REPOSITORY_ROOT / "ansible/ansible.cfg"),
        }
        return subprocess.run(
            [ANSIBLE_COMMAND, "-i", str(inventory_file), str(playbook_file)],
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_supported_distribution_package_lists(self):
        cases = {
            "ubuntu_jammy": {
                "distribution": "Ubuntu",
                "version": "22.04",
                "major_version": "22",
                "expected_package": "tldr",
            },
            "ubuntu_noble": {
                "distribution": "Ubuntu",
                "version": "24.04",
                "major_version": "24",
                "expected_package": "tealdeer",
            },
            "ubuntu_resolute": {
                "distribution": "Ubuntu",
                "version": "26.04",
                "major_version": "26",
                "expected_package": "tealdeer",
            },
            "debian_bookworm": {
                "distribution": "Debian",
                "version": "12.9",
                "major_version": "12",
                "expected_package": "tldr",
            },
            "debian_trixie": {
                "distribution": "Debian",
                "version": "13.1",
                "major_version": "13",
                "expected_package": "tealdeer",
            },
            "arch": {
                "distribution": "Archlinux",
                "version": "rolling",
                "major_version": "rolling",
                "expected_package": "tldr",
            },
        }

        result = self.run_selection_cases(ROLE_DIRECTORY, cases)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prefers_full_version_then_major_version_then_distribution(self):
        fixture_role = self.temporary_directory / "fixture_role"
        task_directory = fixture_role / "tasks"
        package_directory = fixture_role / "vars/packages"
        task_directory.mkdir(parents=True)
        package_directory.mkdir(parents=True)
        shutil.copyfile(
            ROLE_DIRECTORY / "tasks/load_packages.yml",
            task_directory / "load_packages.yml",
        )
        fixture_packages = {
            "Example-24.04.yml": "exact_version_package",
            "Example-24.yml": "major_version_package",
            "Example.yml": "distribution_package",
        }
        for filename, package in fixture_packages.items():
            (package_directory / filename).write_text(f"packages:\n  - {package}\n")

        cases = {
            "exact_version": {
                "distribution": "Example",
                "version": "24.04",
                "major_version": "24",
                "expected_package": "exact_version_package",
                "expected_package_count": 1,
            },
            "major_version": {
                "distribution": "Example",
                "version": "24.10",
                "major_version": "24",
                "expected_package": "major_version_package",
                "expected_package_count": 1,
            },
            "distribution": {
                "distribution": "Example",
                "version": "25.04",
                "major_version": "25",
                "expected_package": "distribution_package",
                "expected_package_count": 1,
            },
        }

        result = self.run_selection_cases(fixture_role, cases)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_distribution_file_fails(self):
        cases = {
            "unsupported": {
                "distribution": "Unsupported",
                "version": "1.0",
                "major_version": "1",
                "expected_package": "unused",
            },
        }

        result = self.run_selection_cases(ROLE_DIRECTORY, cases)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No file was found", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
