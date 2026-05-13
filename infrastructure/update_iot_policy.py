"""
Update IoT Policy to allow MedAI topics.
Run this once after initial setup.

Usage:
    python update_iot_policy.py
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv("../backend/.env")

REGION      = os.getenv("AWS_REGION", "ap-southeast-1")
ACCOUNT_ID  = "521330944778"
POLICY_NAME = "medai-cabinet-device-Policy"

UPDATED_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowConnect",
            "Effect": "Allow",
            "Action": ["iot:Connect"],
            "Resource": [
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:client/sdk-nodejs-*",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:client/medai-*",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:client/medai-backend-server",
            ],
        },
        {
            "Sid": "AllowPublishDevice",
            "Effect": "Allow",
            "Action": ["iot:Publish", "iot:PublishRetain"],
            "Resource": [
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/sdk/test/js",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/medai/device/*/telemetry",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/medai/device/*/status",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/medai/device/*/heartbeat",
            ],
        },
        {
            "Sid": "AllowPublishBackend",
            "Effect": "Allow",
            "Action": ["iot:Publish", "iot:PublishRetain"],
            "Resource": [
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/medai/device/*/command",
            ],
        },
        {
            "Sid": "AllowSubscribeDevice",
            "Effect": "Allow",
            "Action": ["iot:Subscribe"],
            "Resource": [
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topicfilter/sdk/test/js",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topicfilter/medai/device/*/command",
            ],
        },
        {
            "Sid": "AllowReceive",
            "Effect": "Allow",
            "Action": ["iot:Receive"],
            "Resource": [
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/sdk/test/js",
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:topic/medai/device/*/command",
            ],
        },
        {
            "Sid": "AllowShadow",
            "Effect": "Allow",
            "Action": [
                "iot:GetThingShadow",
                "iot:UpdateThingShadow",
                "iot:DeleteThingShadow",
            ],
            "Resource": [
                f"arn:aws:iot:{REGION}:{ACCOUNT_ID}:thing/medai-*",
            ],
        },
    ],
}

IOT_RULES = [
    {
        "ruleName": "medai_telemetry_to_api",
        "sql": "SELECT * FROM 'medai/device/+/telemetry'",
        "description": "Forward device telemetry to MedAI backend",
        "endpoint_path": "/api/v1/iot/telemetry",
    },
    {
        "ruleName": "medai_status_to_api",
        "sql": "SELECT * FROM 'medai/device/+/status'",
        "description": "Forward device status to MedAI backend",
        "endpoint_path": "/api/v1/iot/status",
    },
    {
        "ruleName": "medai_heartbeat_to_api",
        "sql": "SELECT * FROM 'medai/device/+/heartbeat'",
        "description": "Forward device heartbeat to MedAI backend",
        "endpoint_path": "/api/v1/iot/status",
    },
]


def main():
    iot = boto3.client(
        "iot",
        region_name=REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN") or None,
    )

    # ── 1. Update IoT Policy ──────────────────────────────────────────────────
    print(f"Updating IoT Policy: {POLICY_NAME}")
    try:
        # Create new version and set as default
        response = iot.create_policy_version(
            policyName=POLICY_NAME,
            policyDocument=json.dumps(UPDATED_POLICY),
            setAsDefault=True,
        )
        print(f"  ✓ Policy updated → version {response['policyVersionId']}")
    except Exception as e:
        print(f"  ✗ Policy update failed: {e}")
        print("  → Try manually in AWS Console: IoT Core → Security → Policies")

    # ── 2. Create IoT Rules ───────────────────────────────────────────────────
    api_base = input("\nEnter your backend API URL (e.g. https://abc.ngrok.io): ").strip()
    if not api_base:
        print("Skipping IoT Rules (no API URL provided)")
        return

    for rule in IOT_RULES:
        rule_payload = {
            "sql": rule["sql"],
            "description": rule["description"],
            "actions": [{
                "http": {
                    "url": f"{api_base}{rule['endpoint_path']}",
                    "confirmationUrl": f"{api_base}{rule['endpoint_path']}",
                    "headers": [{"key": "Content-Type", "value": "application/json"}],
                }
            }],
            "ruleDisabled": False,
            "awsIotSqlVersion": "2016-03-23",
        }
        try:
            iot.create_topic_rule(
                ruleName=rule["ruleName"],
                topicRulePayload=rule_payload,
            )
            print(f"  ✓ Created IoT Rule: {rule['ruleName']}")
        except iot.exceptions.ResourceAlreadyExistsException:
            iot.replace_topic_rule(
                ruleName=rule["ruleName"],
                topicRulePayload=rule_payload,
            )
            print(f"  ✓ Updated IoT Rule: {rule['ruleName']}")
        except Exception as e:
            print(f"  ✗ Rule {rule['ruleName']}: {e}")

    print("\n✅ Done! IoT Policy and Rules updated.")
    print(f"\nNext steps:")
    print(f"  1. Copy firmware certs to firmware/data/certs/")
    print(f"  2. Run: pio run --target uploadfs")
    print(f"  3. Run: pio run --target upload")


if __name__ == "__main__":
    main()
