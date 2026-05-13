#include "display_manager.h"
#include "config.h"
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <Wire.h>

static Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);

void DisplayManager::init() {
    Wire.begin(OLED_SDA, OLED_SCL);
    if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("[Display] SSD1306 init failed");
        return;
    }
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("MedAI Cabinet");
    display.display();
    Serial.println("[Display] OLED initialized");
}

void DisplayManager::clear() {
    display.clearDisplay();
    display.display();
}

void DisplayManager::showMessage(const char* msg) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 24);
    display.println(msg);
    display.display();
}

void DisplayManager::showReady(const char* deviceId) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("MedAI Cabinet");
    display.drawLine(0, 10, OLED_WIDTH, 10, SSD1306_WHITE);
    display.setCursor(0, 16);
    display.printf("ID: %s", deviceId);
    display.setCursor(0, 28);
    display.println("Status: Ready");
    display.display();
}

void DisplayManager::showDispensing(int compartment, int quantity) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("Dispensing...");
    display.setTextSize(2);
    display.setCursor(0, 20);
    display.printf("C%d x%d", compartment, quantity);
    display.display();
}

void DisplayManager::showAlert(const char* msg) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("! ALERT !");
    display.drawLine(0, 10, OLED_WIDTH, 10, SSD1306_WHITE);
    display.setCursor(0, 16);
    display.println(msg);
    display.display();
}
