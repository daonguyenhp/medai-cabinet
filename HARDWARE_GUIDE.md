# MedAI Cabinet — Hướng dẫn Hardware

## 1. Danh sách linh kiện cần mua

### ✅ Danh sách bạn đề xuất — Đánh giá

| # | Linh kiện | Số lượng | Phù hợp? | Ghi chú |
|---|-----------|----------|----------|---------|
| 1 | DHT22 AM2302 Ra chân | 1 | ✅ Dùng được | Đúng loại firmware đang dùng |
| 2 | Cảm biến vật cản hồng ngoại | 3 | ✅ Dùng được | 1 cái/ngăn để detect thuốc |
| 3 | TMB09A03 Buzzer 3V 9×5.5mm | 1 | ⚠️ Cần thêm transistor | Buzzer passive, cần NPN (BC547/S8050) để drive từ ESP32 |
| 4 | Module ULN2003 + động cơ 5V | 3 | ✅ Hoàn hảo | Đúng loại firmware đang dùng (28BYJ-48) |
| 5 | Đế ra chân cổng Type-C | 1 | ✅ Dùng được | Cấp nguồn 5V cho toàn mạch |
| 6 | Board đồng đục lỗ PCB 9×15cm | 2 | ✅ Đủ | 1 cho ESP32+sensors, 1 cho 3 ULN2003 |

### 📦 Linh kiện cần mua thêm (chưa có trong danh sách)

| # | Linh kiện | Số lượng | Giá ước tính | Mua ở đâu |
|---|-----------|----------|--------------|-----------|
| 1 | **ESP32 DevKit V1** (38 pin) | 1 | ~80k | Shopee / Thegioiic |
| 2 | **OLED 0.96" I2C SSD1306** (128×64) | 1 | ~35k | Shopee |
| 3 | **LED 5mm** — xanh lá (status) | 1 | ~2k | Shopee |
| 4 | **LED 5mm** — đỏ (alert) | 1 | ~2k | Shopee |
| 5 | **Transistor NPN BC547** hoặc S8050 | 1 | ~2k | Shopee |
| 6 | **Điện trở 1kΩ** | 3 | ~1k | Shopee |
| 7 | **Điện trở 330Ω** | 2 | ~1k | Shopee |
| 8 | **Tụ 100µF 10V** | 1 | ~3k | Shopee (lọc nguồn) |
| 9 | **Dây jumper** (đực-đực, đực-cái) | 1 bộ | ~15k | Shopee |
| 10 | **Header pin** 2.54mm | 1 bộ | ~10k | Shopee |
| 11 | **Nguồn 5V 2A** (adapter hoặc sạc USB-C) | 1 | ~30k | Shopee |

> **Tổng chi phí ước tính:** ~200–250k VNĐ (chưa tính linh kiện bạn đã có)

---

## 2. Sơ đồ kết nối (Wiring Diagram)

```
                    ESP32 DevKit V1
                   ┌──────────────┐
              3.3V │ 3V3      GND │ GND ──────────────── GND chung
               GND │ GND      VIN │ 5V ─────────────────┐
                   │              │                      │
    DHT22 DATA ────│ GPIO4        │                   5V Rail
                   │              │                (từ Type-C)
   OLED SDA ───────│ GPIO21       │
   OLED SCL ───────│ GPIO22       │
                   │              │
  BUZZER (BC547) ──│ GPIO15       │
  LED STATUS ──────│ GPIO2        │
  LED ALERT ───────│ GPIO5        │
                   │              │
  IR Sensor 1 ─────│ GPIO36 (VP)  │
  IR Sensor 2 ─────│ GPIO39 (VN)  │
  IR Sensor 3 ─────│ GPIO34       │
                   │              │
  ULN2003 #1 IN1 ──│ GPIO16       │
  ULN2003 #1 IN2 ──│ GPIO17       │
  ULN2003 #1 IN3 ──│ GPIO18       │
  ULN2003 #1 IN4 ──│ GPIO19       │
                   │              │
  ULN2003 #2 IN1 ──│ GPIO25       │
  ULN2003 #2 IN2 ──│ GPIO26       │
  ULN2003 #2 IN3 ──│ GPIO27       │
  ULN2003 #2 IN4 ──│ GPIO14       │
                   │              │
  ULN2003 #3 IN1 ──│ GPIO32       │
  ULN2003 #3 IN2 ──│ GPIO33       │
  ULN2003 #3 IN3 ──│ GPIO12       │
  ULN2003 #3 IN4 ──│ GPIO13       │
                   └──────────────┘
```

