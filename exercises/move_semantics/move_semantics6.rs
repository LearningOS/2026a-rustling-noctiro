// move_semantics6.rs
// Execute `rustlings hint move_semantics6` or press `h` in watch mode for a hint.
// You can't change anything except adding or removing references.

// TODO: Complete this exercise.

fn main() {
    let data = "Rust is great!".to_string();

    get_char(data);

    string_uppercase(&data);
}

// Should not take ownership
fn get_char(data: String) -> char {
    data.chars().last().unwrap()
}

// Should take ownership
fn string_uppercase(mut data: &String) {
    data = &data.to_uppercase();

    println!("{}", data);
}
