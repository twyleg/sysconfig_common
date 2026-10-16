"""Exercise the native role using temporary homes and local plugin fixtures."""
import functools
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRECTORY = REPOSITORY_ROOT / "tests/fixtures"
ANSIBLE_COMMAND = os.environ.get(
    "SYSCONFIG_TEST_ANSIBLE",
    shutil.which("ansible-playbook") or "",
)


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *arguments):
        pass


@unittest.skipUnless(ANSIBLE_COMMAND, "Install Ansible or set SYSCONFIG_TEST_ANSIBLE")
class NativeSetupTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="native sysconfig review ")
        self.addCleanup(temporary_directory.cleanup)
        self.temporary_directory = Path(temporary_directory.name)

        self.home_directory = self.temporary_directory / "user home"
        self.home_directory.mkdir()
        self.git_configuration = self.home_directory / ".gitconfig"
        self.git_configuration.write_text("keep my configuration\n")

        vim_configuration = (REPOSITORY_ROOT / "conf/vim/vimrc").read_text()
        self.plugin_repositories = re.findall(
            r"^Plug '([^']+)'", vim_configuration, re.MULTILINE
        )
        self.create_plugin_repositories()
        self.start_download_server()
        self.create_playbook_variables()

    def run_git(self, working_directory, *arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=working_directory,
            check=True,
            capture_output=True,
        )

    def create_plugin_repositories(self):
        source_repository = self.temporary_directory / "plugin source"
        source_repository.mkdir()
        (source_repository / "README").write_text("local plugin fixture\n")
        shutil.copyfile(
            FIXTURE_DIRECTORY / "fzf-install.sh", source_repository / "install"
        )
        (source_repository / "install").chmod(0o755)

        self.run_git(source_repository, "init")
        self.run_git(source_repository, "add", ".")
        self.run_git(
            source_repository,
            "-c", "user.name=Fixture",
            "-c", "user.email=fixture@local",
            "commit", "-m", "fixture",
        )

        self.remote_directory = self.temporary_directory / "remote repositories"
        for repository in self.plugin_repositories:
            destination = self.remote_directory / (repository + ".git")
            destination.parent.mkdir(parents=True, exist_ok=True)
            self.run_git(
                source_repository,
                "clone", "--bare", str(source_repository), str(destination),
            )

    def start_download_server(self):
        web_directory = self.temporary_directory / "web"
        web_directory.mkdir()
        (web_directory / "plug.vim").write_text("fixture vim-plug\n")

        request_handler = functools.partial(
            QuietHTTPHandler, directory=str(web_directory)
        )
        self.download_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), request_handler
        )
        self.server_thread = threading.Thread(
            target=self.download_server.serve_forever, daemon=True
        )
        self.server_thread.start()
        self.addCleanup(self.stop_download_server)

    def stop_download_server(self):
        self.download_server.shutdown()
        self.download_server.server_close()
        self.server_thread.join()

    def create_playbook_variables(self):
        variables = {
            "sysconfig_manage_system": False,
            "sysconfig_home": str(self.home_directory),
            "sysconfig_data_home": str(self.home_directory / "data"),
            # Encode spaces in the local Git URL while retaining spaces in the
            # target home path to exercise path handling in the role itself.
            "sysconfig_plugin_base_url": self.remote_directory.as_uri(),
            "sysconfig_vim_plug_url": (
                f"http://127.0.0.1:{self.download_server.server_port}/plug.vim"
            ),
        }
        self.variables_file = self.temporary_directory / "vars.json"
        self.variables_file.write_text(json.dumps(variables, indent=2))

    def run_playbook(self, *additional_arguments):
        command = [
            ANSIBLE_COMMAND,
            "-i", "localhost,",
            str(REPOSITORY_ROOT / "ansible/setup.yml"),
            "-e", "@" + str(self.variables_file),
            *additional_arguments,
        ]
        environment = {
            **os.environ,
            "ANSIBLE_CONFIG": str(REPOSITORY_ROOT / "ansible/ansible.cfg"),
        }
        result = subprocess.run(
            command,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_converges_preserves_files_and_supports_check_mode(self):
        self.run_playbook()

        self.assertEqual(self.git_configuration.read_text(), "keep my configuration\n")
        tmux_link = self.home_directory / ".tmux.conf"
        expected_configuration = (
            self.home_directory / "dev/sysconfig_common/conf/tmux/tmux.conf"
        )
        self.assertEqual(tmux_link.resolve(), expected_configuration)

        for repository in self.plugin_repositories:
            plugin_name = repository.rsplit("/", 1)[-1]
            git_directory = self.home_directory / ".vim/plugged" / plugin_name / ".git"
            self.assertTrue(git_directory.is_dir())

        fzf_binary = self.home_directory / ".vim/plugged/fzf/bin/fzf"
        self.assertTrue(os.access(fzf_binary, os.X_OK))

        second_run = self.run_playbook()
        self.assertRegex(second_run.stdout, r"changed=0\s")

        tmux_link.unlink()
        preview = self.run_playbook("--check", "--diff")
        self.assertFalse(tmux_link.exists())
        self.assertRegex(preview.stdout, r"changed=[1-9]")


@unittest.skipUnless(ANSIBLE_COMMAND, "Install Ansible or set SYSCONFIG_TEST_ANSIBLE")
class ContainerCheckoutTests(unittest.TestCase):
    def test_clones_plugins_when_checkout_git_metadata_is_not_mounted(self):
        with tempfile.TemporaryDirectory(prefix="mounted sysconfig checkout ") as temporary:
            temporary_directory = Path(temporary)
            mounted_checkout = temporary_directory / "working_dir"
            ansible_directory = mounted_checkout / "ansible"
            ansible_directory.mkdir(parents=True)

            # Submodules and Git worktrees use a .git file pointing elsewhere.
            # A container that mounts only the checkout cannot access that path.
            git_pointer = mounted_checkout / ".git"
            git_pointer.write_text("gitdir: /not-mounted/parent/repository.git\n")
            shutil.copyfile(REPOSITORY_ROOT / "setup.sh", mounted_checkout / "setup.sh")
            (mounted_checkout / "setup.sh").chmod(0o755)

            plugin_sources = temporary_directory / "plugin sources"
            source_repository = plugin_sources / "fixture/example.git"
            source_repository.mkdir(parents=True)
            (source_repository / "README").write_text("local plugin fixture\n")
            git_commands = [
                ["git", "init"],
                ["git", "add", "."],
                [
                    "git", "-c", "user.name=Fixture", "-c", "user.email=fixture@local",
                    "commit", "-m", "fixture",
                ],
            ]
            for command in git_commands:
                subprocess.run(
                    command, cwd=source_repository, check=True, capture_output=True
                )

            target_home = temporary_directory / "target home"
            plugin_destination = target_home / ".vim/plugged/example"
            plugin_tasks_path = (
                REPOSITORY_ROOT / "roles/sysconfig_common/tasks/plugins.yml"
            )
            plugin_tasks = yaml.safe_load(plugin_tasks_path.read_text())
            clone_task_names = {
                "Create Vim plugin checkout directories",
                "Install missing Vim plugin repositories",
            }
            clone_tasks = [
                task for task in plugin_tasks if task["name"] in clone_task_names
            ]
            self.assertEqual(len(clone_tasks), 2)

            playbook = [{
                "name": "Clone a plugin from a container-mounted checkout",
                "hosts": "localhost",
                "connection": "local",
                "gather_facts": False,
                "vars": {
                    "ansible_python_interpreter": sys.executable,
                    "sysconfig_home": str(target_home),
                    "sysconfig_plugin_base_url": plugin_sources.as_uri(),
                    "sysconfig_vim_plugins": ["fixture/example"],
                },
                "tasks": clone_tasks,
            }]
            # Use JSON, which Ansible accepts as YAML, to write the test playbook.
            (ansible_directory / "setup.yml").write_text(json.dumps(playbook, indent=2))
            (ansible_directory / "ansible.cfg").write_text(
                "[defaults]\nstdout_callback = default\n"
            )
            (ansible_directory / "requirements.yml").write_text("collections: []\n")

            command_directory = temporary_directory / "commands"
            command_directory.mkdir()
            (command_directory / "ansible-playbook").symlink_to(
                Path(ANSIBLE_COMMAND).resolve()
            )
            galaxy_command = command_directory / "ansible-galaxy"
            shutil.copyfile(FIXTURE_DIRECTORY / "fake_ansible.py", galaxy_command)
            galaxy_command.chmod(0o755)

            environment = {
                **os.environ,
                "PATH": str(command_directory) + ":" + os.environ["PATH"],
                "ANSIBLE_CONFIG": str(ansible_directory / "ansible.cfg"),
                "SYSCONFIG_TEST_CALLS": str(temporary_directory / "calls.jsonl"),
            }
            result = subprocess.run(
                [str(mounted_checkout / "setup.sh")],
                cwd=mounted_checkout,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((plugin_destination / ".git").is_dir())
            self.assertEqual(
                git_pointer.read_text(), "gitdir: /not-mounted/parent/repository.git\n"
            )


class WrapperTests(unittest.TestCase):
    def test_forwards_arguments_and_uses_the_shared_role_playbook(self):
        with tempfile.TemporaryDirectory(prefix="sysconfig wrapper ") as temporary:
            command_directory = Path(temporary)
            call_log = command_directory / "calls.jsonl"

            for command_name in ("ansible-playbook", "ansible-galaxy"):
                command_path = command_directory / command_name
                shutil.copyfile(FIXTURE_DIRECTORY / "fake_ansible.py", command_path)
                command_path.chmod(0o755)

            environment = {
                **os.environ,
                "PATH": str(command_directory) + ":" + os.environ["PATH"],
                "SYSCONFIG_TEST_CALLS": str(call_log),
            }
            result = subprocess.run(
                [str(REPOSITORY_ROOT / "setup.sh"), "--check", "--diff"],
                cwd=temporary,
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            calls = [json.loads(line) for line in call_log.read_text().splitlines()]
            galaxy_call, playbook_call = calls

            self.assertEqual(galaxy_call[0], "ansible-galaxy")
            self.assertIn(str(REPOSITORY_ROOT / "ansible/requirements.yml"), galaxy_call)
            self.assertEqual(playbook_call[0], "ansible-playbook")
            self.assertIn(str(REPOSITORY_ROOT / "ansible/setup.yml"), playbook_call)
            self.assertEqual(playbook_call[-2:], ["--check", "--diff"])


if __name__ == "__main__":
    unittest.main()
