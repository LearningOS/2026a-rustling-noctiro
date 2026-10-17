"""Grade the 110 community exercises using the same Cargo phases as Rustlings 6."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

from course import COURSE, ROOT, record, run, write_result


def validate_catalog():
    catalog = tomllib.loads((ROOT / "info.toml").read_text())
    exercises = catalog["exercises"]
    actual = [{"name": item["name"],
               "path": str(Path("exercises") / item.get("dir", "") / (item["name"] + ".rs")),
               "test": item.get("test", True),
               "strict_clippy": item.get("strict_clippy", False)} for item in exercises]
    expected = [{"name": item["name"], "path": item["path"],
                 "test": item["mode"] in ("test", "buildscript"),
                 "strict_clippy": item["mode"] == "clippy"} for item in COURSE["tests"]]
    if (type(catalog.get("format_version")) is not int or catalog["format_version"] != 1
            or any(type(item.get(key, default)) is not bool for item in exercises
                   for key, default in (("test", True), ("strict_clippy", False)))
            or actual != expected):
        raise ValueError("Exercise catalog differs from the course rubric; no score was produced.")
    manifest = tomllib.loads((ROOT / "Cargo.toml").read_text())
    targets = [{key: item[key] for key in ("name", "path")} for item in manifest["bin"]]
    if targets != [{key: item[key] for key in ("name", "path")} for item in COURSE["tests"]]:
        raise ValueError("Cargo targets differ from the course rubric; run rustlings dev update.")
    if manifest["package"].get("build") != "exercises/tests/build.rs":
        raise ValueError("The shared build script for tests7 and tests8 is missing.")
    if any(manifest.get(key) for key in ("dependencies", "dev-dependencies", "build-dependencies")):
        raise ValueError("The course exercises must use only the Rust standard library.")
    for exercise in expected:
        path = (ROOT / exercise["path"]).resolve()
        if not path.is_relative_to(ROOT / "exercises") or not path.is_file():
            raise ValueError("Missing or invalid exercise file: " + exercise["path"])


def passed(test, code, output):
    if code != 0:
        return False
    if test["mode"] in ("test", "buildscript"):
        return bool(re.search(r"test result: ok\. [1-9][0-9]* passed; 0 failed;", output))
    return "Successfully ran " + test["path"] in output


def exercise_commands(test, manifest):
    """Build, test when requested, lint, then execute the requested binary."""
    name = test["name"]
    target = ["--manifest-path", str(manifest), "--locked", "--bin", name]
    commands = [["cargo", "generate-lockfile", "--offline", "--manifest-path", str(manifest)],
                ["cargo", "build", *target]]
    if test["mode"] in ("test", "buildscript"):
        commands.append(["cargo", "test", *target, "--", "--show-output"])
    clippy = ["cargo", "clippy", *target, "--profile", "test"]
    if test["mode"] == "clippy":
        clippy.extend(["--", "-D", "warnings", "-D", "clippy::float_cmp"])
    commands.extend([clippy, ["cargo", "run", *target]])
    return commands


def isolated_manifest(test, project):
    """Keep errors in the student build script confined to its two exercises."""
    package = tomllib.loads((ROOT / "Cargo.toml").read_text())["package"]
    build = "false"
    if test["mode"] == "buildscript":
        build = json.dumps(str((ROOT / package.get("build", "build.rs")).resolve()))
    manifest = project / "Cargo.toml"
    manifest.write_text(
        '[package]\nname = ' + json.dumps("course-" + test["name"]) + '\n'
        'version = "0.0.0"\nedition = ' + json.dumps(package["edition"]) + '\n'
        'autobins = false\nbuild = ' + build + '\n'
        '[[bin]]\nname = ' + json.dumps(test["name"]) + '\n'
        'path = ' + json.dumps(str((ROOT / test["path"]).resolve())) + '\n'
        '[workspace]\n'
    )
    return manifest


def run_exercise(name):
    test = next((test for test in COURSE["tests"] if test["name"] == name), None)
    if test is None:
        raise ValueError("Unknown course exercise: " + name)
    (ROOT / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=name + "-", dir=ROOT / "tmp") as directory:
        manifest = isolated_manifest(test, Path(directory))
        for command in exercise_commands(test, manifest):
            print("$ " + " ".join(command), flush=True)
            code = subprocess.run(command, cwd=ROOT).returncode
            if code != 0:
                return code if code > 0 else 1
    print("Successfully ran " + test["path"], flush=True)
    return 0


def main():
    os.chdir(ROOT)
    output = ROOT / "tmp/grade"
    output.mkdir(parents=True, exist_ok=True)
    os.environ["TMPDIR"] = str(ROOT / "tmp")
    os.environ["CARGO_TERM_COLOR"] = "never"
    validate_catalog()
    # Infrastructure failures must not be published as student scores.
    subprocess.run(["cargo", "clippy", "--version"], check=True)
    subprocess.run(["cargo", "metadata", "--locked", "--no-deps", "--format-version", "1"],
                   check=True, stdout=subprocess.DEVNULL)
    results = []
    with tempfile.TemporaryDirectory(prefix="exercise-target-", dir=ROOT / "tmp") as target:
        os.environ["CARGO_TARGET_DIR"] = target
        for test in COURSE["tests"]:
            print(f"::group::{test['name']}", flush=True)
            with (output / (test["name"] + ".log")).open("w") as log:
                code, text = run([sys.executable, __file__, "--exercise", test["name"]],
                                 log, ROOT, seconds=20)
            results.append(record(test, code, passed(test, code, text)))
            print("::endgroup::", flush=True)
    write_result(results)


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--exercise":
            sys.exit(run_exercise(sys.argv[2]))
        if len(sys.argv) != 1:
            raise ValueError("Usage: grade.py [--exercise NAME]")
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
