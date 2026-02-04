#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[10];
    strcpy(buffer, input);  // Vulnerabilidad: buffer overflow
    printf("%s\n", buffer);
}

int main() {
    char *user_input = "This is a very long string that will overflow the buffer";
    vulnerable_function(user_input);
    return 0;
}
