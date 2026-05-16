# 🚀 QUICK START - MEDAI CABINET

Hướng dẫn nhanh để chạy hệ thống trong 10 phút.

---

## ✅ CHECKLIST TRƯỚC KHI BẮT ĐẦU

- [ ] Node.js 18+ đã cài
- [ ] Python 3.11+ đã cài
- [ ] VS Code + PlatformIO đã cài
- [ ] Tài khoản AWS đã có (hoặc AWS Academy)
- [ ] ESP32 + cáp USB

---

## 📦 BƯỚC 1: CÀI ĐẶT DEPENDENCIES

```cmd
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ..\frontend
npm install
```

---

## ☁️ BƯỚC 2: SETUP AWS (5 PHÚT)

```cmd
cd ..\infrastructure

# Tạo file .env với AWS credentials
echo AWS_ACCESS_KEY_ID=YOUR_KEY > .env
echo AWS_SECRET_ACCESS_KEY=YOUR_SECRET >> .env
echo AWS_REGION=ap-southeast-1 >> .env

# Chạy script setup
pip install boto3
python aws_setup.py
```

**Lưu lại output:**
- IoT Endpoint: `xxxxxx-ats.iot.ap-southeast-1.amazonaws.com`
- Thing Name: `medai-cabinet-device`

---

## 🔧 BƯỚC 3: CẤU HÌNH .ENV

### Backend (.env)
```cmd
cd ..\backend
copy .env.example .env
```

Sửa file `.env`:
```env
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_REGION=ap-southeast-1

IOT_ENDPOINT=xxxxxx-ats.iot.ap-southeast-1.amazonaws.com
IOT_THING_NAME=medai-cabinet-device

BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Frontend (.env)
```cmd
cd ..\frontend
echo REACT_APP_API_URL=http://localhost:8000 > .env
```

---

## 🚀 BƯỚC 4: CHẠY BACKEND + FRONTEND

### Terminal 1 - Backend
```cmd
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Terminal 2 - Frontend
```cmd
cd frontend
npm start
```

**Kiểm tra:**
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 📱 BƯỚC 5: NẠP FIRMWARE ESP32

### 5.1. Copy certificates
```cmd
cd medai-esp32
mkdir data

copy ..\backend\certs\medai-cabinet-device.cert.pem data\device.cert.pem
copy ..\backend\certs\medai-cabinet-device.private.key data\device.key
```

### 5.2. Tạo file data/aws_config.txt
```txt
ap-southeast-1
xxxxxx-ats.iot.ap-southeast-1.amazonaws.com
medai-cabinet-device
```

### 5.3. Upload firmware
```cmd
# Trong VS Code với PlatformIO
# 1. Mở folder medai-esp32
# 2. Click "Upload" (hoặc Ctrl+Alt+U)
# 3. Click "Upload Filesystem Image"

# Hoặc dùng CLI:
pio run --target upload
pio run --target uploadfs
```

### 5.4. Xem log
```cmd
pio device monitor --baud 115200
```

---

## 📶 BƯỚC 6: KẾT NỐI WIFI (ĐIỆN THOẠI)

1. **Cắm ESP32 vào nguồn** (USB hoặc adapter 5V)

2. **Mở WiFi trên điện thoại**
   - Tìm mạng: `MedAI-Setup`
   - Password: `medai1234`

3. **Trang config tự động mở**
   - Nếu không, vào: http://192.168.4.1

4. **Chọn WiFi nhà bạn**
   - Nhập password
   - Click "Save & Connect"

5. **Chờ ESP32 kết nối**
   - Xem log serial:
   ```
   [WIFI] Connected to: YourWiFi
   [MQTT] Connected to AWS IoT
   ```

---

## ✅ BƯỚC 7: KIỂM TRA

### Test Frontend
1. Mở http://localhost:3000
2. Vào **Medications** → Add thuốc mới
3. Vào **Schedules** → Tạo lịch uống thuốc
4. Vào **AI Triage** → Nhập triệu chứng
5. Vào **Device Monitor** → Xem dữ liệu từ ESP32

### Test ESP32
1. Trong Frontend, click **Dispense** trên một thuốc
2. Xem log serial ESP32:
   ```
   [MQTT] Received command: dispense
   [DISPENSER] Opening slot 1...
   ```

### Test AWS
1. Vào AWS Console → IoT Core → Test
2. Subscribe topic: `medai/device/+/telemetry`
3. Thấy message mỗi 30 giây → ✅ OK

---

## 🐛 XỬ LÝ LỖI NHANH

### Backend không chạy
```cmd
# Kiểm tra virtual env
venv\Scripts\activate

# Cài lại packages
pip install -r requirements.txt
```

### Frontend lỗi icon
```cmd
npm install react-icons
```

### ESP32 không upload
```cmd
# Giữ nút BOOT khi upload
# Hoặc sửa platformio.ini:
upload_speed = 115200
```

### ESP32 không kết nối MQTT
```cmd
# Kiểm tra certificates đã upload
pio run --target uploadfs

# Kiểm tra IoT endpoint trong data/aws_config.txt
```

---

## 📚 TÀI LIỆU CHI TIẾT

Xem file **HUONG_DAN_CHAY.md** để biết thêm chi tiết về:
- Cài đặt môi trường
- Cấu hình AWS từng bước
- Xử lý lỗi chi tiết
- Tips & tricks

---

## 🎯 NEXT STEPS

Sau khi chạy thành công:

1. **Thêm dữ liệu mẫu**
   - 3-5 loại thuốc
   - Lịch uống thuốc hàng ngày

2. **Test tính năng**
   - Dispense thuốc từ Frontend
   - AI Triage với triệu chứng khác nhau
   - Xem biểu đồ nhiệt độ/độ ẩm

3. **Kết nối phần cứng**
   - Gắn servo, DHT22, OLED
   - Test cơ cấu phát thuốc thật

---

**Thời gian ước tính:**
- Setup AWS: 5 phút
- Cài đặt + config: 3 phút
- Upload firmware: 2 phút
- Kết nối WiFi: 1 phút
- **Tổng: ~10-15 phút**

**Chúc bạn thành công! 🎉**
