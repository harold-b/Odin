package main

import "other"

main :: proc() {
    foo()
    other.foo()
    say_hello()
}
