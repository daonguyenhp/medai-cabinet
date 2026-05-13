# MedAI Cabinet

Hệ thống tủ thuốc thông minh tích hợp AI — giúp người cao tuổi và bệnh nhân quản lý thuốc an toàn tại nhà.

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Cloud                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ DynamoDB │  │  S3      │  │ IoT Core │  │Bedrock │ │
│  │ (data)   │  │ (images) │  │ (MQTT)   │  │(Claude)│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│         ▲              ▲            ▲ ▼          ▲      │
│         └──────────────┴────────────┴────────────┘      │
│                         FastAPI Backend                  │
└─────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │ REST/WebSocket                     │ MQTT/TLS
┌────────┴────────┐                 ┌─────────┴────────┐
│  React Frontend │                 │  ESP32 Firmware  │
│  (Web App)      │                 │  (Hardware)      │
└─────────────────┘                 └──────────────────┘
```

## Cấu trúc thư mục

```
medai-cabinet/
├── backend/              # FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── models/           # Pydantic models
│   ├── routers/          # API endpoints
│   └── services/         # Business logic (DynamoDB, IoT, AI)
├── frontend/             # React frontend
│   ├── src/
│   │   ├── api/          # API client functions
│   │   ├── components/   # Reusable UI components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── pages/        # Page components
│   │   └── styles/       # CSS files
│   └── package.json
├── firmware/             # ESP32 firmware (PlatformIO)
│   ├── platformio.ini
│   └── main/             # C++ source files
├── infrastructure/       # AWS setup scripts
│   └── aws_setup.py
└── docker-compose.yml
```

## Tính năng

- **Quản lý thuốc** — thêm/sửa/xóa thuốc, theo dõi tồn kho, cảnh báo hết hạn
- **Lịch uống thuốc** — đặt lịch nhắc nhở, ghi nhận liều đã uống
- **AI Triage** — phân tích triệu chứng bằng Amazon Bedrock (Claude 3)
- **Điều khiển phần cứng** — mở ngăn thuốc qua AWS IoT Core → ESP32
- **Giám sát thiết bị** — nhiệt độ, độ ẩm, pin, trạng thái kết nối
- **Cảnh báo** — thông báo cho người chăm sóc qua SNS

## Cài đặt & Chạy

### Yêu cầu

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (tuỳ chọn)
- Tài khoản AWS với quyền DynamoDB, IoT Core, Bedrock, SNS

### 1. Backend

```bash
cd backend
cp .env.example .env
# Điền thông tin AWS vào .env

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

Mở: http://localhost:3000

### 3. Docker Compose (cả hai cùng lúc)

```bash
# Tạo file .env từ mẫu
cp backend/.env.example backend/.env

docker-compose up --build
```

### 4. Firmware (ESP32)

```bash
cd firmware
# Cài PlatformIO: https://platformio.org/install

# Sao chép certificates vào firmware/data/certs/
# Chỉnh WIFI_SSID và WIFI_PASSWORD trong platformio.ini

pio run --target upload
pio run --target uploadfs   # Upload certificates lên SPIFFS
```

## Cấu hình AWS

Chạy script setup để tạo tất cả tài nguyên AWS:

```bash
cd infrastructure
pip install boto3
python aws_setup.py
```

Script sẽ tạo:
- DynamoDB tables với GSI
- S3 bucket
- IoT Thing, certificates, policies
- SNS topics
- IAM roles

## API Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/v1/medications/` | Danh sách thuốc |
| POST | `/api/v1/medications/` | Thêm thuốc |
| POST | `/api/v1/medications/{id}/dispense` | Phát thuốc |
| GET | `/api/v1/schedules/today` | Lịch hôm nay |
| POST | `/api/v1/schedules/dose-history` | Ghi nhận liều |
| POST | `/api/v1/ai-triage/analyze` | Phân tích triệu chứng |
| POST | `/api/v1/ai-triage/chat` | Chat với AI |
| GET | `/api/v1/dashboard/summary` | Tổng quan |
| GET | `/api/v1/alerts/` | Danh sách cảnh báo |
| GET | `/api/v1/devices/{id}/telemetry` | Dữ liệu cảm biến |

## Hardware

- **MCU**: ESP32 DevKit V1
- **Servo**: 3× SG90 (3 ngăn thuốc)
- **Cảm biến**: DHT22 (nhiệt độ/độ ẩm)
- **Màn hình**: OLED SSD1306 128×64 (I2C)
- **Cảnh báo**: LED + Buzzer thụ động
- **Kết nối**: WiFi 2.4GHz + MQTT/TLS → AWS IoT Core

## License

MIT
