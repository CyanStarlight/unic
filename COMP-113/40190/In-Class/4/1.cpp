#pragma region init
#include <iostream>
#include <iomanip>
#include <limits>
#include <ctime>
using namespace std;
/*
    Constants
        CURRENCY: Currency symbol, gets baked into the program. Please don't use USD
*/
static char CURRENCY= 'E';
#pragma endregion init

#pragma region structure

struct Book
{
    string author;
    string title;
    int year;
    int ISBN;
    double price;
};

#pragma endregion structure

#pragma region validation

auto vinputUInt()
{
    unsigned int input;
    while (true)
    {
        cout << "" << endl;
        cin >> input;
        if (cin.fail())
        {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Invalid input, Please try again:" << endl;
        }
        else
        {
            break;
        }
    }
    return input;
}
auto vinputString()
{
    string input;
    while (true)
    {
        cout << endl;
        cin >> input;
        if (cin.fail())
        {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Invalid input, Please try again:" << endl;
        }
        else
        {
            break;
        }
    }
    return input;
}
auto vinputDouble()
{
    double input;
    while (true)
    {
        cout << "" << endl;
        cin >> input;
        if (cin.fail())
        {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Invalid input, Please try again:" << endl;
        }
        else
        {
            break;
        }
    }
    return input;
}
#pragma endregion validation

#pragma region function
// Populate a book with user input, performs input validation on all fields
#pragma warning(disable : 4996)
int PopulateBook(Book &book)
{

    time_t now = time(nullptr);
    struct tm *ltm = localtime(&now); // DevSkim: ignore DS154189
    int year;
    if (ltm != NULL)
    {
        year = ltm->tm_year + 1900;
    }
    else
    {
        cout << "Time not timing, please enter year manually" << endl;
        year = int(vinputUInt());
        cout << "Year set to: " << year << endl;
    }

    if (&book == nullptr)
    {
        return -1;
    }
    cout << "| Populating book |" << endl;
    cout << "Enter author: ";
    book.author = vinputString();
    cout << "Enter title: ";
    book.title = vinputString();
    cout << "Enter year: ";
    book.year = vinputUInt();
    cout << "Enter ISBN: ";
    book.ISBN = vinputUInt();
    cout << "Enter price in " << CURRENCY << ": ";
    book.price = vinputDouble();
    cout << "| Book populated |" << endl;
    return 0;
}
#pragma warning(default : 4996)

// Start a new book input session
Book InputBook()
{
    Book book;
    PopulateBook(book);
    return book;
}

// Start a number of book sessions and return an array of books
Book *InputBooks(int n)
{
    Book *books = new Book[n];
    for (int i = 0; i < n; i++)
    {
        books[i] = InputBook();
    }
    return books;
}
// Funny functions

// Returns the first index in case of multiple books with the same price
unsigned int ExpensiveBookPosition(const Book *books)
{
    if (books == nullptr)
    {
        return -1;
    }
    int num = sizeof(books) / sizeof(books[0]);
    double max = 0;
    unsigned int pos = -1;
    for (int i = 0; i < num; i++)
    {
        if (books[i].price > max)
        {
            max = books[i].price;
            pos = i;
        }
    }
    return pos;
}

// Displays the entire list of books to the user
void ListBooks(const Book *books, int n)
{
    if (books == nullptr)
    {
        cout << "No books to list" << endl;
        return;
    }
    int num = n;
    cout << "Listing books, total: " << num << endl;
    for (int i = 0; i < num; i++)
    {
        cout << "____" << i + 1 << "____" << endl;
        cout << "Author: " << books[i].author << endl;
        cout << "Title: " << books[i].title << endl;
        cout << "Year: " << books[i].year << endl;
        cout << "ISBN: " << books[i].ISBN << endl;
        cout << "Price: " << books[i].price << CURRENCY << endl;
    }
}
#pragma endregion function

#pragma region main
int main()
{
    // Ask user for number of books
    cout << "Enter number of books: ";
    int n = vinputUInt();
    Book *books = InputBooks(n);
    if (books == nullptr)
    {
        cout << "No books to list" << endl;
        return 0;
    }

    ListBooks(books, n);

    return 0;
}
#pragma endregion main
