// functions5.rs
//
// Execute `rustlings hint functions5` or press `h` in watch mode for a
// hint.


fn main() {
    let answer = square(3);
    println!("The square of 3 is {}", answer);
}

fn square(num: i32) -> i32 {
    num * num
}
