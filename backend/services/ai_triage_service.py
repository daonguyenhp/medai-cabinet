"""
AI Triage Service — Amazon Bedrock.
Supports both Meta Llama 3 and Anthropic Claude models.
Model is selected via BEDROCK_MODEL_ID in .env.
"""
import boto3
import json
import logging
from typing import List, Dict

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý y tế AI của MedAI Cabinet, hỗ trợ người dùng Việt Nam.
Nhiệm vụ của bạn:
1. Phân tích triệu chứng và đề xuất thuốc phù hợp từ tủ thuốc của người dùng.
2. Cảnh báo về tương tác thuốc, chống chỉ định.
3. Hướng dẫn cách dùng thuốc đúng cách.
4. Khuyến nghị gặp bác sĩ khi cần thiết.

Quy tắc quan trọng:
- Luôn trả lời bằng tiếng Việt.
- Không chẩn đoán bệnh — chỉ hỗ trợ thông tin.
- Ưu tiên an toàn: nếu triệu chứng nghiêm trọng, khuyên gặp bác sĩ ngay.
- Chỉ đề xuất thuốc có trong tủ thuốc của người dùng.
- Luôn nhắc nhở liều lượng và thời gian uống thuốc."""


def _is_claude(model_id: str) -> bool:
    return "anthropic" in model_id.lower() or "claude" in model_id.lower()


def _is_llama(model_id: str) -> bool:
    return "llama" in model_id.lower() or "meta" in model_id.lower()


class AITriageService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=settings.BEDROCK_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
                aws_session_token=settings.AWS_SESSION_TOKEN or None,
            )
        return self._client

    def _invoke(self, messages: List[Dict], system: str = SYSTEM_PROMPT) -> str:
        model_id = settings.BEDROCK_MODEL_ID

        if _is_claude(model_id):
            return self._invoke_claude(messages, system, model_id)
        elif _is_llama(model_id):
            return self._invoke_llama(messages, system, model_id)
        else:
            # Generic fallback — try Claude format
            return self._invoke_claude(messages, system, model_id)

    def _invoke_claude(self, messages: List[Dict], system: str, model_id: str) -> str:
        """Anthropic Claude via Bedrock."""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": system,
            "messages": messages,
        }
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def _invoke_llama(self, messages: List[Dict], system: str, model_id: str) -> str:
        """Meta Llama 3 via Bedrock — uses prompt format."""
        # Build Llama 3 chat prompt
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}<|eot_id|>"
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"<|start_header_id|>{role}<|end_header_id|>\n{content}<|eot_id|>"
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n"

        body = {
            "prompt": prompt,
            "max_gen_len": 1024,
            "temperature": 0.5,
            "top_p": 0.9,
        }
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result.get("generation", "").strip()

    async def analyze_symptoms(self, symptoms: str, available_medications: List[Dict]) -> Dict:
        """Analyze symptoms and suggest medications from the user's cabinet."""
        med_list = "\n".join(
            f"- {m['name']} ({m.get('medication_type', 'pill')}): "
            f"còn {m.get('stock_count', 0)} {m.get('unit', 'viên')}"
            for m in available_medications
            if m.get("expiry_status") not in ["expired"]
        )

        user_message = (
            f"Triệu chứng của người dùng: {symptoms}\n\n"
            f"Thuốc hiện có trong tủ:\n"
            f"{med_list if med_list else 'Không có thuốc nào trong tủ.'}\n\n"
            f"Hãy phân tích và đề xuất cách xử lý phù hợp."
        )

        try:
            response_text = self._invoke([{"role": "user", "content": user_message}])
            return {
                "analysis": response_text,
                "symptoms": symptoms,
                "medications_checked": len(available_medications),
                "model": settings.BEDROCK_MODEL_ID,
            }
        except Exception as e:
            logger.error(f"analyze_symptoms error: {e}")
            return {
                "analysis": (
                    "Xin lỗi, không thể phân tích lúc này. "
                    "Vui lòng thử lại sau hoặc liên hệ bác sĩ."
                ),
                "symptoms": symptoms,
                "error": str(e),
            }

    async def chat(self, message: str, conversation_history: List[Dict]) -> Dict:
        """Continue a multi-turn conversation."""
        messages = list(conversation_history)
        messages.append({"role": "user", "content": message})

        try:
            response_text = self._invoke(messages)
            updated_history = messages + [{"role": "assistant", "content": response_text}]
            return {
                "response": response_text,
                "conversation_history": updated_history,
                "model": settings.BEDROCK_MODEL_ID,
            }
        except Exception as e:
            logger.error(f"chat error: {e}")
            return {
                "response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
                "conversation_history": messages,
                "error": str(e),
            }
