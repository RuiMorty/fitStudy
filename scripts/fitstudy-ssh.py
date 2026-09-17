#!/usr/bin/env python3
"""SSH/SCP using this Mac's FitStudy configuration and Keychain entry."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
config = json.loads((root / '.deploy-local.json').read_text())
mode = sys.argv[1] if len(sys.argv) > 1 else 'ssh'
args = sys.argv[2:]
if mode not in ('ssh', 'scp'):
    sys.exit('Usage: python3 scripts/fitstudy-ssh.py ssh [remote-command] | scp [source] [destination]')

target = f"{config['user']}@{config['host']}"
common = [
    '-o', 'ConnectTimeout=10', '-o', 'ConnectionAttempts=1',
    '-o', 'StrictHostKeyChecking=yes',
    '-o', 'PreferredAuthentications=password',
    '-o', 'PubkeyAuthentication=no', '-o', 'NumberOfPasswordPrompts=1',
]
env = os.environ.copy()
env.update({
    'SSH_ASKPASS': str(root / 'scripts/fitstudy-askpass.sh'),
    'SSH_ASKPASS_REQUIRE': 'force',
    'DISPLAY': env.get('DISPLAY') or ':0',
    'FITSTUDY_KEYCHAIN_SERVICE': config['keychainService'],
    'FITSTUDY_KEYCHAIN_ACCOUNT': config['keychainAccount'],
})
if mode == 'ssh':
    command = ['/usr/bin/ssh', *common, '-p', str(config['port']), target, *args]
else:
    args = [target + ':' + a[len('fitstudy:'):] if a.startswith('fitstudy:') else a for a in args]
    command = ['/usr/bin/scp', *common, '-P', str(config['port']), *args]
sys.exit(subprocess.run(command, env=env).returncode)
