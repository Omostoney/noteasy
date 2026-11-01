import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import io
import json
from datetime import datetime
from PIL import Image

from core.ai_agent import LabNoteAgent
from core.data_handler import parse_uploaded_file, dataframe_to_markdown_summary, safe_calculate
from core.report_builder import generate_a4_html, generate_markdown_note

# 페이지 기본 설정
st.set_page_config(
    page_title="NoteEasy - 스마트 AI 전자연구노트",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- 세션 상태 초기화 -----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 🧪 **스마트 AI 연구노트 어시스턴트 (NoteEasy)**입니다.\n\n실험이나 작업을 진행하시면서 **메모, 사진, CSV/Excel 데이터 파일, 계산 요청**을 자유롭게 남겨주세요. 언제든지 **'전자노트 만들어줘'**라고 말씀하시거나 상단의 **[⚡ 1페이지 전자노트 생성]** 버튼을 누르시면, 지금까지의 모든 과정을 A4 1페이지 규격의 완벽한 전자연구노트로 정리해 드립니다!"}
    ]
if "images" not in st.session_state:
    st.session_state.images = []  # [{"name": str, "bytes": bytes, "b64": str, "caption": str}]
if "data_tables" not in st.session_state:
    st.session_state.data_tables = []  # [{"name": str, "df": DataFrame, "summary": str}]
if "calculations" not in st.session_state:
    st.session_state.calculations = []  # [{"expr": str, "result": str}]
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "current_html" not in st.session_state:
    st.session_state.current_html = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# ----------------- 사이드바 설정 -----------------
