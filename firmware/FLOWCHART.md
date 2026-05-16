# Lưu đồ thuật toán — MedAI Cabinet ESP32 Firmware

> **Cách dùng**: Vào https://mermaid.live/ và paste **TỪNG SƠ ĐỒ MỘT** (không paste cả file).
> Hoặc mở file này trong VS Code với extension "Markdown Preview Mermaid Support".

---

## 1. Setup — Khởi động thiết bị

```mermaid
flowchart TD
    Start([Power ON]) --> InitSerial[Khoi tao Serial 115200]
    InitSerial --> InitHW[Khoi tao phan cung<br/>3 Stepper Motors<br/>IR Sensor<br/>Inventory mac dinh 10 vien/ngan]
    InitHW --> ConnWiFi{Ket noi WiFi?}
    ConnWiFi -->|That bai| RetryWiFi[Cho 500ms thu lai]
    RetryWiFi --> ConnWiFi
    ConnWiFi -->|Thanh cong| SyncTime[Dong bo NTP]
    SyncTime --> LoadCert{Load certs<br/>tu SPIFFS}
    LoadCert -->|Loi| Halt[HALT - bao loi]
    LoadCert -->|OK| MQTTConn{Ket noi MQTT<br/>AWS IoT Core}
    MQTTConn -->|That bai| WaitMQTT[Cho 5s]
    WaitMQTT --> MQTTConn
    MQTTConn -->|OK| Sub[Subscribe topic command]
    Sub --> PubOnline[Publish status online<br/>va inventory]
    PubOnline --> MainLoop([Vao Main Loop])

    style Start fill:#8B1A1A,color:#fff
    style MainLoop fill:#8B1A1A,color:#fff
    style Halt fill:#D32F2F,color:#fff
```

---

## 2. Main Loop — Vòng lặp chính

```mermaid
flowchart TD
    Loop([Main Loop]) --> CheckMQTT{MQTT con<br/>ket noi?}
    CheckMQTT -->|Khong| Reconnect[Reconnect MQTT<br/>moi 5s]
    Reconnect --> Loop
    CheckMQTT -->|Co| Process[mqttClient.loop<br/>xu ly message den]
    Process --> CheckTele{Da toi chu ky<br/>telemetry 60s?}
    CheckTele -->|Co| PubInv[Publish inventory<br/>len telemetry topic]
    PubInv --> Sleep[delay 10ms]
    CheckTele -->|Khong| Sleep
    Sleep --> Loop

    style Loop fill:#8B1A1A,color:#fff
```

---

## 3. Xử lý lệnh dispense — Khi nhận command từ backend

```mermaid
flowchart TD
    Msg([Nhan MQTT message]) --> Parse{Parse JSON?}
    Parse -->|Loi| Alert1[Publish alert parse_error]
    Alert1 --> End1([END])
    Parse -->|OK| Cmd{command type?}

    Cmd -->|ping| Pong[Publish status pong]
    Pong --> End2([END])

    Cmd -->|set_inventory| SetInv[Cap nhat inventory]
    SetInv --> PubUpd[Publish inventory_updated]
    PubUpd --> End3([END])

    Cmd -->|dispense| ValSlot{slot 1-3?}
    ValSlot -->|Khong| Alert2[Publish alert invalid_slot]
    Alert2 --> End4([END])
    ValSlot -->|Co| ValQty{quantity 1-10?}
    ValQty -->|Khong| Alert3[Publish alert invalid_quantity]
    Alert3 --> End5([END])
    ValQty -->|Co| ChkInv{Du thuoc<br/>trong slot?}
    ChkInv -->|Khong| Alert4[Publish inventory_low<br/>status failed]
    Alert4 --> End6([END])
    ChkInv -->|Co| Disp[Publish status dispensing]
    Disp --> Loop1[Lap qty lan]
    Loop1 --> OpenSlot[Quay motor 512 steps<br/>mo ngan]
    OpenSlot --> WaitDrop{IR detect<br/>thuoc roi?<br/>timeout 5s}
    WaitDrop -->|Khong| Retry{retry nho hon 3?}
    Retry -->|Co| OpenSlot
    Retry -->|Khong| Jam[Publish alert jam<br/>status failed]
    Jam --> End7([END])
    WaitDrop -->|Co| DecInv[Inventory giam 1]
    DecInv --> CloseSlot[Quay motor nguoc 512 steps<br/>dong ngan]
    CloseSlot --> WaitPick{IR clear<br/>nguoi lay thuoc?<br/>timeout 30s}
    WaitPick -->|Khong| AlertPick[Publish alert not_picked_up]
    AlertPick --> End8([END])
    WaitPick -->|Co| MoreP{Con pill<br/>can phat?}
    MoreP -->|Co| Loop1
    MoreP -->|Khong| Done[Publish status completed<br/>va inventory moi]
    Done --> End9([END])

    style Msg fill:#8B1A1A,color:#fff
    style Done fill:#2E7D32,color:#fff
    style Alert1 fill:#D32F2F,color:#fff
    style Alert2 fill:#D32F2F,color:#fff
    style Alert3 fill:#D32F2F,color:#fff
    style Alert4 fill:#D32F2F,color:#fff
    style Jam fill:#D32F2F,color:#fff
    style AlertPick fill:#F5A623,color:#fff
```

---

## 4. Tổng quan toàn hệ thống

```mermaid
flowchart LR
    User[Nguoi dung] -->|Click Lay thuoc| FE[Frontend React]
    FE -->|HTTP POST| BE[Backend FastAPI]
    BE -->|Query| DB[(DynamoDB)]
    BE -->|MQTT Publish| AWS[AWS IoT Core]
    AWS -->|MQTT| ESP[ESP32]
    ESP -->|GPIO| Motor[Stepper Motor]
    Motor --> Pill([Thuoc roi])
    Pill -->|Detect| IR[IR Sensor]
    IR --> ESP
    ESP -->|Publish status| AWS
    AWS -->|IoT Rule| DB
    AWS -->|Subscribe| BE
    BE -->|WebSocket| FE
    FE --> User

    style User fill:#8B1A1A,color:#fff
    style ESP fill:#8B1A1A,color:#fff
    style Pill fill:#2E7D32,color:#fff
```
