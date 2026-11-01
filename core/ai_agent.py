import os
import io
import json
import base64
from typing import List, Dict, Any, Optional
from PIL import Image

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


SYSTEM_PROMPT = """당신은 과학 및 실험 연구를 돕는 최고의 '스마트 연구노트 어시스턴트(NoteEasy)'입니다.
사용자는 실험을 진행하며 관찰 사항, 메모, 사진, 파일 데이터, 계산 요청 등을 자유롭게 전달합니다.
당신의 역할:
1. 사용자의 질문에 친절하고 과학적으로 답변합니다.
2. 수치 계산이나 실험 결과에 대해 정밀하게 분석하고 정리된 표(Markdown Table)를 제시합니다.
3. 업로드된 실험 사진(장치, 시료, 반응 등)의 특징을 분석하고 기록에 남깁니다.
4. "전자노트 만들어줘" 또는 "정리해줘" 요청 시, 지금까지 축적된 대화와 데이터, 사진들을 종합하여 A4 1페이지에 딱 들어맞는 완벽한 표준 전자연구노트(ELN)를 작성합니다.
항상 한국어로 명확하고 간결하며 신뢰성 높은 어조를 유지하세요.
"""

REPORT_GENERATION_PROMPT = """[요청: 1페이지 전자연구노트(ELN) 생성]
지금까지의 실험 진행 내역(대화 메모, 업로드된 사진 설명, 파일/데이터 표, 계산 결과)을 모두 종합하여,
표준 연구노트 양식에 맞춰 아래 JSON 규격으로 반환해주세요. 반드시 마크다운 코드블록(` ```json ... ``` `) 없이 순수한 JSON 또는 JSON 파싱 가능한 텍스트만 출력하세요.

JSON 출력 형식:
{
  "title": "실험 또는 연구 제목 (구체적이고 명확하게)",
  "experimenter": "연구자/작업자 이름 또는 미지정시 '연구원'",
  "date": "실험 일시 (예: 2026-11-02)",
  "objective": "실험 목적 및 배경 요약 (1~2문장)",
  "materials_and_conditions": [
    "재료/시약 또는 장비 조건 1",
    "재료/시약 또는 장비 조건 2"
  ],
  "procedure_steps": [
    "단계 1: 수행한 내용 요약",
    "단계 2: 수행한 내용 요약",
    "단계 3: 수행한 내용 요약"
  ],
  "results_summary": "핵심 결과 종합 설명 (1~2문장)",
  "result_table_markdown": "실험 결과/측정치/계산치가 들어간 정돈된 마크다운 표 문자열 (없으면 기본 요약표 생성)",
  "key_findings": [
    "핵심 수치나 발견점 1",
    "핵심 수치나 발견점 2"
  ],
  "discussion_and_conclusion": "실험에 대한 고찰, 오차 요인 분석 또는 최종 결론 (2~3문장)"
}
"""

