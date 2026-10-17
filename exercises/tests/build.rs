//! This is the build script for both tests7 and tests8.
//!
//! You should modify this file to make both exercises pass.

fn main() {
    // tests7 checks a fresh timestamp. A missing watched file makes Cargo rerun
    // this build script before each command, including when binaries are cached.
    println!("cargo:rerun-if-changed=tmp/always-rerun-course-build-script");
    println!("cargo:rustc-check-cfg=cfg(feature, values(\"pass\"))");
    // In tests7, we should set up an environment variable
    // called `TEST_FOO`. Print in the standard output to let
    // Cargo do it.
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs(); // What's the use of this timestamp here?
    let your_command = format!(
        "placeholder=Your command here with {}, please checkout exercises/tests/build.rs",
        timestamp
    );
    println!("cargo:{}", your_command);

    // In tests8, we should enable "pass" feature to make the
    // testcase return early. Fill in the command to tell
    // Cargo about that.
    let your_command = "placeholder=Your command here, please checkout exercises/tests/build.rs";
    println!("cargo:{}", your_command);
}
