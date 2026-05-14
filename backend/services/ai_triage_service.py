"""
AI Triage Service.

Supports two providers (selected via AI_PROVIDER in .env):
  - "gemini"  : Google Gemini API (default, free tier)
  - "bedrock" : Amazon Bedrock Converse API

Frontend doesn't care which one is used — same /analyze and /chat endpoints.
"""
import json
import logging
from typing import List, Dict, Optional

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
- Ưu tiên đề xuất thuốc SẮP HẾT HẠN trước (giảm lãng phí), nhưng KHÔNG dùng thuốc đã hết hạn.
- Luôn nhắc nhở liều lượng và thời gian uống thuốc."""

# Triệu chứng nguy hiểm — bypass LLM, khuyên gặp bác sĩ ngay
RED_FLAG_KEYWORDS = [
    "khó thở", "kho tho", "đau ngực", "dau nguc", "đau tim", "dau tim",
    "tê liệt", "te liet", "co giật", "co giat", "ngất", "ngat",
    "ho ra máu", "ho ra mau", "nôn ra máu", "non ra mau",
    "sốt cao 40", "sot cao 40", "đau đầu dữ dội", "dau dau du doi",
    "mất ý thức", "mat y thuc", "đột quỵ", "dot quy",
]


def _check_red_flag(symptoms: str) -> Optional[str]:
    """Return urgent message if any red-flag keyword is found."""
    s = symptoms.lower()
    for kw in RED_FLAG_KEYWORDS:
        if kw in s:
            return (
                f"⚠️ TRIỆU CHỨNG NGHIÊM TRỌNG ('{kw}') — "
                f"Vui lòng GỌI 115 hoặc đến bệnh viện gần nhất NGAY LẬP TỨC. "
                f"Không tự ý dùng thuốc trong tình huống này."
            )
    return None


# ── Gemini provider ──────────────────────────────────────────────────────────

class _GeminiProvider:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            if not settings.GEMINI_API_KEY:
                raise RuntimeError("GEMINI_API_KEY not set in .env")
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def invoke(self, messages: List[Dict], system: str) -> str:
        # Convert messages to Gemini format
        # Gemini uses "user" and "model" roles, with a separate system_instruction
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": str(msg["content"])}]
            })

        logger.info(f"[Gemini] Calling model={settings.GEMINI_MODEL}, msgs={len(contents)}")
        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": system,
                "temperature": 0.5,
                "max_output_tokens": 1024,
            },
        )
        return response.text or ""


# ── Bedrock provider (kept as fallback) ──────────────────────────────────────

class _BedrockProvider:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=settings.BEDROCK_REGION,
            )
        return self._client

    def invoke(self, messages: List[Dict], system: str) -> str:
        converse_messages = [
            {"role": m["role"], "content": [{"text": str(m["content"])}]}
            for m in messages
        ]
        response = self.client.converse(
            modelId=settings.BEDROCK_MODEL_ID,
            messages=converse_messages,
            system=[{"text": system}],
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.5,
                "topP": 0.9,
            },
        )
        output = response["output"]["message"]["content"]
        return "".join(b.get("text", "") for b in output)


# ── Public service ──────────────────────────────────────────────────────────

class AITriageService:
    def __init__(self):
        provider_name = (settings.AI_PROVIDER or "gemini").lower()
        if provider_name == "bedrock":
            self.provider = _BedrockProvider()
        else:
            self.provider = _GeminiProvider()
        self.provider_name = provider_name

    def _invoke(self, messages: List[Dict], system: str = SYSTEM_PROMPT) -> str:
        return self.provider.invoke(messages, system)
    def _build_med_list(self, available_medications: List[Dict]) -> str:
        """Build medication list with priority hints (near-expiry first)."""
        # Filter out expired meds
        usable = [m for m in available_medications if m.get("expiry_status") != "expired"]
        # Sort: critical < warning < ok < unknown (nearer expiry first)
        priority = {"critical": 0, "warning": 1, "ok": 2, "unknown": 3}
        usable.sort(key=lambda m: priority.get(m.get("expiry_status", "unknown"), 3))

        lines = []
        for m in usable:
            status = m.get("expiry_status")
            days = m.get("days_until_expiry")
            if status == "critical":
                hint = f" [⚠️ SẮP HẾT HẠN trong {days} ngày — ưu tiên dùng]"
            elif status == "warning":
                hint = f" [hết hạn trong {days} ngày]"
            else:
                hint = ""
            lines.append(
                f"- {m['name']} ({m.get('medication_type', 'pill')}): "
                f"còn {m.get('stock_count', 0)} {m.get('unit', 'viên')}"
                f"{hint}"
            )
        return "\n".join(lines)

    def _system_prompt_with_meds(self, available_medications: Optional[List[Dict]]) -> str:
        """Inject the user's current medication inventory into the system prompt
        so the AI never has to ask the user to list pills manually."""
        if not available_medications:
            return SYSTEM_PROMPT + (
                "\n\nNGỮ CẢNH: Tủ thuốc của người dùng hiện trống — "
                "không có thuốc nào để đề xuất. Khi cần thuốc, hãy khuyên người "
                "dùng đi mua hoặc gặp bác sĩ."
            )
        med_list = self._build_med_list(available_medications)
        if not med_list:
            return SYSTEM_PROMPT + (
                "\n\nNGỮ CẢNH: Tất cả thuốc trong tủ đều đã hết hạn — "
                "không có thuốc nào còn dùng được. Khuyên người dùng "
                "vứt thuốc cũ và mua mới."
            )
        return (
            SYSTEM_PROMPT
            + "\n\nNGỮ CẢNH: Đây là danh sách thuốc HIỆN CÓ trong tủ thuốc "
            + "của người dùng (đã sắp xếp theo ưu tiên — sắp hết hạn lên đầu). "
            + "TUYỆT ĐỐI KHÔNG hỏi người dùng liệt kê thuốc — bạn đã biết tủ thuốc rồi:\n"
            + med_list
            + "\n\nKhi đề xuất thuốc, hãy ƯU TIÊN thuốc sắp hết hạn để giảm "
            + "lãng phí. Chỉ đề xuất thuốc có trong danh sách trên."
        )

    async def analyze_symptoms(self, symptoms: str, available_medications: List[Dict]) -> Dict:
        """Analyze symptoms and suggest medications, prioritizing near-expiry stock."""
        # Safety guard
        red_flag = _check_red_flag(symptoms)
        if red_flag:
            return {
                "analysis": red_flag,
                "symptoms": symptoms,
                "urgency": "emergency",
                "should_see_doctor": True,
                "model": "safety-guard",
            }

        system = self._system_prompt_with_meds(available_medications)
        user_message = (
            f"Triệu chứng của người dùng: {symptoms}\n\n"
            f"Hãy phân tích và đề xuất cách xử lý dựa trên tủ thuốc đã biết. "
            f"Nếu phù hợp, ƯU TIÊN đề xuất thuốc sắp hết hạn để giảm lãng phí. "
            f"Nếu triệu chứng nghiêm trọng hoặc không có thuốc phù hợp trong tủ, "
            f"hãy khuyên gặp bác sĩ."
        )

        try:
            response_text = self._invoke(
                [{"role": "user", "content": user_message}],
                system=system,
            )
            return {
                "analysis": response_text,
                "symptoms": symptoms,
                "medications_checked": len(available_medications),
                "urgency": "normal",
                "should_see_doctor": False,
                "model": f"{self.provider_name}:{settings.GEMINI_MODEL if self.provider_name == 'gemini' else settings.BEDROCK_MODEL_ID}",
            }
        except Exception as e:
            logger.error(f"analyze_symptoms error: {e}")
            return {
                "analysis": (
                    "Xin lỗi, hệ thống AI tạm thời không khả dụng. "
                    "Vui lòng thử lại sau hoặc liên hệ bác sĩ nếu cần."
                ),
                "symptoms": symptoms,
                "error": str(e),
            }

    async def chat(
        self,
        message: str,
        conversation_history: List[Dict],
        available_medications: Optional[List[Dict]] = None,
    ) -> Dict:
        """Continue a multi-turn conversation.

        The user's current medication inventory (if provided) is injected into
        the system prompt so the AI can answer with real data without asking
        the user to list pills.
        """
        # Safety guard on each new user message
        red_flag = _check_red_flag(message)
        if red_flag:
            response_text = red_flag
        else:
            messages = list(conversation_history)
            messages.append({"role": "user", "content": message})
            system = self._system_prompt_with_meds(available_medications)
            try:
                response_text = self._invoke(messages, system=system)
            except Exception as e:
                logger.error(f"chat error: {e}")
                return {
                    "response": "Xin lỗi, hệ thống AI tạm thời không khả dụng. Vui lòng thử lại.",
                    "conversation_history": conversation_history + [
                        {"role": "user", "content": message}
                    ],
                    "error": str(e),
                }

        updated_history = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response_text},
        ]
        return {
            "response": response_text,
            "conversation_history": updated_history,
            "model": f"{self.provider_name}:{settings.GEMINI_MODEL if self.provider_name == 'gemini' else settings.BEDROCK_MODEL_ID}",
        }

    async def suggest_refills(
        self,
        medications: List[Dict],
        dose_history: List[Dict],
    ) -> Dict:
        """
        Generate a smart shopping list:
          - Mark meds with low stock or near expiry
          - Estimate weekly usage from dose_history
          - Ask AI to draft a friendly Vietnamese reminder
        """
        from datetime import datetime, timedelta

        # Compute usage rate per medication (doses per week, last 28 days)
        cutoff = datetime.utcnow() - timedelta(days=28)
        usage = {}  # medication_id → count
        for h in dose_history:
            if h.get("status") not in ("taken", "late"):
                continue
            ts = h.get("taken_time") or h.get("created_at")
            if not ts:
                continue
            try:
                taken = datetime.fromisoformat(ts.replace("Z", ""))
            except (ValueError, AttributeError):
                continue
            if taken < cutoff:
                continue
            mid = h.get("medication_id")
            if mid:
                usage[mid] = usage.get(mid, 0) + h.get("dosage_count", 1)

        # Build candidates needing refill
        candidates = []
        for m in medications:
            stock = int(m.get("stock_count", 0))
            threshold = int(m.get("low_stock_threshold", 5))
            status = m.get("expiry_status")
            doses_28d = usage.get(m.get("medication_id"), 0)
            weekly_rate = round(doses_28d / 4, 1) if doses_28d else 0
            days_until_empty = (
                round(stock / (weekly_rate / 7), 0)
                if weekly_rate > 0 else None
            )

            need_refill = False
            reasons = []
            if status == "expired":
                need_refill = True
                reasons.append("đã hết hạn — cần mua thay thế")
            elif stock <= threshold:
                need_refill = True
                reasons.append(f"tồn kho thấp ({stock} {m.get('unit', 'viên')})")
            if status == "critical":
                need_refill = True
                reasons.append(f"sắp hết hạn trong {m.get('days_until_expiry')} ngày")
            if days_until_empty is not None and days_until_empty <= 14:
                need_refill = True
                reasons.append(f"dự kiến hết trong ~{int(days_until_empty)} ngày theo nhịp dùng hiện tại")

            if need_refill:
                candidates.append({
                    "name": m.get("name"),
                    "stock_count": stock,
                    "unit": m.get("unit", "viên"),
                    "expiry_status": status,
                    "days_until_expiry": m.get("days_until_expiry"),
                    "weekly_usage": weekly_rate,
                    "estimated_days_until_empty": int(days_until_empty) if days_until_empty is not None else None,
                    "reasons": reasons,
                })

        if not candidates:
            return {
                "needs_refill": False,
                "suggestions": [],
                "summary": "Tủ thuốc của bạn đang đầy đủ — chưa cần mua thêm.",
                "candidates": [],
            }

        # Ask AI to draft a friendly natural-language summary
        candidate_lines = "\n".join(
            f"- {c['name']}: còn {c['stock_count']} {c['unit']}; "
            f"lý do: {', '.join(c['reasons'])}"
            + (f"; dùng ~{c['weekly_usage']} {c['unit']}/tuần" if c['weekly_usage'] else "")
            for c in candidates
        )
        prompt = (
            "Đây là danh sách thuốc người dùng nên mua thêm:\n"
            f"{candidate_lines}\n\n"
            "Hãy viết MỘT đoạn ngắn (3-5 câu) bằng tiếng Việt, giọng thân thiện, "
            "tóm tắt cho người dùng biết nên mua gì và vì sao. Không cần lặp lại "
            "tất cả lý do, chỉ điểm chính. Không thêm disclaimer."
        )

        try:
            summary = self._invoke(
                [{"role": "user", "content": prompt}],
                system="Bạn là trợ lý y tế MedAI Cabinet, viết ngắn gọn tiếng Việt.",
            )
        except Exception as e:
            logger.error(f"suggest_refills LLM error: {e}")
            summary = (
                "Một số thuốc trong tủ cần được nạp lại. "
                "Xem chi tiết bên dưới để chuẩn bị mua sắm."
            )

        return {
            "needs_refill": True,
            "suggestions": candidates,  # alias for frontend convenience
            "summary": summary,
            "candidates": candidates,
        }
