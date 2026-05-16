#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "mqtt_manager.h"
#include "dispenser.h"
#include "inventory.h"
#include "stepper.h"
#include "config.h"

PubSubClient mqttClient;

// ----------------------------------------
// MQTT state → human readable
// ----------------------------------------

static const char* stateToString(int state) {
    switch (state) {
        case -4: return "TIMEOUT — TLS handshake failed (check certs)";
        case -3: return "CONNECTION LOST";
        case -2: return "CONNECTION FAILED — wrong broker or port";
        case -1: return "DISCONNECTED";
        case  0: return "CONNECTED";
        case  1: return "BAD PROTOCOL";
        case  2: return "BAD CLIENT ID";
        case  3: return "SERVER UNAVAILABLE";
        case  4: return "BAD CREDENTIALS";
        case  5: return "UNAUTHORIZED — check AWS IoT policy";
        default: return "UNKNOWN";
    }
}

// ----------------------------------------
// Command handlers
// ----------------------------------------

/*
  Expected MQTT command payload — "dispense":
  {
    "command": "dispense",
    "slot": 1,          ← 1-based (1, 2, or 3)
    "quantity": 2
  }
*/
static void handleDispense(JsonDocument& doc) {

    int slot     = doc["slot"]     | -1;
    int quantity = doc["quantity"] | 1;

    Serial.println("[MQTT] Command: dispense");
    Serial.print("[MQTT] Slot: ");
    Serial.print(slot);
    Serial.print(", Quantity: ");
    Serial.println(quantity);

    // Validate slot (convert 1-based to 0-based)
    if (slot < 1 || slot > MAX_SLOTS) {
        Serial.print("[MQTT] Invalid slot: ");
        Serial.println(slot);
        publishAlert("invalid_slot", "slot must be 1, 2, or 3");
        publishStatus("failed");
        return;
    }

    int slotIndex = slot - 1;  // convert to 0-based

    // Validate quantity
    if (quantity < 1 || quantity > 10) {
        Serial.println("[MQTT] Invalid quantity");
        publishAlert("invalid_quantity", "quantity must be 1-10");
        publishStatus("failed");
        return;
    }

    // Check inventory before starting
    if (!hasInventory(slotIndex, quantity)) {
        Serial.println("[MQTT] Not enough inventory");
        publishAlert("inventory_low", "not enough pills in slot");
        publishStatus("failed");
        return;
    }

    // Run dispense
    publishStatus("dispensing");

    bool success = dispensePills(slotIndex, quantity);

    if (success) {
        publishStatus("completed");
        publishInventory();  // send updated inventory after dispense
    } else {
        publishStatus("failed");
        publishInventory();
    }
}

/*
  Expected MQTT command payload — "set_inventory":
  {
    "command": "set_inventory",
    "slot": 1,
    "count": 10
  }
*/
static void handleSetInventory(JsonDocument& doc) {

    int slot  = doc["slot"]  | -1;
    int count = doc["count"] | -1;

    Serial.println("[MQTT] Command: set_inventory");

    if (slot < 1 || slot > MAX_SLOTS || count < 0) {
        Serial.println("[MQTT] Invalid set_inventory params");
        publishAlert("invalid_params", "slot 1-3, count >= 0");
        return;
    }

    setInventory(slot - 1, count);
    publishInventory();
    publishStatus("inventory_updated");
}

/*
  Expected MQTT command payload — "ping":
  { "command": "ping" }
*/
static void handlePing() {
    Serial.println("[MQTT] Command: ping");
    publishStatus("pong");
}

/*
  Expected MQTT command payload — "test_motor":
  Bypass IR, inventory, retry — just rotate motor to verify hardware.
  {
    "command": "test_motor",
    "slot": 1,           ← 1-based (1, 2, or 3)
    "steps": 512         ← optional, default 512 (quarter turn). Negative = reverse
  }
*/
static void handleTestMotor(JsonDocument& doc) {

    int slot  = doc["slot"]  | -1;
    int steps = doc["steps"] | STEPS_QUARTER_TURN;

    Serial.println("[MQTT] Command: test_motor");
    Serial.print("[MQTT] Slot: ");
    Serial.print(slot);
    Serial.print(", Steps: ");
    Serial.println(steps);

    if (slot < 1 || slot > MAX_SLOTS) {
        publishAlert("invalid_slot", "slot must be 1, 2, or 3");
        return;
    }

    publishStatus("test_motor_running");
    rotateStepper(slot - 1, steps);
    powerOffStepper(slot - 1);
    publishStatus("test_motor_done");
}

// ----------------------------------------
// MQTT Callback — entry point for all messages
// ----------------------------------------