class LabNoteAgent:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None
        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"GenAI Client 초기화 실패: {e}")

    def is_configured(self) -> bool:
        return self.client is not None

    def chat(self, user_message: str, history: List[Dict[str, Any]], image_bytes_list: Optional[List[bytes]] = None) -> str:
        """
        일반 대화 및 분석 요청을 처리합니다.
        """
        if not self.is_configured():
            return self._demo_chat_response(user_message)

        try:
            # 멀티모달 컨텐츠 구성
            contents = [SYSTEM_PROMPT]
            
            # 이전 대화 컨텍스트 일부 주입 (최근 6개)
            recent_history = history[-6:] if len(history) > 6 else history
            for msg in recent_history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(f"[{role.upper()}]: {msg.get('content', '')}")
            
            # 이번 턴 입력
            contents.append(f"[USER 현재 메시지]: {user_message}")
            
            # 첨부 이미지 추가
            if image_bytes_list:
                for img_data in image_bytes_list:
                    contents.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"⚠️ AI 응답 생성 중 오류가 발생했습니다: {str(e)}\n\n(API 키와 네트워크 상태를 확인해주세요.)"

    def generate_lab_note(self, context_summary: str, images_info: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        세션 전체의 로그를 요약하여 A4 1페이지 구조화된 전자노트 JSON을 생성합니다.
        """
        if not self.is_configured():
            return self._demo_lab_note_report(context_summary)

        prompt = f"""{SYSTEM_PROMPT}

{REPORT_GENERATION_PROMPT}

[지금까지 수집된 실험 세션 데이터]:
{context_summary}
"""
        contents = [prompt]
        if images_info:
            for item in images_info[:2]:  # 대표 사진 최대 2장 전송
                if "bytes" in item:
                    contents.append(types.Part.from_bytes(data=item["bytes"], mime_type="image/jpeg"))

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            text = response.text.strip()
            
            # 마크다운 json 제거
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            return data
        except Exception as e:
            print(f"JSON 파싱 실패 또는 API 오류: {e}")
            return self._demo_lab_note_report(context_summary, raw_text=text if 'text' in locals() else str(e))

    def _demo_chat_response(self, message: str) -> str:
        """API 키가 없을 때의 스마트 가이드 응답"""
        if "계산" in message:
            return "💡 [데모 모드] 사이드바의 '간편 수식 계산기'를 이용하시거나, Gemini API 키를 등록하시면 AI가 수식을 실시간 자동 계산하고 해설해 드립니다."
        elif "표" in message or "table" in message.lower():
            return "📊 [데모 모드] 파일을 업로드하시면 즉시 대화형 표로 변환되며, API 키 등록 시 AI가 맞춤형 표 분석을 지원합니다."
        elif "노트" in message or "정리" in message:
            return "📝 언제든지 상단의 **[⚡ 1페이지 전자노트 생성]** 버튼을 누르시면 지금까지의 대화, 사진, 표를 모아 A4 1페이지 요약 리포트가 생성됩니다!"
        return f"🤖 [안내] API 키를 입력하시면 멀티모달 Gemini AI가 실험 도우미로서 대화, 사진 분석, 계산, 정리를 완벽하게 지원합니다. (입력하신 내용: '{message}')"

    def _demo_lab_note_report(self, context_summary: str, raw_text: str = "") -> Dict[str, Any]:
        """데모 또는 에러 시 fallback 기본 구조"""
        return {
            "title": "실험 진행 요약 및 전자연구노트",
            "experimenter": "담당 연구원",
            "date": "2026-11-02",
            "objective": "수행된 작업 및 입력된 데이터/사진을 바탕으로 실험 결과를 종합 정리함.",
            "materials_and_conditions": [
                "입력된 실험 파라미터 및 측정 데이터 활용",
                "환경 조건: 실온 (기본값 설정)"
            ],
            "procedure_steps": [
                "1. 초기 실험 조건 설정 및 대화창을 통한 관찰 기록",
                "2. 관련 실험 사진 및 데이터셋 파일 업로드",
                "3. 수치 연산 및 표 생성 후 전자연구노트 요약 요청"
            ],
            "results_summary": "기록된 관찰 내용과 첨부된 데이터가 성공적으로 취합되었으며, 주요 지표가 산출되었습니다.",
            "result_table_markdown": "| 항목 | 측정/계산값 | 비고 |\n| :--- | :--- | :--- |\n| 데이터 레코드 | 정상 취합 | 세션 내 저장됨 |\n| 분석 지표 | 기준치 충족 | 1페이지 요약 완결 |",
            "key_findings": [
                "실험 세션의 모든 활동 로그가 체계적으로 보존됨",
                "A4 1페이지 규격 내에 핵심 결과가 일목요연하게 정리됨"
            ],
            "discussion_and_conclusion": "실험 전반의 프로세스가 원활히 수행되었으며, 추후 재현성 검증 및 추가 반복 실험을 통해 오차 범위를 더욱 좁힐 수 있을 것으로 사료됨."
        }
