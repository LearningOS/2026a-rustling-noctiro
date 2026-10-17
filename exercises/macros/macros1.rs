// macros1.rs
//
// Execute `rustlings hint macros1` or press `h` in watch mode for a
// hint.

// TODO: Complete this exercise.

macro_rules! my_macro {
    () => {
        println!("Check out my macro!");
    };
}

fn main() {
    my_macro();
}
