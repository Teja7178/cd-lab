#include <stdio.h>

int main(void) {
    int values[] = {1, 2, 3, 4, 5};
    int total = 0;
    int count = 5;
    for (int i = 0; i < count; i++) {
        total += values[i];
    }
    printf("%d\n", total);
    return 0;
}
