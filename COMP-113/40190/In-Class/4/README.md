
# Week 4: Data Structures

- ___Record___: Used for storing information of varying types under a single name.
- ___Data field___: A single piece of information stored in a record.
- ___Structure___: A record
  - ___Structure example___:
    - A student record:
      - `Name: "John Doe"` $\Leftarrow$ `String`
      - `ID: S12345`   $\Leftarrow$ `String` or some other type
      - `CPA: 3.56`      $\Leftarrow$ `Float`
      - `Credits: 62`    $\Leftarrow$ `Int`

    - A time record:
      - `Hours: 12`      $\Leftarrow$ `Int`
      - `Minutes: 30`   $\Leftarrow$ `Int`
      - `Seconds: 45`   $\Leftarrow$ `Int`

## Structures in C++

- Aggregate data types built using elements of other data types

    ```c++
    struct Time {
        int hours;
        int minutes;
        int seconds;
        double milliseconds;
    };
    ```

  - Structure member naming:

    - Inside the structure, members must have unique names.

    - Outside the structure, members must be accessed using the structure name and the dot operator, can still have the same name as other variables.

  - __`struct`__ definition
    - Creates a new data type used to declare variables.
    - Defines a template for the structure.
    - ___Example___ usage of a new structure type:

      ```c++
      Time timeObject;
      timeObject.hours = 12;
      timeObject.milliseconds = 45.3;
      ```

      - Member access operators
        - Dot operator `.`: Used to access members of a structure.
           `timeObject.hours`, `timeObject.minutes`, `timeObject.seconds`

    - Read value to member `hours` of `timeObject`:

      ```c++
      cin >> timeObject.hours;
      ```

      - Assign value to member `hours` of `timeObject`:

      ```c++
      timeObject.hours = 11;
      ```

      - Print value of member `hours` of `timeObject`:

      ```c++
      cout << timeObject.hours;
      ```
