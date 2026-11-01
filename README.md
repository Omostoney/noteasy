# 🧪 NoteEasy - 스마트 AI 멀티모달 전자연구노트

> **"대화하고, 사진과 데이터를 올리고, 수식을 계산하다가... 마지막에 '전자노트 만들어줘' 하면 A4 1페이지 규격의 표준 전자연구노트로 자동 정리해주는 스마트 실험 어시스턴트"**

---

## ✨ 핵심 기능

1. **실시간 실험 기록 & 대화 (Chat & Memo)**:
   - 실험 도중 메모, 관찰 일지, 조건 변경 사항을 실시간 기록
   - AI 에이전트와 질문 및 과학적 질의응답
2. **멀티모달 데이터 입력 (사진, 파일, 표, 계산)**:
   - **📷 사진 업로드**: 실험 장비, 시료, 반응 색상 변화, 현미경 사진 등 등록 및 AI 시각 분석
   - **📁 데이터 파일 파싱**: CSV, Excel(`xlsx`), TXT 파일을 업로드하면 데이터프레임과 기초 통계량 자동 추출
   - **🧮 간편 수식 계산기**: 파이썬 엔진을 통한 수율, 희석 배율, 평균 등 안전 연산 및 기록
3. **원클릭 A4 1페이지 전자연구노트 (One-page ELN)**:
   - *"전자노트 만들어줘"* 명령 또는 **[⚡ 1페이지 전자노트 생성]** 버튼 클릭 시,
   - **실험명, 연구자, 목적, 재료/조건, 절차 타임라인, 결과(사진+표+수치), 고찰 및 결론**으로 완벽하게 구조화
   - 인쇄 최적화 CSS로 A4 1페이지 규격 자동 맞춤
4. **인쇄 및 다양한 포맷 내보내기**:
   - `Ctrl + P`를 통한 고화질 **A4 PDF 저장 / 인쇄**
   - **HTML 다운로드**, **Markdown(.md) 다운로드**, **JSON 백업** 지원

---

## 🚀 빠른 시작 (로컬 실행)

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 실행
```bash
streamlit run app.py
```
브라우저에서 `http://localhost:8501`로 자동 열립니다.

---

## 🌐 다른 사람들에게 배포하는 방법 (Streamlit Cloud 무료 배포)

이 프로젝트는 **Streamlit Community Cloud**를 통해 누구에게나 웹 링크 하나로 손쉽게 무료 배포할 수 있도록 최적화되어 있습니다:

### Step 1: GitHub 리포지토리 생성
1. [GitHub](https://github.com/)에 로그인하고 새 리포지토리(예: `noteasy`)를 생성합니다.
2. 현재 프로젝트의 파일들을 GitHub에 푸시합니다:
```bash
git init
git add .
git commit -m "feat: NoteEasy - Multimodal One-Page Lab Notebook"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/noteasy.git
git push -u origin main
```

### Step 2: Streamlit Cloud 연동
1. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
2. **[Create app]** 버튼을 클릭합니다.
3. 방금 올린 GitHub 저장소(`noteasy`), 브랜치(`main`), 메인 파일 경로(`app.py`)를 선택합니다.

### Step 3: API Key 설정 (선택 사항)
- **모든 사용자 공용으로 제공하고 싶을 때**:
  Streamlit Cloud 앱 대시보드의 **[App Settings] > [Secrets]** 에 아래와 같이 추가합니다:
  ```toml
  GEMINI_API_KEY = "발급받은_Google_Gemini_API_키"
  ```
- **사용자 각자의 키를 쓰게 하고 싶을 때**:
  별도 설정 없이 배포하면, 사용자가 사이드바 입력창에 본인의 무료 API Key를 입력하여 사용할 수 있습니다. (미입력 시에도 스마트 데모 모드로 둘러보기 가능)

---

## 📁 디렉터리 구조

```
noteasy/
├── app.py                     # Streamlit 메인 애플리케이션
├── core/
│   ├── ai_agent.py            # Gemini 2.5/2.0 멀티모달 AI 연동 및 프롬프트
│   ├── data_handler.py        # CSV/Excel 파서, 통계 추출 및 수식 계산기
│   └── report_builder.py      # A4 1페이지 반응형 인쇄 HTML 및 Markdown 빌더
├── .streamlit/
│   ├── config.toml            # UI 테마 및 서버 설정
│   └── secrets.toml.example   # 비밀키 설정 예시
├── requirements.txt           # 배포용 의존성 패키지
└── README.md                  # 사용 및 배포 설명서
```
