#pragma once
#include <Arduino.h>

class DisplayManager {
public:
    static void init();
    static void showMessage(const char* msg);
    static void showReady(const char* deviceId);
    static void showDispensing(int compartment, int quantity);
    static void showAlert(const char* msg);
    static void clear();
};
