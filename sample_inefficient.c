#include <stdio.h>
#include <string.h>

int main(void) {
    char name[] = "compiler";
    int total = 0;
    for (int i = 0; i < 100; i++) {
        int length = (int)strlen(name); /* potentially repeated work */
        if (i < length) {
            total += i;
        }
    }
    printf("%d\n", total);
    return 0;
}