---

## 3. Hướng dẫn đấu nối từng linh kiện

### 3.1 DHT22 (Cảm biến nhiệt độ/độ ẩm)

```
DHT22 (nhìn mặt trước, 4 chân từ trái sang phải):
  Chân 1 (VCC)  → 3.3V ESP32
  Chân 2 (DATA) → GPIO4 ESP32  +  điện trở 10kΩ kéo lên 3.3V
  Chân 3 (NC)   → Bỏ trống
  Chân 4 (GND)  → GND

⚠️ Nếu mua loại "ra chân" (module 3 chân) thì đã có điện trở sẵn:
  VCC  → 3.3V
  DATA → GPIO4
  GND  → GND
```

### 3.2 ULN2003 + Động cơ 28BYJ-48 (3 bộ)

```
Mỗi bộ ULN2003:
  Module ULN2003:
    IN1 → ESP32 GPIO (xem bảng dưới)
    IN2 → ESP32 GPIO
    IN3 → ESP32 GPIO
    IN4 → ESP32 GPIO
    VCC (+) → 5V Rail (KHÔNG dùng 3.3V ESP32)
    GND (-) → GND chung

  Động cơ 28BYJ-48:
    Cắm thẳng vào connector 5 chân trên board ULN2003

Bảng GPIO:
  ┌────────┬──────┬──────┬──────┬──────┐
  │ Module │  IN1 │  IN2 │  IN3 │  IN4 │
  ├────────┼──────┼──────┼──────┼──────┤
  │ Ngăn 1 │  16  │  17  │  18  │  19  │
  │ Ngăn 2 │  25  │  26  │  27  │  14  │
  │ Ngăn 3 │  32  │  33  │  12  │  13  │
  └────────┴──────┴──────┴──────┴──────┘

⚠️ QUAN TRỌNG: VCC của ULN2003 phải là 5V riêng,
   KHÔNG lấy từ chân 3.3V của ESP32 (không đủ dòng).
   Lấy từ cùng nguồn 5V với ESP32 VIN.
```

### 3.3 Cảm biến IR vật cản (3 cái)

```
Mỗi module IR:
  VCC  → 3.3V hoặc 5V (module thường chịu cả hai)
  GND  → GND
  OUT  → GPIO (xem bảng)

  Ngăn 1: OUT → GPIO36
  Ngăn 2: OUT → GPIO39
  Ngăn 3: OUT → GPIO34

⚠️ GPIO36, 39, 34 là INPUT ONLY trên ESP32 — không dùng được OUTPUT.
   Đây là lý do chọn các chân này cho cảm biến.

Cách đặt cảm biến:
  - Gắn ở đáy ngăn thuốc, hướng lên
  - Khi có thuốc: OUT = LOW (vật cản)
  - Khi lấy thuốc: OUT = HIGH (không có vật cản)
```

### 3.4 Buzzer TMB09A03 (3V passive)

```
Buzzer passive cần transistor để drive:

  ESP32 GPIO15 ──[1kΩ]── Base (B) của BC547
  GND ─────────────────── Emitter (E) của BC547
  Collector (C) ────────── Chân âm (-) Buzzer
  Chân dương (+) Buzzer ── 3.3V

Sơ đồ:
  GPIO15 ──R1kΩ──┐
                 B
  GND ─────────E   C──── Buzzer(-) ──── Buzzer(+) ──── 3.3V
                 BC547

⚠️ Buzzer TMB09A03 là 3V — dùng 3.3V ESP32 là vừa đủ.
   Không nối thẳng GPIO vào buzzer (quá dòng, hỏng ESP32).
```

### 3.5 OLED SSD1306 0.96" I2C

```
  VCC → 3.3V ESP32
  GND → GND
  SDA → GPIO21 ESP32
  SCL → GPIO22 ESP32

Không cần điện trở pull-up (module đã có sẵn).
```

### 3.6 LED Status & Alert

```
LED xanh (Status):
  GPIO2 ──[330Ω]── Anode(+) LED ── Cathode(-) ── GND

LED đỏ (Alert):
  GPIO5 ──[330Ω]── Anode(+) LED ── Cathode(-) ── GND
```

### 3.7 Nguồn điện (Type-C)

