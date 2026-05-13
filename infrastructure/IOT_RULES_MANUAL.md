# Tao IoT Rules thu cong tren AWS Console

## Buoc 1 — Mo AWS Console
Vao: IoT Core -> Message routing -> Rules -> Create rule

## Rule 1: medai_telemetry_to_dynamo
- Rule name: medai_telemetry_to_dynamo
- SQL:
  SELECT *, topic(3) as device_id, timestamp() as ts
  FROM 'medai/device/+/telemetry'
- Action: DynamoDBv2
  - Table name: medai-device-telemetry
  - IAM role: LabRole (hoac tao role moi voi policy AmazonDynamoDBFullAccess)

## Rule 2: medai_status_to_dynamo (optional)
- Rule name: medai_status_to_dynamo
- SQL: SELECT *, topic(3) as device_id FROM 'medai/device/+/status'
- Action: DynamoDBv2 -> Table: medai-device-telemetry
  (dung chung bang telemetry, them field "type": "status")

## Luu y
- AWS Academy chi cho phep DynamoDB/SNS/S3 actions trong IoT Rules
- HTTP action bi chan do cross-account role restriction
- Backend se poll DynamoDB de lay telemetry (khong can webhook)
