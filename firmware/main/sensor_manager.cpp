#include "sensor_manager.h"
#include "config.h"
#include <DHT.h>
#include <time.h>

static DHT dht(DHT_PIN, DHT_TYPE);

void SensorManager::init() {
    dht.begin();
    // Configure NTP
    configTime(7 * 3600, 0, "pool.ntp.org", "time.nist.gov");
    Serial.println("[Sensor] DHT22 initialized");
}

SensorData SensorManager::read() {
    SensorData data;
    data.temperature  = dht.readTemperature();
    data.humidity     = dht.readHumidity();
    data.batteryLevel = readBatteryPercent();

    // ISO timestamp
    time_t now;
    time(&now);
    char buf[32];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", gmtime(&now));
    data.timestamp = String(buf);

    if (isnan(data.temperature)) data.temperature = -1;
    if (isnan(data.humidity))    data.humidity    = -1;

    return data;
}

int SensorManager::readBatteryPercent() {
    // No battery ADC in current hardware build — return fixed value
    // TODO: Add voltage divider circuit if battery monitoring needed
    return 100;
}
