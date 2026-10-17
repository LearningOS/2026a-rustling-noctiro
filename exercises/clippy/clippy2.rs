#![deny(clippy::float_cmp)]

// clippy2.rs
// 
// Execute `rustlings hint clippy2` or press `h` in watch mode for a
// hint.

// TODO: Complete this exercise.

fn main() {
    let mut res = 42;
    let option = Some(12);
    for x in option {
        res += x;
    }
    println!("{}", res);
}
