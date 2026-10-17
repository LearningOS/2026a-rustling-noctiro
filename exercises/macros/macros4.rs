// macros4.rs
//
// Execute `rustlings hint macros4` or press `h` in watch mode for a
// hint.

// TODO: Complete this exercise.

#[rustfmt::skip]
macro_rules! my_macro {
    () => {
        println!("Check out my macro!");
    }
    ($val:expr) => {
        println!("Look at this other macro: {}", $val);
    }
}

fn main() {
    my_macro!();
    my_macro!(7777);
}
