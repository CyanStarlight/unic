from random import random_ui64, seed

# Find the first occurrence of a character in a string
fn locateRec(
    borrowed text: String, borrowed char: String, start: UInt32
) -> Int:
    if len(text) == 0 or start > len(text):
        return -1
    elif text[int(start)] == char:
        return int(start)
    else:
        return locateRec(text, char, start + 1)


# Print the alphabet, ending with the argument character
fn printLetters(borrowed text: String) -> None:
    var alphabet: String = "abcdefghijklmnopqrstuvwxyz"
    i = 0
    while i != len(alphabet):
        print(alphabet[i-1], end=" ")
        if alphabet[i] == text:
            print()
            break
        i += 1

fn printLettersRec(borrowed text: String, start: Int, stop: Int) -> None:
    if len(text) == 0 or start > len(text) or start > stop:
        return
    print(text[start], end=" ")
    if start == len(text):
        return
    else:
        printLettersRec(text, start + 1, stop)


" Test functions "

fn testLocateRec(inout text: String) -> None:
    seed()
    print("Testing LocateRec function")
    print("Test string: " + str(text))
    var char: String = str(text[int(random_ui64(0, len(text) - 1))])
    print("Test character: " + char)
    print(locateRec(text, char, 0), end="\n\n")


fn testPrintLetters() -> None:
    var alphabet: String = "abcdefghijklmnopqrstuvwxyz"
    seed()
    print("Testing printLetters function")
    var i: Int = int(random_ui64(0, len(alphabet)-1))
    print("random char: " + alphabet[i-1])
    printLetters(alphabet[i])
    print()

fn testPrintLettersRec(inout text: String, start: Int) -> None:
    seed()
    print("Testing printLettersRec function")
    var i: Int = int(random_ui64(0, len(text)))
    print("random char: " + text[i])

    printLettersRec(text, start=start, stop=i)
    print()

" Main function "

fn main():
    var text: String = "Hello, world!"
    testLocateRec(text)
    testPrintLetters()
    var alphabet: String = "abcdefghijklmnopqrstuvwxyz"
    testPrintLettersRec(alphabet, 0)
