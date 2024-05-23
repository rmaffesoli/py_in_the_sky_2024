import subprocess
import os
import sys
from pathlib import Path

python_executable = sys.executable


def run_subprocess(filepath, *args):
    output_filepath = Path(filepath).with_suffix(".log")
    output_file = open(output_filepath, "w")
    process = subprocess.Popen(
        [f"{python_executable}", filepath, *args],
        stdout=output_file,
        stderr=output_file,
        start_new_session=True,
    )
    print("Called subprocess with PID:", process.pid)


if __name__ == "__main__":
    run_subprocess(*sys.argv[1:])
