#pragma once
#include <Arduino.h>

struct SensorData {
    float temperature;
    float humidity;
    int   batteryLevel;   // 0-100 %
    String timestamp;
};

class SensorManager {
public:
    static void init();
    static SensorData read();

private:
    static int readBatteryPercent();
};
