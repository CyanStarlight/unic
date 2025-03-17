#include "tests.h"


class tests {
private:
    int* testUserInput_INT;

public:
    tests() {
        testUserInput_INT = new int[10] {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    }

    ~tests() {
        delete[] testUserInput_INT;
    }

    void modifyUserInput_INT(int* userInput) {
        for (int i = 0; i < 10; i++) {
            userInput[i] = testUserInput_INT[i];
        }
    }
};

