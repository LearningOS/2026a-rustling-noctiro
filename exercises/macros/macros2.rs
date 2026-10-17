// macros2.rs
//
// Execute `rustlings hint macros2` or press `h` in watch mode for a
// hint.

// TODO: Complete this exercise.

fn main() {
    my_macro!();
}

macro_rules! my_macro {
    () => {
        println!("Check out my macro!");
    };
}
