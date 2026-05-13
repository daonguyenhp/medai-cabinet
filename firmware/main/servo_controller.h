#pragma once
// Renamed conceptually to "compartment controller"
// Uses ULN2003 + 28BYJ-48 stepper instead of servo
#include <Arduino.h>

class ServoController {
public:
    static void init();
    static void dispense(int compartment, int quantity);
    static void openCompartment(int compartment);
    static void closeCompartment(int compartment);
    static void closeAll();
    static bool isPillDetected(int compartment);  // IR sensor check
};
