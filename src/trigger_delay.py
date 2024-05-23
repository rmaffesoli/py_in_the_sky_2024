import shlex
import subprocess
import argparse

def main(cmd):
    cmds = shlex.split(cmd)
    p = subprocess.Popen(cmds, start_new_session=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command")

    parsed_args = parser.parse_args()
    main(parsed_args.command)
    