"""
Seed 3 sample medications + user record into DynamoDB via the backend API.

Usage:
    # Đảm bảo backend đang chạy (localhost:8000)
    python seed_medications.py
"""
import requests

API_BASE = "http://localhost:8000/api/v1"
USER_ID = "demo-user-001"
DEVICE_ID = "medai-001"  # Must match firmware config.h DEVICE_ID

MEDICATIONS = [
    {
        "user_id": USER_ID,
        "name": "Paracetamol 500mg",
        "generic_name": "Acetaminophen",
        "medication_type": "pill",
        "compartment": 1,
        "stock_count": 20,
        "unit": "viên",
        "dosage_strength": "500mg",
        "manufacturer": "DHG Pharma",
        "expiry_date": "2027-03-15",
        "storage_instructions": "Bảo quản nơi khô ráo, dưới 30°C",
        "notes": "Giảm đau, hạ sốt. Uống sau ăn.",
        "low_stock_threshold": 5,
    },
    {
        "user_id": USER_ID,
        "name": "Vitamin C 1000mg",
        "generic_name": "Ascorbic Acid",
        "medication_type": "pill",
        "compartment": 2,
        "stock_count": 15,
        "unit": "viên",
        "dosage_strength": "1000mg",
        "manufacturer": "Blackmores",
        "expiry_date": "2026-08-20",
        "storage_instructions": "Tránh ánh sáng trực tiếp",
        "notes": "Tăng sức đề kháng. Uống 1 viên/ngày sau ăn sáng.",
        "low_stock_threshold": 5,
    },
    {
        "user_id": USER_ID,
        "name": "Amoxicillin 500mg",
        "generic_name": "Amoxicillin",
        "medication_type": "pill",
        "compartment": 3,
        "stock_count": 10,
        "unit": "viên",
        "dosage_strength": "500mg",
        "manufacturer": "Pymepharco",
        "expiry_date": "2026-12-01",
        "storage_instructions": "Bảo quản dưới 25°C, tránh ẩm",
        "notes": "Kháng sinh. Uống đủ liều theo chỉ định bác sĩ.",
        "low_stock_threshold": 3,
    },
]


def seed_user():
    """Create user record with device_id so backend can route commands to ESP32."""
    print("[User] Creating user record with device_id...")

    # Use DynamoDB directly via boto3 since there's no user creation API
    import boto3
    import os
    from pathlib import Path

    # Load .env
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)

    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
    )

    table = dynamodb.Table("medai-users")
    table.put_item(Item={
        "user_id": USER_ID,
        "name": "Nguyễn Văn An",
        "age": 68,
        "phone": "0901234567",
        "device_id": DEVICE_ID,
        "caregiver_name": "Nguyễn Thị Bình",
        "caregiver_phone": "0907654321",
        "role": "patient",
        "language": "vi",
    })
    print(f"      OK — user_id={USER_ID}, device_id={DEVICE_ID}")
    print()


def seed_medications():
    print("[Medications] Adding 3 medications...")
    print()

    for i, med in enumerate(MEDICATIONS, 1):
        print(f"  [{i}/3] {med['name']}...")
        try:
            resp = requests.post(f"{API_BASE}/medications/", json=med, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                print(f"        OK — ID: {data.get('medication_id', 'N/A')}")
                print(f"        Compartment: {med['compartment']}, Stock: {med['stock_count']} {med['unit']}")
            else:
                print(f"        FAILED — {resp.status_code}: {resp.text[:200]}")
        except requests.ConnectionError:
            print("        ERROR: Cannot connect to backend. Is it running on localhost:8000?")
            return
        except Exception as e:
            print(f"        ERROR: {e}")
        print()


def main():
    print("=" * 50)
    print("  MedAI Cabinet — Seed Data")
    print("=" * 50)
    print()

    seed_user()
    seed_medications()

    print("=" * 50)
    print("  Done!")
    print()
    print("  Flow: Frontend 'Lấy thuốc' button")
    print(f"    → Backend POST /api/v1/medications/{{id}}/dispense")
    print(f"    → AWS IoT publish to medai/device/{DEVICE_ID}/command")
    print(f"    → ESP32 receives command → motor rotates")
    print()
    print("  Check: http://localhost:3000/medications")
    print("=" * 50)


if __name__ == "__main__":
    main()
