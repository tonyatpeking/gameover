#!../.venv/bin/python
import shlex
import subprocess


def sh(command: str,
       print_errors=True,
       raise_errors=False,
       print_output=True,
       print_command_split=False,
       ):
    command_split = shlex.split(command)
    if print_command_split:
        print(command_split)
    result = subprocess.run(command_split, capture_output=True, text=True)
    if result.stderr:
        if print_errors:
            print(result.stderr)
        if raise_errors:
            raise subprocess.CalledProcessError(
                returncode=result.returncode, cmd=result.args, stderr=result.stderr)
    if result.stdout:
        if print_output:
            print(result.stdout)
        return result.stdout


def popen(command: str):
    return subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