static void mqttCallback(char* topic, byte* payload, unsigned int length) {

    Serial.println();
    Serial.println("[MQTT] ========== MESSAGE RECEIVED ==========");
    Serial.print("[MQTT] Topic: ");
    Serial.println(topic);
    Serial.print("[MQTT] Payload: ");

    for (unsigned int i = 0; i < length; i++) {
        Serial.print((char)payload[i]);
    }
    Serial.println();
    Serial.println("[MQTT] =========================================");

    // Parse JSON
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload, length);

    if (error) {
        Serial.print("[MQTT] JSON parse failed: ");
        Serial.println(error.c_str());
        publishAlert("parse_error", error.c_str());
        return;
    }

    const char* command = doc["command"];

    if (command == nullptr) {
        Serial.println("[MQTT] No 'command' field in payload");
        return;
    }

    // Route to correct handler
    if (strcmp(command, "dispense") == 0) {
        handleDispense(doc);

    } else if (strcmp(command, "set_inventory") == 0) {
        handleSetInventory(doc);

    } else if (strcmp(command, "ping") == 0) {
        handlePing();

    } else if (strcmp(command, "test_motor") == 0) {
        handleTestMotor(doc);

    } else {
        Serial.print("[MQTT] Unknown command: ");
        Serial.println(command);
        publishAlert("unknown_command", command);
    }
}

// ----------------------------------------
// Public
// ----------------------------------------

void setupMQTT(WiFiClientSecure& secureClient) {

    mqttClient.setClient(secureClient);
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setKeepAlive(60);
    mqttClient.setBufferSize(1024);

    Serial.println("[MQTT] Setup complete");
    Serial.print("[MQTT] Broker: ");
    Serial.println(MQTT_BROKER);
}

bool connectMQTT() {

    Serial.println("[MQTT] Attempting connection...");
    Serial.print("[MQTT] Client ID: ");
    Serial.println(DEVICE_ID);

    bool result = mqttClient.connect(DEVICE_ID);

    Serial.print("[MQTT] State: ");
    Serial.print(mqttClient.state());
    Serial.print(" → ");
    Serial.println(stateToString(mqttClient.state()));

    if (!result) {
        Serial.println("[MQTT] Connection FAILED");
        return false;
    }

    Serial.println("[MQTT] Connected!");

    bool subResult = mqttClient.subscribe(MQTT_COMMAND_TOPIC);
    Serial.print("[MQTT] Subscribe to command topic: ");
    Serial.println(subResult ? "OK" : "FAILED");
    Serial.print("[MQTT] Subscribed topic name: '");
    Serial.print(MQTT_COMMAND_TOPIC);
    Serial.println("'");

    publishStatus("online");
    publishInventory();

    // Self-test: publish to our own command topic to verify subscribe works.
    // If we receive this message back, the subscribe + receive path is OK
    // and any later issue is purely a topic-name mismatch from the AWS Console.
    Serial.println("[MQTT] === SELF-TEST: publishing ping to own command topic ===");
    bool selfTest = mqttClient.publish(MQTT_COMMAND_TOPIC, "{\"command\":\"ping\"}");
    Serial.print("[MQTT] Self-test publish: ");
    Serial.println(selfTest ? "OK" : "FAILED");

    return true;
}

void mqttLoop() {

    if (!mqttClient.connected()) {
        Serial.print("[MQTT] Disconnected — state: ");
        Serial.println(stateToString(mqttClient.state()));
    }

    mqttClient.loop();
}

void publishStatus(const char* status) {

    StaticJsonDocument<128> doc;
    doc["device"] = DEVICE_ID;
    doc["status"] = status;

    char buffer[128];
    serializeJson(doc, buffer);

    bool ok = mqttClient.publish(MQTT_STATUS_TOPIC, buffer);
    Serial.print("[MQTT] publishStatus('");
    Serial.print(status);
    Serial.print("'): ");
    Serial.println(ok ? "OK" : "FAILED");
}

void publishAlert(const char* alertType, const char* detail) {

    StaticJsonDocument<200> doc;
    doc["device"] = DEVICE_ID;
    doc["alert"]  = alertType;
    doc["detail"] = detail;

    char buffer[200];
    serializeJson(doc, buffer);

    bool ok = mqttClient.publish(MQTT_ALERT_TOPIC, buffer);
    Serial.print("[MQTT] publishAlert('");
    Serial.print(alertType);
    Serial.print("'): ");
    Serial.println(ok ? "OK" : "FAILED");
}

void publishInventory() {

    StaticJsonDocument<200> doc;
    doc["device"] = DEVICE_ID;

    JsonObject inv = doc.createNestedObject("inventory");
    inv["slot1"] = getInventory(0);
    inv["slot2"] = getInventory(1);
    inv["slot3"] = getInventory(2);

    char buffer[200];
    serializeJson(doc, buffer);

    bool ok = mqttClient.publish(MQTT_TELEMETRY_TOPIC, buffer);
    Serial.print("[MQTT] publishInventory: ");
    Serial.println(ok ? "OK" : "FAILED");
    Serial.println(buffer);
}
