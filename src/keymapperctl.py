

import subprocess


def input_raw(text: str):
    subprocess.run(['keymapperctl', '--input', text])


def output_raw(text: str):
    subprocess.run(['keymapperctl', '--output', text])
