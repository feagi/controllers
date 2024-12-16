#include  <Arduino.h>
#include "nm_command/nm_mblock.h"

const size_t dataLength = 5;
uint8_t data[dataLength];

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ; // Wait for serial port to connect
    }
    nm_setup();
    for (int i = 1; i <= 5; i++) {
        setFinger(static_cast<FingerNumber>(i), 40);
    }
    Serial.println("WORKED");  // Add newline
}

void loop() {
    if (Serial.available() >= dataLength) {
        // Clear any extra data in buffer
        while(Serial.available() > dataLength) {
            Serial.read();  // Clear the excess input buffer
        }

        // Read exactly dataLength bytes
//        size_t bytesRead = Serial.readBytes(data, dataLength);

        // Process the data
        for (int i = 0; i < dataLength; i++) {
            int index = i + 1;
            setFinger(static_cast<FingerNumber>(index), data[i]);
        }
    }
}
