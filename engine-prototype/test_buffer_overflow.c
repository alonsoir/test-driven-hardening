#include <string.h>
#include <stdio.h>

void vulnerable() {
    char buffer[10];
    char input[50] = "This is definitely longer than 10 characters!";
    strcpy(buffer, input);  // Buffer overflow claro
}

int main() {
    vulnerable();
    return 0;
}
