/**
 * MedAI Cabinet — ESP32 Firmware
 * Main entry point
 */
#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "iot_manager.h"
#include "servo_controller.h"
#include "sensor_manager.h"
#include "display_manager.h"
#include "led_buzzer.h"

// ── Task handles ──────────────────────────────────────────────────────────────
TaskHandle_t telemetryTaskHandle = NULL;
TaskHandle_t scheduleTaskHandle  = NULL;

// ── Telemetry task (runs every 60 s) ─────────────────────────────────────────
void telemetryTask(void* pvParameters) {
    for (;;) {
        if (IoTManager::isConnected()) {
            SensorData data = SensorManager::read();
            IoTManager::publishTelemetry(data);
        }
        vTaskDelay(pdMS_TO_TICKS(60000));
    }
}

// ── Schedule check task (runs every 30 s) ────────────────────────────────────
void scheduleCheckTask(void* pvParameters) {
    for (;;) {
        IoTManager::checkPendingCommands();
        vTaskDelay(pdMS_TO_TICKS(30000));
    }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial.println("[MedAI] Booting...");

    // Peripheral init
    LedBuzzer::init();
    DisplayManager::init();
    ServoController::init();
    SensorManager::init();

    DisplayManager::showMessage("Connecting WiFi...");
    WiFiManager::connect(WIFI_SSID, WIFI_PASSWORD);

    DisplayManager::showMessage("Connecting AWS IoT...");
    IoTManager::init(DEVICE_ID, IOT_ENDPOINT, IOT_CERT, IOT_KEY, IOT_CA);
    IoTManager::subscribe();

    // Start background tasks
    xTaskCreate(telemetryTask,    "Telemetry", 4096, NULL, 1, &telemetryTaskHandle);
    xTaskCreate(scheduleCheckTask,"Schedule",  4096, NULL, 1, &scheduleTaskHandle);

    LedBuzzer::beep(2);
    DisplayManager::showReady(DEVICE_ID);
    Serial.println("[MedAI] Ready.");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    IoTManager::loop();
    vTaskDelay(pdMS_TO_TICKS(100));
}
