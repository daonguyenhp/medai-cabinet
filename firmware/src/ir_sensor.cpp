#include <Arduino.h>
#include "ir_sensor.h"
#include "config.h"

// Number of consecutive readings required to confirm a pill detection.
// Filters out noise/bouncing when pill enters the beam.
#define IR_DEBOUNCE_SAMPLES   3

void initIRSensor() {
    // GPIO34 is input-only on ESP32 and does NOT support internal pull-up.
    // Module FC-51 has its own onboard pull-up, so plain INPUT is correct.
    pinMode(IR_SENSOR_PIN, INPUT);

    Serial.print("[IR] Sensor initialized on GPIO");
    Serial.println(IR_SENSOR_PIN);
}

bool isPillPresent() {
    // IR module logic: LOW = beam broken = pill detected
    return digitalRead(IR_SENSOR_PIN) == IR_PILL_DETECTED;
}

// Internal: confirm a stable detection by reading multiple samples
static bool isPillPresentDebounced() {
    for (int i = 0; i < IR_DEBOUNCE_SAMPLES; i++) {
        if (!isPillPresent()) return false;
        delay(2);
    }
    return true;
}

bool waitForPillDrop(unsigned long timeoutMs) {

    Serial.print("[IR] Waiting for pill to drop (timeout: ");
    Serial.print(timeoutMs);
    Serial.println("ms)");

    unsigned long start = millis();

    while (millis() - start < timeoutMs) {

        if (isPillPresentDebounced()) {
            Serial.println("[IR] Pill detected!");
            return true;
        }

        delay(IR_POLL_INTERVAL_MS);
    }

    Serial.println("[IR] Timeout — no pill detected");
    return false;
}