with st.sidebar:
    st.markdown("### 🧪 NoteEasy 제어판")
    st.caption("One-Page Multimodal Electronic Lab Notebook")
    
    st.divider()
    
    # 1. API 키 설정 (환경변수/secrets 우선 탐색)
    default_key = os.environ.get("GEMINI_API_KEY", "")
    if not default_key:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                default_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    user_api_key = st.text_input(
        "🔑 Google Gemini API Key",
        value=default_key,
        type="password",
        help="Google AI Studio에서 무료로 발급받을 수 있는 API 키를 입력하세요. 미입력 시 스마트 데모 모드로 작동합니다."
    )
    if not user_api_key:
        st.info("💡 [무료 API Key 발급받기](https://aistudio.google.com/app/apikey)")
    
    # 모델 선택
    model_choice = st.selectbox(
        "🧠 AI 모델 선택",
        ["gemini-2.5-flash", "gemini-2.0-flash"],
        index=0,
        help="멀티모달 이미지 분석과 고속 요약에 최적화된 최신 Flash 모델"
    )

    # 실험 분야 / 템플릿
    template_type = st.selectbox(
        "📑 실험 양식 템플릿",
        ["일반 과학/실험 연구", "화학/소재 합성", "생명과학/바이오", "데이터 분석/전산 실험", "자유 관찰/아이디어"],
        index=0
    )

    st.divider()

    # 연구자 정보
    researcher_name = st.text_input("👤 담당 연구자", value="홍길동 연구원")
    experiment_date = st.date_input("📅 실험 일자", value=datetime.today())

    st.divider()

    # 세션 상태 요약
    st.markdown("#### 📊 현재 세션 기록 현황")
    c1, c2, c3 = st.columns(3)
    c1.metric("대화 로그", len(st.session_state.messages))
    c2.metric("사진", len(st.session_state.images))
    c3.metric("데이터표", len(st.session_state.data_tables))

    st.divider()

    st.markdown(
        """
        <div style="font-size: 11px; color: #64748b; line-height: 1.5;">
        <strong>🚀 배포 팁</strong><br>
        • GitHub에 올린 뒤 <strong>Streamlit Cloud</strong>에서 리포지토리를 선택하면 바로 무료 웹 배포가 가능합니다.<br>
        • 환경변수 <code>GEMINI_API_KEY</code>를 Streamlit Cloud Secrets에 등록해두면 다른 사용자도 별도 키 없이 즉시 쓸 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True
    )

# AI 에이전트 인스턴스
agent = LabNoteAgent(api_key=user_api_key, model_name=model_choice)

# ----------------- 헬퍼 함수 -----------------
def build_session_context() -> str:
    """세션 내 모든 활동 로그를 프롬프트용 텍스트로 결합합니다."""
    parts = []
    parts.append(f"실험 템플릿: {template_type}")
    parts.append(f"연구자: {researcher_name}")
    parts.append(f"일시: {experiment_date.strftime('%Y-%m-%d')}")
    
    parts.append("\n[대화 및 메모 기록]:")
    for msg in st.session_state.messages:
        role = msg.get("role")
        content = msg.get("content")
        if role in ["user", "assistant"]:
            parts.append(f"- {role.upper()}: {content}")
            
    if st.session_state.calculations:
        parts.append("\n[수행된 수식 및 계산 결과]:")
        for calc in st.session_state.calculations:
            parts.append(f"- 수식: {calc['expr']} => 결과: {calc['result']}")
            
    if st.session_state.data_tables:
        parts.append("\n[업로드된 데이터셋 및 표 요약]:")
        for t in st.session_state.data_tables:
            parts.append(f"- 파일명: {t['name']}\n{t['summary']}")
            if "df" in t and t["df"] is not None:
                parts.append(dataframe_to_markdown_summary(t["df"], max_rows=5))

    if st.session_state.images:
        parts.append(f"\n[첨부된 실험 사진 수]: {len(st.session_state.images)}장")
        for idx, img_info in enumerate(st.session_state.images):
            parts.append(f"- 사진 {idx+1}: {img_info['name']} (메모: {img_info.get('caption', '사진 첨부됨')})")

    return "\n".join(parts)

def trigger_create_note():
    """전자노트 생성 공통 로직"""
    with st.spinner("✨ 지금까지의 대화, 사진, 데이터 표를 분석하여 A4 1페이지 전자연구노트를 생성하고 있습니다..."):
        context_text = build_session_context()
        note_json = agent.generate_lab_note(
            context_summary=context_text,
            images_info=st.session_state.images
        )
        # 연구자, 일자 보정
        note_json["experimenter"] = researcher_name
        note_json["date"] = experiment_date.strftime("%Y-%m-%d")

        # A4 HTML 생성
        img_b64_list = [img["b64"] for img in st.session_state.images]
        html_doc = generate_a4_html(note_json, images_b64=img_b64_list)

        st.session_state.current_report = note_json
        st.session_state.current_html = html_doc

        # 어시스턴트 메시지 추가
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"🎉 **A4 1페이지 전자연구노트가 성공적으로 완성되었습니다!**\n\n상단 **[📑 A4 전자연구노트 프리뷰 & 인쇄]** 탭에서 깔끔하게 정리된 보고서를 확인하고 바로 인쇄(Ctrl+P)하거나 다운로드하세요."
        })

# ----------------- 상단 액션 바 -----------------
col_title, col_btns = st.columns([6, 4])
with col_title:
    st.title("🧪 NoteEasy")
    st.caption("대화 · 사진 · 표 · 계산을 A4 1페이지 규격 전자연구노트로 원클릭 자동 요약")

with col_btns:
    st.write("") # 간격 맞춤
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("⚡ 1페이지 전자노트 생성", type="primary", use_container_width=True):
            trigger_create_note()
            st.rerun()
    with c_btn2:
        if st.button("🗑️ 세션 초기화", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "새로운 실험 세션이 시작되었습니다! 메모나 사진, 데이터를 자유롭게 입력해 주세요."}
            ]
            st.session_state.images = []
            st.session_state.data_tables = []
            st.session_state.calculations = []
            st.session_state.current_report = None
            st.session_state.current_html = ""
            st.rerun()

# ----------------- 메인 탭 구성 -----------------
tab_chat, tab_preview, tab_storage = st.tabs([
    "💬 실험 진행 & 어시스턴트",
    "📑 A4 전자연구노트 프리뷰 & 인쇄",
    "📂 데이터 & 사진 보관소"
])

# ================= TAB 1: 실험 진행 & 대화창 =================
with tab_chat:
    # 1. 상단 퀵 입력 툴바 (사진, 파일, 계산)
    with st.expander("🛠️ 빠른 데이터 입력 도구 (사진 업로드, 데이터 파일, 수식 계산기)", expanded=False):
        t1, t2, t3 = st.columns(3)
        
        # [도구 1] 사진 업로드
        with t1:
            st.markdown("##### 📷 실험 사진 추가")
            photo_file = st.file_uploader("이미지 파일 (JPG, PNG)", type=["jpg", "jpeg", "png"], key="quick_photo")
            photo_caption = st.text_input("사진 메모/설명", placeholder="예: 반응 10분 후 색상 변화", key="quick_caption")
            if st.button("사진 등록", key="btn_add_photo", use_container_width=True):
                if photo_file:
                    bytes_data = photo_file.read()
                    b64_data = base64.b64encode(bytes_data).decode()
                    st.session_state.images.append({
                        "name": photo_file.name,
                        "bytes": bytes_data,
                        "b64": b64_data,
                        "caption": photo_caption or photo_file.name
                    })
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"[📷 사진 등록]: {photo_file.name} - {photo_caption or '설명 없음'}"
                    })
                    st.success(f"사진 '{photo_file.name}'이 등록되었습니다!")
                    st.rerun()

        # [도구 2] 데이터 파일 업로드
        with t2:
            st.markdown("##### 📁 데이터 파일 (CSV/Excel)")
            data_file = st.file_uploader("데이터셋 파일", type=["csv", "xlsx", "xls", "txt"], key="quick_data")
            if st.button("데이터 분석 및 등록", key="btn_add_data", use_container_width=True):
                if data_file:
                    df, summary = parse_uploaded_file(data_file)
                    st.session_state.data_tables.append({
                        "name": data_file.name,
                        "df": df,
                        "summary": summary
                    })
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"[📁 데이터 파일 등록]: {data_file.name}\n\n{summary}"
                    })
                    st.success(f"데이터 파일 '{data_file.name}'이 등록되었습니다!")
                    st.rerun()

        # [도구 3] 간편 수식 계산기
        with t3:
            st.markdown("##### 🧮 간편 수식 계산")
            math_expr = st.text_input("수식 입력", placeholder="예: (15.4 / 20.0) * 100", key="calc_input")
            if st.button("계산 실행", key="btn_run_calc", use_container_width=True):
                if math_expr:
                    calc_res = safe_calculate(math_expr)
                    if calc_res["success"]:
                        result_msg = f"수식: `{math_expr}` = **{calc_res['result']}**"
                        st.session_state.calculations.append({
                            "expr": math_expr,
                            "result": calc_res['result']
                        })
                        st.session_state.messages.append({
                            "role": "user",
                            "content": f"[계산 요청] {math_expr}"
                        })
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"🧮 계산 결과:\n{result_msg}"
                        })
                        st.rerun()
                    else:
                        st.error(calc_res["error"])

    st.markdown("---")

    # 대화 히스토리 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 채팅 입력창
    user_prompt = st.chat_input("질문, 메모, 조건 변경을 입력하거나 '전자노트 만들어줘'라고 말씀하세요...")
    if user_prompt:
        # 1. 사용자 메시지 등록
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # 2. "전자노트 만들어줘" 트리거 감지
        lower_prompt = user_prompt.lower().strip()
        is_note_trigger = any(kw in lower_prompt for kw in ["전자노트", "연구노트", "정리해줘", "노트 만들어", "보고서 만들어", "요약해줘"])

        if is_note_trigger:
            trigger_create_note()
            st.rerun()
        else:
            # 일반 대화 / 계산 / 질의응답
            with st.chat_message("assistant"):
                with st.spinner("답변을 작성하고 있습니다..."):
                    # 최근 이미지 바이트 리스트 준비
                    img_bytes = [img["bytes"] for img in st.session_state.images[-2:]] if st.session_state.images else None
                    ai_reply = agent.chat(user_prompt, st.session_state.messages, image_bytes_list=img_bytes)
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})


# ================= TAB 2: A4 1페이지 전자연구노트 프리뷰 =================
with tab_preview:
    if not st.session_state.current_report:
        st.info("💡 아직 생성된 전자연구노트가 없습니다.\n\n대화창에서 내용을 기록하신 후 **상단의 [⚡ 1페이지 전자노트 생성]** 버튼을 누르거나 채팅으로 **'전자노트 만들어줘'**라고 말씀해 보세요!")
    else:
        # 다운로드 및 내보내기 툴바
        dl1, dl2, dl3, dl4 = st.columns([3, 2, 2, 2])
        
        with dl1:
            st.success("✅ **A4 1페이지 표준 규격으로 생성 완료** (브라우저 인쇄 단축키 `Ctrl + P`)")

        with dl2:
            # HTML 다운로드
            st.download_button(
                label="🌐 HTML 다운로드",
                data=st.session_state.current_html,
                file_name=f"lab_note_{st.session_state.current_report.get('date', 'report')}.html",
                mime="text/html",
                use_container_width=True
            )

        with dl3:
            # Markdown 다운로드
            md_content = generate_markdown_note(st.session_state.current_report)
            st.download_button(
                label="📝 Markdown 다운로드",
                data=md_content,
                file_name=f"lab_note_{st.session_state.current_report.get('date', 'report')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with dl4:
            # JSON 백업 다운로드
            json_str = json.dumps(st.session_state.current_report, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 JSON 백업",
                data=json_str,
                file_name=f"lab_note_{st.session_state.current_report.get('date', 'report')}.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown(
            """
            > [!TIP]
            > **완벽한 A4 1페이지 PDF 저장 방법**:
            > 아래 프리뷰 상단의 **'🖨️ A4 1페이지 인쇄 / PDF 저장'** 버튼을 누르거나 키보드에서 `Ctrl + P`를 누른 뒤, **[대상: PDF로 저장]**, **[용지 크기: A4]**, **[설정 더보기 > 배경 그래픽: 체크]**하시면 여백 없이 깔끔한 1페이지 연구노트 PDF가 완성됩니다!
            """
        )

        # 실제 A4 HTML 임베드 뷰어
        components.html(st.session_state.current_html, height=1150, scrolling=True)


# ================= TAB 3: 데이터 & 사진 보관소 =================
with tab_storage:
    st.markdown("### 🗄️ 세션 데이터 및 사진 보관소")
    
    col_img, col_data = st.columns(2)
    
    with col_img:
        st.markdown("#### 📷 업로드된 사진 목록")
        if not st.session_state.images:
            st.caption("업로드된 사진이 없습니다.")
        else:
            for idx, img_item in enumerate(st.session_state.images):
                with st.container():
                    st.image(img_item["bytes"], caption=f"사진 {idx+1}: {img_item['caption']}", use_container_width=True)
                    st.divider()

    with col_data:
        st.markdown("#### 📊 업로드된 데이터 테이블 및 수식 이력")
        if not st.session_state.data_tables:
            st.caption("업로드된 데이터 테이블이 없습니다.")
        else:
            for t_item in st.session_state.data_tables:
                st.markdown(f"**{t_item['name']}**")
                if t_item["df"] is not None:
                    st.dataframe(t_item["df"].head(10), use_container_width=True)
                else:
                    st.text(t_item["summary"])
                st.divider()

        st.markdown("#### 🧮 수행된 수식 계산 내역")
        if not st.session_state.calculations:
            st.caption("수행된 계산 내역이 없습니다.")
        else:
            for c_item in st.session_state.calculations:
                st.code(f"{c_item['expr']} = {c_item['result']}")
