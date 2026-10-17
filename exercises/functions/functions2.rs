// functions2.rs
//
// Execute `rustlings hint functions2` or press `h` in watch mode for a
// hint.


fn main() {
    call_me(3);
}

fn call_me(num: i32) {
    for i in 0..num {
        println!("Ring! Call number {}", i + 1);
    }
}
