// functions3.rs
// Execute `rustlings hint functions3` or press `h` in watch mode for a hint.

// TODO: Complete this exercise.

fn main() {
    call_me();
}

fn call_me(num: u32) {
    for i in 0..num {
        println!("Ring! Call number {}", i + 1);
    }
}