```
Đế Type-C:
  VBUS (5V) ──┬── VIN ESP32 (qua diode hoặc trực tiếp)
              └── VCC ULN2003 ×3
              └── Tụ 100µF (lọc nhiễu)
  GND ──────── GND chung tất cả

⚠️ Dùng adapter 5V 2A trở lên.
   3 motor + ESP32 + sensors có thể tiêu thụ ~800mA peak.
```

---

## 4. Bố trí PCB

### PCB 1 (9×15cm) — Bo mạch chính

```
┌─────────────────────────────────┐
│  [ESP32 DevKit]                 │
│                                 │
│  [OLED]    [DHT22]              │
│                                 │
│  [IR1] [IR2] [IR3]              │
│                                 │
│  [LED_G] [LED_R] [BUZZER]       │
│                                 │
│  [Type-C Power]  [Tụ 100µF]    │
└─────────────────────────────────┘
```

### PCB 2 (9×15cm) — Bo mạch motor

```
┌─────────────────────────────────┐
│  [ULN2003 #1] ──── Motor 1      │
│  [ULN2003 #2] ──── Motor 2      │
│  [ULN2003 #3] ──── Motor 3      │
│                                 │
│  [Header kết nối PCB1]          │
└─────────────────────────────────┘
```

---

## 5. Cơ chế hoạt động ngăn thuốc

```
Cơ chế đề xuất — Đĩa xoay:

  ┌──────────────────────────────┐
  │         Ngăn thuốc           │
  │  ┌────┐  ┌────┐  ┌────┐     │
  │  │ A  │  │ B  │  │ C  │     │  ← 3 ô chứa thuốc
  │  └────┘  └────┘  └────┘     │
  │         [Đĩa xoay]           │
  │              │               │
  │         [Motor 28BYJ-48]     │
  │              │               │
  │         [Lỗ thoát thuốc]     │
  │              ↓               │
  │         [IR Sensor]          │
  └──────────────────────────────┘

Khi nhận lệnh dispense:
  1. Motor quay 512 steps (1/4 vòng)
  2. Ô thuốc thẳng hàng với lỗ thoát
  3. Thuốc rơi xuống → IR sensor phát hiện
  4. Chờ người dùng lấy (IR = HIGH)
  5. Motor quay thêm 512 steps → đóng lại
```

---

## 6. Kết nối Software ↔ Hardware

### Luồng dữ liệu đầy đủ

```
┌──────────────────────────────────────────────────────────────────┐
│                         LUỒNG ĐIỀU KHIỂN                         │
│                                                                  │
│  Web App (React)                                                 │
│      │                                                           │
│      │ Click "Lấy thuốc"                                        │
│      ↓                                                           │
│  FastAPI Backend                                                 │
│      │ POST /api/v1/medications/{id}/dispense                   │
│      │                                                           │
│      ├─ Kiểm tra tồn kho DynamoDB                               │
│      ├─ Trừ stock_count                                          │
│      │                                                           │
│      ↓                                                           │
│  AWS IoT Core (boto3 iot-data)                                  │
│      │ Publish MQTT:                                             │
│      │ Topic: medai/device/medai-esp32-001/command              │
│      │ Payload: {"command":"dispense",                          │
│      │           "payload":{"compartment":1,"quantity":2}}      │
│      │                                                           │
│      ↓                                                           │
│  ESP32 (MQTT Subscribe)                                         │
│      │ onMessage() nhận lệnh                                    │
│      │                                                           │
│      ├─ ULN2003 #1 → Motor quay → Mở ngăn 1                    │
│      ├─ IR Sensor phát hiện thuốc rơi                           │
│      ├─ Chờ người lấy (IR = HIGH)                               │
│      └─ Motor quay ngược → Đóng ngăn                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                         LUỒNG TELEMETRY                          │
│                                                                  │
│  ESP32 (mỗi 60 giây)                                            │
│      │ DHT22 đọc nhiệt độ/độ ẩm                                 │
│      │                                                           │
│      ↓                                                           │
│  AWS IoT Core (MQTT Publish)                                    │
│      │ Topic: medai/device/medai-esp32-001/telemetry            │
│      │ Payload: {"temperature":26.5,"humidity":58,...}          │
│      │                                                           │
│      ↓ (IoT Rule forward)                                        │
│  FastAPI Backend                                                 │
│      │ POST /api/v1/iot/telemetry                               │
│      │                                                           │
│      ├─ Lưu vào DynamoDB (medai-device-telemetry)               │
│      ├─ Kiểm tra ngưỡng nhiệt độ/độ ẩm                         │
│      └─ Tạo Alert nếu vượt ngưỡng → SNS → Caregiver            │
│                                                                  │
│  Web App (polling 30s)                                          │
│      │ GET /api/v1/devices/{id}/telemetry                       │
│      └─ Hiển thị trên Dashboard                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Hướng dẫn flash firmware từng bước

### Bước 1 — Cài đặt môi trường

```bash
# Cài VS Code + PlatformIO extension
# Hoặc cài PlatformIO CLI:
pip install platformio
```

### Bước 2 — Cấu hình WiFi

Mở `firmware/platformio.ini`, sửa:
```ini
build_flags =
    -DWIFI_SSID=\"TenWifiCuaBan\"
    -DWIFI_PASSWORD=\"MatKhauWifi\"
