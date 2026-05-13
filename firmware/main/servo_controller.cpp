/**
 * Compartment Controller — ULN2003 + 28BYJ-48 Stepper Motor
 *
 * Each compartment has:
 *   - 1× ULN2003 driver board
 *   - 1× 28BYJ-48 stepper motor (5V, 2048 steps/rev)
 *   - 1× IR obstacle sensor (detect pill dispensed)
 *
 * Wiring per motor:
 *   ULN2003 IN1-IN4 → ESP32 GPIO (see config.h)
 *   ULN2003 VCC     → 5V (external supply, NOT ESP32 3.3V)
 *   ULN2003 GND     → GND (common with ESP32)
 */
#include "servo_controller.h"
#include "config.h"
#include <AccelStepper.h>

// AccelStepper: HALF4WIRE mode for 28BYJ-48 via ULN2003
// Pin order: IN1, IN3, IN2, IN4 (interleaved for correct half-step sequence)
static AccelStepper stepper1(AccelStepper::HALF4WIRE, STEPPER1_IN1, STEPPER1_IN3, STEPPER1_IN2, STEPPER1_IN4);
static AccelStepper stepper2(AccelStepper::HALF4WIRE, STEPPER2_IN1, STEPPER2_IN3, STEPPER2_IN2, STEPPER2_IN4);
static AccelStepper stepper3(AccelStepper::HALF4WIRE, STEPPER3_IN1, STEPPER3_IN3, STEPPER3_IN2, STEPPER3_IN4);

static AccelStepper* steppers[3] = { &stepper1, &stepper2, &stepper3 };

// Track open/closed state
static bool compartmentOpen[3] = { false, false, false };

// IR sensor pins
static const int IR_PINS[3] = { IR_SENSOR_1, IR_SENSOR_2, IR_SENSOR_3 };

// Max speed and acceleration for 28BYJ-48
// Half-step mode: 4096 steps/rev; keep speed low for torque
static const float MOTOR_MAX_SPEED  = 500.0f;  // steps/sec
static const float MOTOR_ACCEL      = 200.0f;  // steps/sec²

void ServoController::init() {
    for (int i = 0; i < 3; i++) {
        steppers[i]->setMaxSpeed(MOTOR_MAX_SPEED);
        steppers[i]->setAcceleration(MOTOR_ACCEL);
        steppers[i]->setCurrentPosition(0);
    }

    // IR sensors as input
    for (int i = 0; i < 3; i++) {
        pinMode(IR_PINS[i], INPUT);
    }

    Serial.println("[Stepper] Initialized (3 compartments, ULN2003 + AccelStepper)");
}

void ServoController::openCompartment(int compartment) {
    if (compartment < 1 || compartment > 3) return;
    int idx = compartment - 1;
    if (compartmentOpen[idx]) return;  // Already open

    steppers[idx]->move(STEPS_OPEN);
    while (steppers[idx]->distanceToGo() != 0) {
        steppers[idx]->run();
    }
    // Power off coils to prevent heating
    steppers[idx]->disableOutputs();

    compartmentOpen[idx] = true;
    Serial.printf("[Stepper] Compartment %d opened\n", compartment);
}

void ServoController::closeCompartment(int compartment) {
    if (compartment < 1 || compartment > 3) return;
    int idx = compartment - 1;
    if (!compartmentOpen[idx]) return;  // Already closed

    steppers[idx]->enableOutputs();
    steppers[idx]->move(-STEPS_OPEN);
    while (steppers[idx]->distanceToGo() != 0) {
        steppers[idx]->run();
    }
    steppers[idx]->disableOutputs();

    compartmentOpen[idx] = false;
    Serial.printf("[Stepper] Compartment %d closed\n", compartment);
}

void ServoController::closeAll() {
    for (int i = 1; i <= 3; i++) closeCompartment(i);
}

bool ServoController::isPillDetected(int compartment) {
    if (compartment < 1 || compartment > 3) return false;
    // IR sensor: LOW = object detected (pill present), HIGH = no object
    return digitalRead(IR_PINS[compartment - 1]) == LOW;
}

void ServoController::dispense(int compartment, int quantity) {
    Serial.printf("[Stepper] Dispensing %d from compartment %d\n", quantity, compartment);

    openCompartment(compartment);

    // Wait for user to take pills (up to 10 seconds)
    // IR sensor confirms pill removed
    unsigned long start = millis();
    bool pillTaken = false;
    while (millis() - start < 10000) {
        if (!isPillDetected(compartment)) {
            // Pill no longer detected = taken
            delay(500);  // Debounce
            if (!isPillDetected(compartment)) {
                pillTaken = true;
                break;
            }
        }
        delay(100);
    }

    if (pillTaken) {
        Serial.printf("[Stepper] Pill taken from compartment %d\n", compartment);
    } else {
        Serial.printf("[Stepper] Timeout — closing compartment %d\n", compartment);
    }

    closeCompartment(compartment);
}
