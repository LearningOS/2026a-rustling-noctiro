"""Run the bootstrap in an isolated checkout with native installers replaced."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("bash"), "Bash is required for Unix setup checks")
class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rustlings-setup-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("setup.sh", "rust-toolchain.toml"):
            shutil.copy2(ROOT / name, self.root / name)
        self.bin = self.root / "cargo/bin"
        self.bin.mkdir(parents=True)
        self.log = self.root / "calls.jsonl"
        for name in ("cc", "rustup", "cargo", "rustlings"):
            stub = self.bin / name
            stub.write_text('''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
name = Path(sys.argv[0]).name
with open(os.environ["COURSE_SETUP_CALLS"], "a") as log:
    log.write(json.dumps({"name": name, "args": sys.argv[1:]}) + "\\n")
if name == "cargo" and os.environ.get("COURSE_SETUP_FAIL_CARGO"):
    sys.exit(42)
''')
            stub.chmod(0o755)
        self.env = dict(os.environ, CARGO_HOME=str(self.bin.parent),
                        PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        COURSE_SETUP_CALLS=str(self.log))

    def run_setup(self, *args):
        return subprocess.run(["bash", "setup.sh", *args], cwd=self.root,
                              env=self.env, capture_output=True, text=True)

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_noninteractive_setup_installs_without_starting_watch(self):
        result = self.run_setup("--no-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        names = [call["name"] for call in self.calls()]
        self.assertIn("rustup", names)
        self.assertIn("cargo", names)
        self.assertNotIn("rustlings", names)

    def test_default_setup_starts_watch(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1], {"name": "rustlings", "args": []})

    def test_failed_installation_stops_before_watch(self):
        self.env["COURSE_SETUP_FAIL_CARGO"] = "1"
        result = self.run_setup()
        self.assertEqual(result.returncode, 42)
        self.assertNotIn("rustlings", [call["name"] for call in self.calls()])

    def test_existing_cargo_configuration_is_preserved(self):
        config = self.root / ".cargo/config.toml"
        config.parent.mkdir()
        original = '[build]\njobs = 2\n'
        config.write_text(original)
        result = self.run_setup("--no-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(config.read_text(), original)

    def test_unknown_argument_does_not_start_installation(self):
        result = self.run_setup("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_sourcing_setup_preserves_the_callers_environment(self):
        script = '''setup_original_path=$PATH
setup_original_dist=${RUSTUP_DIST_SERVER-}
source ./setup.sh --no-run
[[ "$PATH" == "$setup_original_path" ]]
[[ "${RUSTUP_DIST_SERVER-}" == "$setup_original_dist" ]]
'''
        result = subprocess.run(["bash", "-e", "-c", script], cwd=self.root,
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
