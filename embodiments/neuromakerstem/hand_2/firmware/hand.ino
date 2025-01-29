#include <Arduino.h>
#include "nm_command/nm_mblock.h"

const size_t dataLength = 5;  // Expected number of data values
uint8_t data[dataLength];

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ; // Wait for serial port to connect
    }
    nm_setup();
    for (int i = 1; i <= dataLength; i++) {
        setFinger(static_cast<FingerNumber>(i), 40);
    }
}

void loop() {
    static String inputString = "";  // Buffer to hold serial input
    static size_t index = 0;         // Track parsed numbers
    inputString.reserve(20);         // Reserve space for efficiency

    while (Serial.available()) {
        char incomingChar = Serial.read();
        
        // Check for newline or termination condition
        if (incomingChar == '\n') {
            // Split and parse the data only if input is complete
            char *token = strtok(const_cast<char*>(inputString.c_str()), ", ");
            index = 0;

            while (token != NULL && index < dataLength) {
                data[index] = atoi(token);  // Convert string to integer
                token = strtok(NULL, ", ");
                index++;
            }
            
            inputString = "";  // Reset the input buffer
            break;             // Exit the while loop
        } else {
            inputString += incomingChar;  // Accumulate input characters
        }
    }

    // Only process the data when all expected values are received
    if (index == dataLength) {
        for (size_t i = 0; i < dataLength; i++) {
            int fingerIndex = i + 1;
            setFinger(static_cast<FingerNumber>(fingerIndex), data[i]);
        }
        index = 0;  // Reset index after processing
    }
}
