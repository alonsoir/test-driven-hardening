#include <string.h>
#include <stdio.h>

int main() {
    char buffer[10];
    char input[20] = "This is too long!";
    
    // Vulnerabilidad: buffer overflow
    strcpy(buffer, input);
    
    printf("Buffer: %s\n", buffer);
    return 0;
}
