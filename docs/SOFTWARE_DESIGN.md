# MedAI Cabinet — Software Design

## Hardware Components (tham chiếu)

| Loại | Model | Vai trò |
|------|-------|---------|
| Microcontroller | ESP32-WROOM-32 | Bộ điều khiển trung tâm, WiFi/MQTT |
| Stepper Motor | 28BYJ-48 (5V, 2048 steps/rev) × 3 | Xoay đĩa thuốc trong từng ngăn |
| Motor Driver | ULN2003 × 3 | Điều khiển stepper motor |
| Sensor | IR Obstacle Sensor (FC-51) | Phát hiện thuốc rơi và việc lấy thuốc |
| Cloud | AWS IoT Core, DynamoDB, Bedrock | Backend hạ tầng |

---

## 1. System Architecture — Kiến trúc phần mềm

```mermaid
flowchart TB
    subgraph Client[Client Layer]
        UI[React Web App]
    end

    subgraph Backend[Application Layer - FastAPI]
        Router[REST API Routers]
        Service[Business Services]
        AI[AI Triage Service]
    end

    subgraph Cloud[Cloud Services]
        IoT[AWS IoT Core MQTT Broker]
        DDB[(AWS DynamoDB)]
        Gem[Google Gemini API]
        S3[(AWS S3 Storage)]
    end

    subgraph Edge[Edge Device]
        ESP[ESP32 Firmware]
    end

    UI <-->|HTTP REST| Router
    Router --> Service
    Service <-->|Read/Write| DDB
    Service -->|Publish Command| IoT
    AI -->|generate_content| Gem
    Router --> AI
    IoT <-->|MQTT TLS| ESP
    IoT -->|IoT Rules| DDB
    Service -->|Subscribe| IoT

    style UI fill:#8B1A1A,color:#fff
    style Router fill:#8B1A1A,color:#fff
    style ESP fill:#8B1A1A,color:#fff
```

---

## 2. Dispense Request Flow — Luồng xử lý lệnh phát thuốc

Mô tả cách phần mềm xử lý khi user bấm nút "Lấy thuốc". Đây là flowchart chính thể hiện input → decision → output.

```mermaid
flowchart TD
    Start([User clicks Dispense]) --> InputUI[Input: medication_id, quantity]
    InputUI --> POST[Frontend: HTTP POST<br/>api/v1/medications/id/dispense]
    POST --> ValidReq{Backend:<br/>Validate Pydantic schema}
    ValidReq -->|Invalid| Err400[Response 400<br/>Bad Request]
    Err400 --> EndF([END])
    ValidReq -->|Valid| QueryMed[Query DynamoDB<br/>medai-medications]
    QueryMed --> MedExist{Medication<br/>exists?}
    MedExist -->|No| Err404[Response 404<br/>Not Found]
    Err404 --> EndF
    MedExist -->|Yes| ChkStock{stock_count<br/>greater equal quantity?}
    ChkStock -->|No| Err400b[Response 400<br/>Insufficient Stock]
    Err400b --> EndF
    ChkStock -->|Yes| GetDev[Lookup user device_id<br/>from medai-users]
    GetDev --> DevExist{Device<br/>linked?}
    DevExist -->|No| SkipPub[Skip MQTT publish<br/>only update DB]
    DevExist -->|Yes| BuildCmd[Build command JSON<br/>command dispense<br/>slot compartment<br/>quantity N]
    BuildCmd --> PubMQTT[Publish to topic<br/>medai/device/id/command]
    PubMQTT --> SkipPub
    SkipPub --> UpdDB[Update stock_count<br/>new = old minus quantity]
    UpdDB --> Resp200[Response 200<br/>message + remaining stock]
    Resp200 --> Toast[Frontend toast<br/>Refresh medication list]
    Toast --> EndS([END])

    style Start fill:#8B1A1A,color:#fff
    style EndS fill:#2E7D32,color:#fff
    style Err400 fill:#D32F2F,color:#fff
    style Err404 fill:#D32F2F,color:#fff
    style Err400b fill:#D32F2F,color:#fff
```

---

## 3. AI Triage Pipeline — Luồng xử lý tư vấn AI

Mô tả cách phần mềm xử lý input triệu chứng từ user, làm giàu context, gọi Gemini API, và parse output.

