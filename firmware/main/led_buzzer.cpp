#include "led_buzzer.h"
#include "config.h"

void LedBuzzer::init() {
    pinMode(LED_STATUS_PIN, OUTPUT);
    pinMode(LED_ALERT_PIN,  OUTPUT);
    pinMode(BUZZER_PIN,     OUTPUT);
    digitalWrite(LED_STATUS_PIN, LOW);
    digitalWrite(LED_ALERT_PIN,  LOW);
    digitalWrite(BUZZER_PIN,     LOW);
}

void LedBuzzer::beep(int times) {
    for (int i = 0; i < times; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
        if (i < times - 1) delay(100);
    }
}

void LedBuzzer::alert() {
    setAlertLed(true);
    for (int i = 0; i < 3; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(200);
        digitalWrite(BUZZER_PIN, LOW);
        delay(100);
    }
    setAlertLed(false);
}

void LedBuzzer::setStatusLed(bool on) {
    digitalWrite(LED_STATUS_PIN, on ? HIGH : LOW);
}

void LedBuzzer::setAlertLed(bool on) {
    digitalWrite(LED_ALERT_PIN, on ? HIGH : LOW);
}
