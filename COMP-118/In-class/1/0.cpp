#pragma region init
#include <iostream>
#include <limits>
#include <cmath>

using namespace std;
#pragma endregion init

#pragma region const
const double PI = 3.14; // Might not be enough but ehh
#pragma endregion const

#pragma region template
double sum(int a, int b);
double area_circle(double radius);
double circumf_circle(double radius);
double vat_price_calc(double price, double vat_percent);

#pragma endregion template

#pragma region function
auto inputHandler(char *word, int wordlen)
{
    double input;
    while (true)
    {
        cout << "Enter ";
        for (int i = 0; i < wordlen; i++)
        {
            cout << word[i];
        }
        cout << endl;
        cin >> input;
        if (cin.fail())
        {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cerr << "Invalid input, Please try again:" << endl;
        }
        else
        {
            break;
        }
    }
    return input;
}

double sum(const int a, const int b)
{
    return a + b;
}
double area_circle(const double r)
{
    return PI * r * r;
}
double circumf_circle(const double r)
{
    return 2 * PI * r;
}
double vat_price_calc(const double price, const double vat_p)
{
    return price * ((vat_p / 100) + 1);
}

#pragma endregion function

#pragma region main
int main()
{
    bool ex = false;
    double a, b = 0;

    do
    {
        a = inputHandler("a", 1);
        b = inputHandler("b", 1);

        cout << "Options: " << endl;
        cout << "1. sum(a,b)" << endl;
        cout << "2. area_circle(a)" << endl;
        cout << "3. circumf_circle(a)" << endl;
        cout << "4. vat_price_calc(a)" << endl;
        cout << "0. Exit" << endl;

        int ch = inputHandler("option", 6);
        cout << ch << endl;
        switch (ch)
        {
        case 1:
            cout << "Running 'sum'" << endl;
            cout << sum(a, b) << endl;
            break;
        case 2:
            cout << "Running 'area_circle' using parameter 'a'" << endl;
            cout << area_circle(a) << endl;
            break;
        case 3:
            cout << "Running test 'circumf_circle'" << endl;
            cout << circumf_circle(a) << endl;
            break;
        case 4:
            cout << "Running test 'vat_price_calc'" << endl;
            cout << vat_price_calc(a, b) << endl;
            break;

        case 0:
            cout << "Oki bye" << endl;
            ex = true;
            break;
        default:
            cerr << "Not an option here!" << endl;
            break;
        }

    } while (ex != true);
}
#pragma endregion main