```mermaid
flowchart TD
    Start([User submits symptoms]) --> Input[Input: symptoms text<br/>user_id]
    Input --> POST[POST api/v1/ai-triage/analyze]
    POST --> ValSym{symptoms.length<br/>greater than 5?}
    ValSym -->|No| Err422[Response 422<br/>Validation Error]
    Err422 --> EndF([END])
    ValSym -->|Yes| FetchMeds[Query user medications<br/>from DynamoDB]
    FetchMeds --> FilterExp[Filter: exclude<br/>expired meds]
    FilterExp --> BuildCtx[Build context string<br/>medication name<br/>stock count<br/>expiry status]
    BuildCtx --> BuildPrompt[Compose prompt<br/>SYSTEM_PROMPT + symptoms + meds]
    BuildPrompt --> SelProv{AI_PROVIDER<br/>setting?}
    SelProv -->|gemini default| InitGem[Init google-genai client<br/>api_key from env]
    SelProv -->|bedrock| InitBed[Init boto3 bedrock-runtime]
    InitGem --> FmtGem[Format Gemini schema<br/>contents array<br/>role user or model<br/>system_instruction]
    InitBed --> FmtBed[Format Bedrock payload<br/>Claude or Llama template]
    FmtGem --> Invoke[Call generate_content<br/>or invoke_model]
    FmtBed --> Invoke
    Invoke --> ChkResp{Response<br/>OK?}
    ChkResp -->|Error| FallbackErr[Return safe fallback<br/>Xin loi loi he thong]
    FallbackErr --> EndF
    ChkResp -->|Success| ParseTxt[Extract text from response]
    ParseTxt --> Detect{Contains keywords<br/>khan cap, bac si,<br/>cap cuu?}
    Detect -->|Yes| FlagDr[Set should_see_doctor true<br/>urgency emergency]
    Detect -->|No| FlagOk[Set should_see_doctor false<br/>urgency normal]
    FlagDr --> WrapResp[Wrap structured response<br/>analysis<br/>medications_checked<br/>model<br/>should_see_doctor<br/>urgency]
    FlagOk --> WrapResp
    WrapResp --> LogInter[Log interaction<br/>future fine-tuning data]
    LogInter --> Resp200[Response 200 JSON]
    Resp200 --> Render[Frontend render<br/>react-markdown]
    Render --> EndS([END])

    style Start fill:#8B1A1A,color:#fff
    style EndS fill:#2E7D32,color:#fff
    style Err422 fill:#D32F2F,color:#fff
    style FallbackErr fill:#F5A623,color:#fff
```

---

## 4. Telemetry Ingestion — Xử lý dữ liệu từ thiết bị

Khi ESP32 publish telemetry (inventory update, status), phần mềm backend xử lý và đồng bộ.

```mermaid
flowchart TD
    Start([ESP32 publishes message]) --> Topic{Topic pattern?}
    Topic -->|telemetry| ParseT[Parse JSON payload<br/>device_id, inventory]
    Topic -->|status| ParseS[Parse status string<br/>online, completed, failed]
    Topic -->|alert| ParseA[Parse alert type<br/>jam, low_stock]

    ParseT --> RuleEng[AWS IoT Rule<br/>SQL filter and route]
    RuleEng --> WriteT[Insert into<br/>medai-device-telemetry]

    ParseS --> SubBE[Backend MQTT subscriber<br/>mqtt_subscriber.py]
    ParseA --> SubBE
    SubBE --> Match{Status type?}
    Match -->|completed| ReconcileInv[Reconcile inventory<br/>compare DB vs device]
    Match -->|failed| CreateAlert1[Create alert record<br/>severity warning]
    Match -->|jam| CreateAlert2[Create alert record<br/>severity critical]
    Match -->|low_stock| CreateAlert3[Create alert record<br/>severity warning]
    ReconcileInv --> UpdDB[Update medai-medications<br/>set stock_count]
    CreateAlert1 --> InsAlert[Insert into medai-alerts]
    CreateAlert2 --> InsAlert
    CreateAlert3 --> InsAlert
    InsAlert --> NotifFE[Frontend polls<br/>alerts/unread-count]
    UpdDB --> NotifFE
    WriteT --> EndS([END])
    NotifFE --> EndS

    style Start fill:#8B1A1A,color:#fff
    style EndS fill:#2E7D32,color:#fff
    style CreateAlert1 fill:#F5A623,color:#fff
    style CreateAlert2 fill:#D32F2F,color:#fff
    style CreateAlert3 fill:#F5A623,color:#fff
```

---

## Notes

- Mỗi flowchart là 1 sơ đồ độc lập — có thể paste từng cái vào https://mermaid.live/ để export PNG/SVG.
- Diamond (`{...}`) là decision point.
- Rectangle (`[...]`) là process step.
- Stadium (`([...])`) là start/end terminator.
- Kiểu trình bày này là **standard flowchart symbols** theo ISO 5807.
