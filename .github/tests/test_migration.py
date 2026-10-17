"""Exercise real Cargo failures and the shared build script after the v6 migration."""

import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github/scripts"))
import grade


@unittest.skipUnless(shutil.which("cargo"), "Cargo is required for migration integration checks")
class CargoMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rustlings-migration-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "exercises").mkdir()
        shutil.copy2(ROOT / "rust-toolchain.toml", self.root / "rust-toolchain.toml")
        self.environment = patch.dict(os.environ, {"CARGO_TARGET_DIR": str(self.root / "target"),
                                                  "CARGO_TERM_COLOR": "never"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.actual_run = subprocess.run

    def prepare(self, source, mode="compile", build=None):
        self.exercise = {"name": "example", "path": "exercises/example.rs", "mode": mode}
        (self.root / "exercises/example.rs").write_text(source)
        manifest = ('[package]\nname = "migration-fixture"\nversion = "0.1.0"\n'
                    'edition = "2024"\n[[bin]]\nname = "example"\n'
                    'path = "exercises/example.rs"\n')
        (self.root / "Cargo.toml").write_text(manifest)
        if build is not None:
            (self.root / "build.rs").write_text(build)
        result = self.actual_run(["cargo", "generate-lockfile", "--offline"], cwd=self.root,
                                 capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def measure(self):
        logs = []

        def capture(command, **kwargs):
            result = self.actual_run(command, **kwargs, capture_output=True, text=True)
            logs.extend([result.stdout, result.stderr])
            return result

        stdout = io.StringIO()
        with patch.object(grade, "ROOT", self.root), \
                patch.object(grade, "COURSE", {"tests": [self.exercise]}), \
                patch.object(grade.subprocess, "run", side_effect=capture), \
                contextlib.redirect_stdout(stdout):
            code = grade.run_exercise("example")
        output = "\n".join(logs) + stdout.getvalue()
        return code, output, grade.passed(self.exercise, code, output)

    def test_compiler_failure_does_not_receive_points(self):
        self.prepare("fn main() { let value: u8 = true; }")
        code, output, passed = self.measure()
        self.assertNotEqual(code, 0)
        self.assertIn("mismatched types", output)
        self.assertFalse(passed)
        self.assertNotIn("Successfully ran", output)

    def test_runtime_failure_does_not_receive_points(self):
        self.prepare('fn main() { panic!("runtime fixture failed"); }')
        code, output, passed = self.measure()
        self.assertNotEqual(code, 0)
        self.assertIn("runtime fixture failed", output)
        self.assertFalse(passed)

    def test_zero_tests_do_not_receive_points(self):
        self.prepare("fn main() {}", mode="test")
        code, output, passed = self.measure()
        self.assertEqual(code, 0, output)
        self.assertIn("0 passed", output)
        self.assertFalse(passed)

    def test_failed_test_does_not_receive_points(self):
        self.prepare('fn main() {}\n#[test] fn example() { assert_eq!(1, 2); }', mode="test")
        code, output, passed = self.measure()
        self.assertNotEqual(code, 0)
        self.assertIn("1 failed", output)
        self.assertFalse(passed)

    def test_clippy_warning_is_rejected_for_a_clippy_exercise(self):
        self.prepare("fn main() { let unused = 1; }", mode="clippy")
        code, output, passed = self.measure()
        self.assertNotEqual(code, 0)
        self.assertIn("unused variable", output)
        self.assertFalse(passed)

    def test_successful_test_receives_points(self):
        self.prepare('fn main() {}\n#[test] fn example() { assert_eq!(2 + 2, 4); }', mode="test")
        code, output, passed = self.measure()
        self.assertEqual(code, 0, output)
        self.assertTrue(passed)

    def test_unfinished_shared_build_script_does_not_block_other_exercises(self):
        self.prepare("fn main() {}", build=(ROOT / "exercises/tests/build.rs").read_text())
        native = self.actual_run(["cargo", "run", "--locked", "--bin", "example"],
                                 cwd=self.root, capture_output=True, text=True)
        self.assertEqual(native.returncode, 0, native.stdout + native.stderr)
        code, output, passed = self.measure()
        self.assertEqual(code, 0, output)
        self.assertTrue(passed)

    def test_broken_build_script_only_fails_buildscript_grading(self):
        self.prepare('fn main() {}\n#[test] fn example() { assert_eq!(2 + 2, 4); }',
                     mode="test", build='compile_error!("broken student build script");')
        code, output, passed = self.measure()
        self.assertEqual(code, 0, output)
        self.assertTrue(passed)
        self.exercise["mode"] = "buildscript"
        code, output, passed = self.measure()
        self.assertNotEqual(code, 0)
        self.assertIn("broken student build script", output)
        self.assertFalse(passed)

    def test_buildscript_exercise_receives_its_environment(self):
        self.prepare('''fn main() {}
#[test] fn example() { assert_eq!(std::env::var("TEST_FOO").unwrap(), "fixture"); }
''', mode="buildscript", build='fn main() { println!("cargo:rustc-env=TEST_FOO=fixture"); }')
        code, output, passed = self.measure()
        self.assertEqual(code, 0, output)
        self.assertTrue(passed)

    def test_shared_build_script_refreshes_cached_timestamps(self):
        original = (ROOT / "exercises/tests/build.rs").read_text()
        # Use the repository's rerun policy with a solved fixture only. Student
        # build-script answers remain untouched in the actual exercise files.
        policy = next(line for line in original.splitlines() if "cargo:rerun-if-changed=" in line)
        self.prepare('''fn main() {}
#[test]
fn fresh_timestamp() {
    let timestamp: u64 = std::env::var("TEST_FOO").unwrap().parse().unwrap();
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
    assert!(now >= timestamp && now < timestamp + 10);
}
''', mode="buildscript", build='''fn main() {
''' + policy + '''
    let timestamp = std::env::var("FIXTURE_OLD_TIMESTAMP").unwrap_or_else(|_| {
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)
            .unwrap().as_secs().to_string()
    });
    println!("cargo:rustc-env=TEST_FOO={timestamp}");
}
''')
        with patch.dict(os.environ, {"FIXTURE_OLD_TIMESTAMP": str(int(time.time()) - 60)}):
            first = self.actual_run(["cargo", "test", "--locked", "--bin", "example"],
                                    cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(first.returncode, 0)
        second = self.actual_run(["cargo", "test", "--locked", "--bin", "example"],
                                 cwd=self.root, capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)


if __name__ == "__main__":
    unittest.main()
