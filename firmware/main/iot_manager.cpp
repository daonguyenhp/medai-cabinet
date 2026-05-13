#include "iot_manager.h"
#include "config.h"
#include "servo_controller.h"
#include "led_buzzer.h"
#include "display_manager.h"

#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>

static WiFiClientSecure wifiClient;
static PubSubClient mqttClient(wifiClient);
static const char* _deviceId;

void IoTManager::init(const char* deviceId, const char* endpoint,
                      const char* certPath, const char* keyPath, const char* caPath) {
    _deviceId = deviceId;

    if (!SPIFFS.begin(true)) {
        Serial.println("[IoT] SPIFFS mount failed");
        return;
    }

    // Load certificates from SPIFFS into strings, then pass to WiFiClientSecure
    auto readFile = [](const char* path) -> String {
        File f = SPIFFS.open(path, "r");
        if (!f) return String();
        String s = f.readString();
        f.close();
        return s;
    };

    String certStr = readFile(certPath);
    String keyStr  = readFile(keyPath);
    String caStr   = readFile(caPath);

    if (certStr.isEmpty() || keyStr.isEmpty() || caStr.isEmpty()) {
        Serial.println("[IoT] Certificate files not found or empty");
        return;
    }

    wifiClient.setCertificate(certStr.c_str());
    wifiClient.setPrivateKey(keyStr.c_str());
    wifiClient.setCACert(caStr.c_str());

    mqttClient.setServer(endpoint, IOT_PORT);
    mqttClient.setCallback(onMessage);
    mqttClient.setBufferSize(2048);

    reconnect();
}

void IoTManager::reconnect() {
    int attempts = 0;
    while (!mqttClient.connected() && attempts < 5) {
        Serial.print("[IoT] Connecting MQTT...");
        // Use MQTT_CLIENT_ID from config.h — must match IoT Policy
        if (mqttClient.connect(MQTT_CLIENT_ID)) {
            Serial.println(" connected");
            subscribe();
        } else {
            Serial.printf(" failed (rc=%d), retry in 5s\n", mqttClient.state());
            delay(5000);
            attempts++;
        }
    }
}

void IoTManager::subscribe() {
    mqttClient.subscribe(TOPIC_COMMAND);
    Serial.printf("[IoT] Subscribed to %s\n", TOPIC_COMMAND);
}

void IoTManager::loop() {
    if (!mqttClient.connected()) {
        reconnect();
    }
    mqttClient.loop();
}

bool IoTManager::isConnected() {
    return mqttClient.connected();
}

void IoTManager::publishTelemetry(const SensorData& data) {
    StaticJsonDocument<512> doc;
    doc["device_id"]        = _deviceId;
    doc["timestamp"]        = data.timestamp;
    doc["temperature"]      = data.temperature;
    doc["humidity"]         = data.humidity;
    doc["battery_level"]    = data.batteryLevel;
    doc["wifi_rssi"]        = WiFi.RSSI();
    doc["firmware_version"] = FIRMWARE_VER;
    doc["uptime_seconds"]   = millis() / 1000;
    doc["free_heap"]        = ESP.getFreeHeap();

    char buf[512];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_TELEMETRY, buf, true); // retained=true
    Serial.println("[IoT] Telemetry published");

    // Also publish heartbeat
    StaticJsonDocument<128> hb;
    hb["device_id"] = _deviceId;
    hb["ts"]        = data.timestamp;
    hb["online"]    = true;
    char hbBuf[128];
    serializeJson(hb, hbBuf);
    mqttClient.publish(TOPIC_HEARTBEAT, hbBuf, true);
}

void IoTManager::checkPendingCommands() {
    // Commands arrive via MQTT callback — nothing to poll
}

void IoTManager::onMessage(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
    Serial.printf("[IoT] Message on %s: %s\n", topic, msg.c_str());

    StaticJsonDocument<512> doc;
    if (deserializeJson(doc, msg) != DeserializationError::Ok) {
        Serial.println("[IoT] JSON parse error");
        return;
    }

    const char* command = doc["command"];
    if (!command) return;

    if (strcmp(command, "dispense") == 0) {
        int compartment = doc["payload"]["compartment"] | 0;
        int quantity    = doc["payload"]["quantity"] | 1;
        const char* medId = doc["payload"]["medication_id"] | "";
        handleDispense(compartment, quantity, medId);
    } else if (strcmp(command, "alert") == 0) {
        const char* alertType = doc["payload"]["alert_type"] | "info";
        const char* alertMsg  = doc["payload"]["message"] | "";
        handleAlert(alertType, alertMsg);
    } else if (strcmp(command, "get_telemetry") == 0) {
        // Will be published on next telemetry cycle
        Serial.println("[IoT] Telemetry requested");
    }
}

void IoTManager::handleDispense(int compartment, int quantity, const char* medicationId) {
    Serial.printf("[IoT] Dispense: compartment=%d qty=%d med=%s\n", compartment, quantity, medicationId);
    DisplayManager::showDispensing(compartment, quantity);
    LedBuzzer::beep(1);
    ServoController::dispense(compartment, quantity);
    LedBuzzer::beep(2);
    DisplayManager::showReady(_deviceId);
}

void IoTManager::handleAlert(const char* alertType, const char* message) {
    Serial.printf("[IoT] Alert: type=%s msg=%s\n", alertType, message);
    DisplayManager::showAlert(message);
    LedBuzzer::alert();
}
