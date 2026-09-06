#!/usr/bin/env python3
"""Build pinned unmodified libplist/libtatsu and a local offline request encoder."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
DEPENDENCIES = (
    ("libplist", "32428abacb909988e8e960a8845a6430b17b6a60"),
    ("libtatsu", "60a39f36d719344360ec2e87563ed43f61f0530f"),
)


def build(work):
    if platform.system() != "Linux":
        raise ValueError("Build the restore helper on Linux/WSL")
    work = Path(work).absolute()
    work.mkdir(parents=True, exist_ok=False)
    prefix = work / "prefix"
    env = dict(os.environ)
    env["PKG_CONFIG_PATH"] = str(prefix / "lib/pkgconfig")
    env["LD_LIBRARY_PATH"] = str(prefix / "lib")
    env["CFLAGS"] = "-O2 -mavx2"
    with (work / "build.log").open("xb") as log:
        def run(command, cwd=work):
            log.write(("+ " + shlex.join(map(str, command)) + "\n").encode())
            log.flush()
            subprocess.run(list(map(str, command)), cwd=cwd, env=env, stdout=log, stderr=log, check=True)
        for name, revision in DEPENDENCIES:
            print("Building " + name + " at " + revision, flush=True)
            source = work / name
            run(["git", "init", source])
            run(["git", "remote", "add", "origin", "https://github.com/libimobiledevice/" + name + ".git"], source)
            run(["git", "fetch", "--depth=1", "origin", revision], source)
            run(["git", "checkout", "--detach", revision], source)
            options = ["--prefix=" + str(prefix), "--disable-static"]
            if name == "libplist":
                options += ["--without-cython", "--without-tests"]
            run([source / "autogen.sh", *options], source)
            run(["make", "-j", "8"], source)
            run(["make", "install"], source)
        flags = subprocess.check_output(["pkg-config", "--cflags", "--libs", "libtatsu-1.0", "libplist-2.0"],
                                        env=env, text=True).strip()
        executable = prefix / "bin/venfire-tss-request"
        executable.parent.mkdir(exist_ok=True)
        run(["cc", "-O2", "-Wall", "-Wextra", "-Werror", "-mavx2", PROJECT / "tools/tss_request.c",
             "-Wl,-rpath," + str(prefix / "lib"), *shlex.split(flags), "-o", executable])
    report = {"schema": 1, "executable": str(executable),
              "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "dependencies": [{"name": name, "commit": revision} for name, revision in DEPENDENCIES],
              "scope": "Offline TSS request encoding only; no ticket signing or TLS bypass."}
    (work / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True)
    options = parser.parse_args()
    print(json.dumps(build(options.work), indent=2))
