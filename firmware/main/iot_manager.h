#pragma once
#include <Arduino.h>
#include "sensor_manager.h"

class IoTManager {
public:
    static void init(const char* deviceId, const char* endpoint,
                     const char* certPath, const char* keyPath, const char* caPath);
    static void subscribe();
    static void loop();
    static bool isConnected();
    static void publishTelemetry(const SensorData& data);
    static void checkPendingCommands();

private:
    static void onMessage(char* topic, byte* payload, unsigned int length);
    static void handleDispense(int compartment, int quantity, const char* medicationId);
    static void handleAlert(const char* alertType, const char* message);
    static void reconnect();
};
