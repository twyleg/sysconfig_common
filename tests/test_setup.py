"""Exercise the native role, including plugin cloning, without root or Internet."""
import functools
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest

import yaml
ROOT=Path(__file__).resolve().parents[1]
ANSIBLE=os.environ.get('SYSCONFIG_TEST_ANSIBLE',shutil.which('ansible-playbook') or '')

class QuietHTTP(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

@unittest.skipUnless(ANSIBLE,'Install Ansible or set SYSCONFIG_TEST_ANSIBLE')
class NativeSetupTests(unittest.TestCase):
    def test_converges_preserves_files_and_supports_check_mode(self):
        with tempfile.TemporaryDirectory(prefix='native sysconfig review ') as temp:
            base=Path(temp)
            home=base/'user home'
            home.mkdir()
            (home/'.gitconfig').write_text('keep my configuration\n')
            repo_source=base/'plugin source'
            repo_source.mkdir()
            (repo_source/'README').write_text('local plugin fixture\n')
            (repo_source/'install').write_text('#!/bin/sh\nmkdir -p "$(dirname "$0")/bin"\nprintf fixture > "$(dirname "$0")/bin/fzf"\nchmod +x "$(dirname "$0")/bin/fzf"\n')
            (repo_source/'install').chmod(0o755)
            def git(*args):
                subprocess.run(['git',*args],cwd=repo_source,check=True,capture_output=True)
            git('init')
            git('add','.')
            git('-c','user.name=Fixture','-c','user.email=fixture@local','commit','-m','fixture')
            remotes=base/'remote repositories'
            plugins=re.findall(r"^Plug '([^']+)'",(ROOT/'conf/vim/vimrc').read_text(),re.M)
            for plugin in plugins:
                dest=remotes/(plugin+'.git')
                dest.parent.mkdir(parents=True,exist_ok=True)
                subprocess.run(['git','clone','--bare',str(repo_source),str(dest)],check=True,capture_output=True)
            web=base/'web'
            web.mkdir()
            (web/'plug.vim').write_text('fixture vim-plug\n')
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHTTP,directory=str(web)))
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                vars_file=base/'vars.json'
                vars_file.write_text(json.dumps({'sysconfig_manage_system':False,'sysconfig_home':str(home),
                    'sysconfig_data_home':str(home/'data'),'sysconfig_plugin_base_url':remotes.as_uri(),
                    'sysconfig_vim_plug_url':f'http://127.0.0.1:{server.server_port}/plug.vim'}))
                env={**os.environ,'ANSIBLE_CONFIG':str(ROOT/'ansible/ansible.cfg')}
                command=[ANSIBLE,'-i','localhost,',str(ROOT/'ansible/setup.yml'),'-e','@'+str(vars_file)]
                first=subprocess.run(command,env=env,capture_output=True,text=True,timeout=180)
                self.assertEqual(first.returncode,0,first.stdout+first.stderr)
                self.assertEqual((home/'.gitconfig').read_text(),'keep my configuration\n')
                link=home/'.tmux.conf'
                self.assertEqual(link.resolve(),home/'dev/sysconfig_common/conf/tmux/tmux.conf')
                for plugin in plugins:
                    self.assertTrue((home/'.vim/plugged'/plugin.split('/')[-1]/'.git').is_dir())
                self.assertTrue(os.access(home/'.vim/plugged/fzf/bin/fzf',os.X_OK))
                second=subprocess.run(command,env=env,capture_output=True,text=True,timeout=180)
                self.assertEqual(second.returncode,0,second.stdout+second.stderr)
                self.assertRegex(second.stdout,r'changed=0\s')
                link.unlink()
                preview=subprocess.run(command+['--check','--diff'],env=env,capture_output=True,text=True,timeout=180)
                self.assertEqual(preview.returncode,0,preview.stdout+preview.stderr)
                self.assertFalse(link.exists())
                self.assertRegex(preview.stdout,r'changed=[1-9]')
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


class WrapperTests(unittest.TestCase):
    def test_forwards_arguments_and_uses_the_shared_role_playbook(self):
        with tempfile.TemporaryDirectory(prefix='sysconfig wrapper ') as temp:
            root=Path(temp)
            calls=root/'calls.jsonl'
            mock=r'''#!/usr/bin/env python3
import json, os, pathlib, sys
with open(os.environ['SYSCONFIG_TEST_CALLS'],'a') as output:
    output.write(json.dumps([pathlib.Path(sys.argv[0]).name,*sys.argv[1:]])+'\n')
'''
            for name in ('ansible-playbook','ansible-galaxy'):
                path=root/name
                path.write_text(mock)
                path.chmod(0o755)
            env={**os.environ,'PATH':str(root)+':'+os.environ['PATH'],
                 'SYSCONFIG_TEST_CALLS':str(calls)}
            result=subprocess.run([str(ROOT/'setup.sh'),'--check','--diff'],
                                  cwd=temp,env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            recorded=[json.loads(line) for line in calls.read_text().splitlines()]
            self.assertEqual(recorded[0][0],'ansible-galaxy')
            self.assertIn(str(ROOT/'ansible/requirements.yml'),recorded[0])
            self.assertEqual(recorded[1][0],'ansible-playbook')
            self.assertIn(str(ROOT/'ansible/setup.yml'),recorded[1])
            self.assertEqual(recorded[1][-2:],['--check','--diff'])

if __name__=='__main__': unittest.main()
