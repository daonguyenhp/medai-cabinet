#pragma once
#include <Arduino.h>

class LedBuzzer {
public:
    static void init();
    static void beep(int times = 1);
    static void alert();
    static void setStatusLed(bool on);
    static void setAlertLed(bool on);
};
