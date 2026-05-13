#pragma once

// ── Device identity ───────────────────────────────────────────────────────────
#define DEVICE_ID       "medai-esp32-001"
#define FIRMWARE_VER    "1.0.0"

// ── WiFi credentials (override via platformio.ini build_flags) ───────────────
#ifndef WIFI_SSID
#define WIFI_SSID       "YourWiFiSSID"
#endif
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD   "YourWiFiPassword"
#endif

// ── AWS IoT Core ──────────────────────────────────────────────────────────────
// Endpoint from: AWS Console → IoT Core → Settings
#define IOT_ENDPOINT    "a3mqc6kvosl0e0-ats.iot.ap-southeast-1.amazonaws.com"
#define IOT_PORT        8883

// Certificate paths in SPIFFS (upload via: pio run --target uploadfs)
// Copy from backend/certs/ → firmware/data/certs/
#define IOT_CERT        "/certs/medai-cabinet-device.cert.pem"
#define IOT_KEY         "/certs/medai-cabinet-device.private.key"
#define IOT_CA          "/certs/AmazonRootCA1.pem"

// MQTT client ID — must match IoT Policy AllowConnect resource: medai-*
#define MQTT_CLIENT_ID  "medai-" DEVICE_ID

// ── MQTT topics (must match IoT Policy + IoT Rules SQL) ──────────────────────
// Device → Cloud (Publish)
#define TOPIC_TELEMETRY  "medai/device/" DEVICE_ID "/telemetry"
#define TOPIC_STATUS     "medai/device/" DEVICE_ID "/status"
#define TOPIC_HEARTBEAT  "medai/device/" DEVICE_ID "/heartbeat"
// Cloud → Device (Subscribe)
#define TOPIC_COMMAND    "medai/device/" DEVICE_ID "/command"

// ── Hardware pins ─────────────────────────────────────────────────────────────
// ULN2003 Stepper driver — 4 pins per motor, 3 motors total
// Motor 1 (Ngăn 1): IN1-IN4
#define STEPPER1_IN1    16
#define STEPPER1_IN2    17
#define STEPPER1_IN3    18
#define STEPPER1_IN4    19
// Motor 2 (Ngăn 2): IN1-IN4
#define STEPPER2_IN1    25
#define STEPPER2_IN2    26
#define STEPPER2_IN3    27
#define STEPPER2_IN4    14
// Motor 3 (Ngăn 3): IN1-IN4
#define STEPPER3_IN1    32
#define STEPPER3_IN2    33
#define STEPPER3_IN3    12
#define STEPPER3_IN4    13

// DHT22 temperature/humidity sensor
#define DHT_PIN         4
#define DHT_TYPE        DHT22

// IR obstacle sensor (detect if pill dispensed)
#define IR_SENSOR_1     36   // VP — Ngăn 1
#define IR_SENSOR_2     39   // VN — Ngăn 2
#define IR_SENSOR_3     34   // Ngăn 3

// OLED display (I2C)
#define OLED_SDA        21
#define OLED_SCL        22
#define OLED_ADDR       0x3C
#define OLED_WIDTH      128
#define OLED_HEIGHT     64

// LED & Buzzer
#define LED_STATUS_PIN  2
#define LED_ALERT_PIN   5
#define BUZZER_PIN      15

// ── Stepper motor config ──────────────────────────────────────────────────────
// 28BYJ-48 with ULN2003: 2048 steps = 1 full revolution
#define STEPS_PER_REV   2048
// Steps to open/close compartment (quarter turn = 512 steps)
#define STEPS_OPEN      512
#define STEPPER_RPM     10    // Slow = more torque, quieter

// ── Environment thresholds (must match backend config.py) ────────────────────
#define TEMP_MAX        35.0f  // °C — alert if exceeded
#define HUMIDITY_MAX    80.0f  // % — alert if exceeded
#define BATTERY_LOW     20     // % — alert if below
