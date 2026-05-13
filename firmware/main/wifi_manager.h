#pragma once
#include <Arduino.h>

class WiFiManager {
public:
    static void connect(const char* ssid, const char* password);
    static bool isConnected();
    static String getIP();
};