```

### Bước 3 — Copy certificates

```powershell
# Chạy từ thư mục gốc project
.\medai-cabinet\firmware\copy_certs.ps1
```

Hoặc thủ công:
```
backend/certs/medai-cabinet-device.cert.pem   → firmware/data/certs/
backend/certs/medai-cabinet-device.private.key → firmware/data/certs/
# Download AmazonRootCA1.pem từ:
# https://www.amazontrust.com/repository/AmazonRootCA1.pem
# → firmware/data/certs/AmazonRootCA1.pem
```

### Bước 4 — Upload certificates lên SPIFFS

```bash
cd medai-cabinet/firmware
pio run --target uploadfs
# Chờ "Success" — certificates đã lên ESP32
```

### Bước 5 — Upload firmware

```bash
pio run --target upload
# Chờ "Success"
```

### Bước 6 — Kiểm tra Serial Monitor

```bash
pio device monitor --baud 115200
```

Output mong đợi:
```
[MedAI] Booting...
[Stepper] Initialized (3 compartments, ULN2003)
[Sensor] DHT22 initialized
[WiFi] Connecting to TenWifiCuaBan...
[WiFi] Connected. IP: 192.168.1.x
[IoT] Connecting MQTT... connected
[IoT] Subscribed to medai/device/medai-esp32-001/command
[MedAI] Ready.
```

---

## 8. Cập nhật IoT Policy trên AWS

Policy hiện tại chỉ cho `sdk/test/*`. Cần cập nhật để cho phép MedAI topics:

```bash
cd medai-cabinet/infrastructure
pip install boto3 python-dotenv
python update_iot_policy.py
```

Hoặc thủ công trên AWS Console:
1. Vào **IoT Core → Security → Policies**
2. Chọn `medai-cabinet-device-Policy`
3. Click **Edit active version**
4. Paste nội dung từ `backend/certs/medai-cabinet-device-Policy-updated.json`
5. Click **Save as new version** → **Set as active**

---

## 9. Test end-to-end

### Test 1 — Kiểm tra MQTT kết nối

```bash
# Trên AWS Console → IoT Core → MQTT test client
# Subscribe: medai/device/medai-esp32-001/telemetry
# Chờ 60s → thấy JSON telemetry = ESP32 đang hoạt động
```

### Test 2 — Gửi lệnh dispense từ web

```
1. Chạy backend: cd backend && uvicorn main:app --reload
2. Chạy frontend: cd frontend && npm start
3. Vào trang "Tủ Thuốc" → chọn thuốc → click "Lấy thuốc"
4. Quan sát Serial Monitor ESP32 → motor phải quay
```

### Test 3 — Kiểm tra telemetry trên Dashboard

```
1. Vào trang "Thiết Bị"
2. Thấy nhiệt độ/độ ẩm từ DHT22 = pipeline hoàn chỉnh
```

---

## 10. Troubleshooting

| Triệu chứng | Nguyên nhân | Fix |
|-------------|-------------|-----|
| Motor không quay | VCC ULN2003 lấy từ 3.3V | Đổi sang 5V |
| MQTT connect failed (rc=-2) | Cert sai hoặc Policy chưa update | Kiểm tra bước 8 |
| DHT22 trả về -1 | Thiếu điện trở pull-up | Thêm 10kΩ từ DATA lên 3.3V |
| IR sensor luôn LOW | Cảm biến quá gần vật | Điều chỉnh biến trở trên module |
| ESP32 reset liên tục | Nguồn không đủ dòng | Dùng adapter 5V 2A |
| OLED không hiển thị | Địa chỉ I2C sai | Scan I2C, thử 0x3C hoặc 0x3D |
