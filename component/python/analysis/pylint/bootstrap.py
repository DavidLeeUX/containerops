#!/usr/bin/env python3

import subprocess
import os
import sys
import json

REPO_PATH = 'git-repo'


def git_clone(url):
    r = subprocess.run(['git', 'clone', url, REPO_PATH])

    if (r.returncode == 0):
        return True
    else:
        print("[COUT] Git clone error: Invalid argument to exit", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return False


def get_pip_cmd(version):
    if version == 'py3k' or version == 'python3':
        return 'pip3'

    return 'pip'


def init_env(version):
    subprocess.run([get_pip_cmd(version), 'install', 'pylint'])


def validate_version(version):
    valid_version = ['python', 'python2', 'python3', 'py3k']
    if version not in valid_version:
        print("[COUT] Check version failed: the valid version is {}".format(valid_version), file=sys.stderr)
        return False

    return True


def pylint(file_name, rcfile):
    if rcfile:
        rcfile = '--rcfile={}/{}'.format(REPO_PATH, rcfile)
    else:
        rcfile = '--rcfile=/root/.pylintrc'
    r = subprocess.run(['pylint', '-f', 'json', rcfile, file_name], stdout=subprocess.PIPE)

    passed = True
    if (r.returncode != 0):
        passed = False

    out = str(r.stdout, 'utf-8').strip()
    retval = []
    for o in json.loads(out):
        o['path'] = trim_repo_path(o['path'])
        retval.append(o)

    if len(retval) > 0:
        print('[COUT] CO_JSON_CONTENT {}'.format(json.dumps({
            "results": { "cli": retval } })))

    return passed


def trim_repo_path(n):
    return n[len(REPO_PATH) + 1:]


def parse_argument():
    data = os.environ.get('CO_DATA', None)
    if not data:
        return {}

    validate = ['git-url', 'rcfile', 'version']
    ret = {}
    for s in data.split(' '):
        s = s.strip()
        if not s:
            continue
        arg = s.split('=')
        if len(arg) < 2:
            print('[COUT] Unknown Parameter: [{}]'.format(s))
            continue

        if arg[0] not in validate:
            print('[COUT] Unknown Parameter: [{}]'.format(s))
            continue

        ret[arg[0]] = arg[1]

    return ret


def main():
    argv = parse_argument()
    git_url = argv.get('git-url')
    if not git_url:
        print("[COUT] The git-url value is null", file=sys.stderr)
        print("[COUT] CO_RESULT = false")
        return

    version = argv.get('version', 'py3k')

    if not validate_version(version):
        print("[COUT] CO_RESULT = false")
        return

    init_env(version)

    rcfile = argv.get('rcfile')

    if not git_clone(git_url):
        return

    all_true = True

    for root, dirs, files in os.walk(REPO_PATH):
        for file_name in files:
            if file_name.endswith('.py'):
                o = pylint(os.path.join(root, file_name), rcfile)
                all_true = all_true and o

    if all_true:
        print("[COUT] CO_RESULT = true")
    else:
        print("[COUT] CO_RESULT = false")


main()
