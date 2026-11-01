import base64
from typing import Dict, Any, List, Optional
import markdown

def markdown_to_html(md_text: str) -> str:
    """간단한 마크다운을 HTML로 변환합니다 (표 확장 포함)."""
    try:
        return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    except Exception:
        return f"<pre>{md_text}</pre>"

def generate_a4_html(note_data: Dict[str, Any], images_b64: Optional[List[str]] = None) -> str:
    """
    A4 1페이지에 정확히 들어맞도록 인쇄 최적화된 HTML 문서를 생성합니다.
    """
    title = note_data.get("title", "실험 전자연구노트")
    experimenter = note_data.get("experimenter", "연구원")
    date_str = note_data.get("date", "2026-11-02")
    objective = note_data.get("objective", "실험 목적이 기술되지 않았습니다.")
    
    materials = note_data.get("materials_and_conditions", [])
    materials_html = "".join([f"<li>{m}</li>" for m in materials]) if materials else "<li>기본 조건 준수</li>"
    
    procedures = note_data.get("procedure_steps", [])
    procedures_html = "".join([f"<li>{p}</li>" for p in procedures]) if procedures else "<li>표준 절차 수행</li>"
    
    results_summary = note_data.get("results_summary", "")
    table_md = note_data.get("result_table_markdown", "")
    table_html = markdown_to_html(table_md) if table_md else ""
    
    findings = note_data.get("key_findings", [])
    findings_html = "".join([f"<li><strong>발견/결과:</strong> {f}</li>" for f in findings]) if findings else ""
    
    discussion = note_data.get("discussion_and_conclusion", "이상 없음.")
    
    # 이미지 갤러리 HTML
    images_html = ""
    if images_b64:
        img_tags = "".join([
            f'<div class="report-img-wrapper"><img src="data:image/jpeg;base64,{img}" alt="실험 사진"/></div>'
            for img in images_b64[:2]
        ])
        images_html = f'<div class="report-img-grid">{img_tags}</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{title} - 전자연구노트</title>
<style>
  @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
  
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    background-color: #f8fafc;
    color: #1e293b;
    line-height: 1.45;
    padding: 20px;
    font-size: 13px;
  }}

  .a4-page {{
    background: #ffffff;
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto;
    padding: 18mm 18mm;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-radius: 4px;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}

  /* 인쇄 전용 스타일 (Ctrl + P 시 A4 1페이지에 딱 맞춤) */
  @media print {{
    body {{
      background: #ffffff;
      padding: 0;
      margin: 0;
    }}
    .a4-page {{
      width: 100% !important;
      min-height: 100% !important;
      height: 100vh !important;
      box-shadow: none !important;
      border-radius: 0 !important;
      padding: 10mm 12mm !important;
      margin: 0 !important;
      page-break-after: avoid;
      page-break-inside: avoid;
    }}
    .no-print {{
      display: none !important;
    }}
  }}

  .header {{
    border-bottom: 2px solid #0f172a;
    padding-bottom: 10px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}

  .header-left h1 {{
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }}

  .header-left .meta {{
    font-size: 11px;
    color: #64748b;
  }}

  .header-right {{
    text-align: right;
  }}

  .sign-box {{
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    background: #f8fafc;
    display: inline-block;
  }}

  .section {{
    margin-bottom: 12px;
  }}

  .section-title {{
    font-size: 12.5px;
    font-weight: 700;
    color: #1e40af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-left: 3px solid #2563eb;
    padding-left: 6px;
    margin-bottom: 6px;
    background: #eff6ff;
    padding-top: 2px;
    padding-bottom: 2px;
  }}

  .section-content {{
    font-size: 12px;
    color: #334155;
  }}

  ul, ol {{
    padding-left: 18px;
    margin-top: 2px;
  }}

  li {{
    margin-bottom: 2px;
  }}

  .grid-2col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 10px;
  }}

  /* 표 스타일 */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    margin: 6px 0;
  }}

  th, td {{
    border: 1px solid #cbd5e1;
    padding: 4px 8px;
    text-align: left;
  }}

  th {{
    background-color: #f1f5f9;
    color: #1e293b;
    font-weight: 600;
  }}

  tr:nth-child(even) {{
    background-color: #f8fafc;
  }}

  /* 사진 그리드 */
  .report-img-grid {{
    display: flex;
    gap: 8px;
    margin-top: 6px;
  }}

  .report-img-wrapper {{
    flex: 1;
    max-height: 125px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    background: #000000;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .report-img-wrapper img {{
    max-width: 100%;
    max-height: 125px;
    object-fit: cover;
  }}

  .footer {{
    border-top: 1px solid #e2e8f0;
    padding-top: 8px;
    font-size: 10px;
    color: #94a3b8;
    display: flex;
    justify-content: space-between;
    margin-top: auto;
  }}

  /* 상단 툴바 */
  .toolbar {{
    max-width: 210mm;
    margin: 0 auto 12px auto;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }}

  .print-btn {{
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(37,99,235,0.3);
  }}

  .print-btn:hover {{
    background-color: #1d4ed8;
  }}
</style>
</head>
<body>

<div class="toolbar no-print">
  <button class="print-btn" onclick="window.print()">🖨️ A4 1페이지 인쇄 / PDF 저장 (Ctrl+P)</button>
</div>

<div class="a4-page">
  <div>
    <!-- 헤더 -->
    <div class="header">
      <div class="header-left">
        <h1>{title}</h1>
        <div class="meta">
          <strong>연구/실험 일시:</strong> {date_str} &nbsp;|&nbsp; 
          <strong>담당 연구자:</strong> {experimenter} &nbsp;|&nbsp; 
          <strong>문서번호:</strong> ELN-{date_str.replace('-', '')}-01
        </div>
      </div>
      <div class="header-right">
        <div class="sign-box">
          서명 / 승인: _________________ (인)
        </div>
      </div>
    </div>

    <!-- 1. 실험 목적 -->
    <div class="section">
      <div class="section-title">1. 실험 목적 및 개요 (Objective)</div>
      <div class="section-content">
        <p>{objective}</p>
      </div>
    </div>

    <!-- 2. 재료 및 절차 (2컬럼 배치) -->
    <div class="grid-2col">
      <div class="section">
        <div class="section-title">2. 준비물 및 조건 (Materials)</div>
        <div class="section-content">
          <ul>{materials_html}</ul>
        </div>
      </div>

      <div class="section">
        <div class="section-title">3. 주요 실험 절차 (Procedure)</div>
        <div class="section-content">
          <ol>{procedures_html}</ol>
        </div>
      </div>
    </div>

    <!-- 4. 결과 및 데이터 -->
    <div class="section">
      <div class="section-title">4. 실험 결과 및 데이터 (Results & Data)</div>
      <div class="section-content">
        {f"<p style='margin-bottom:4px;'>{results_summary}</p>" if results_summary else ""}
        {table_html}
        {f"<ul>{findings_html}</ul>" if findings_html else ""}
        {images_html}
      </div>
    </div>

    <!-- 5. 고찰 및 결론 -->
    <div class="section" style="margin-bottom:0;">
      <div class="section-title">5. 고찰 및 결론 (Discussion & Conclusion)</div>
      <div class="section-content">
        <p>{discussion}</p>
      </div>
    </div>
  </div>

  <!-- 푸터 -->
  <div class="footer">
    <span>NoteEasy Electronic Lab Notebook System</span>
    <span>A4 One-Page Standard Verified &bull; Confidential Research Record</span>
  </div>
</div>

</body>
</html>
"""
    return html_content

def generate_markdown_note(note_data: Dict[str, Any]) -> str:
    """다운로드 및 공유를 위한 순수 마크다운 포맷 생성"""
    title = note_data.get("title", "실험 전자연구노트")
    date_str = note_data.get("date", "2026-11-02")
    experimenter = note_data.get("experimenter", "연구원")
    objective = note_data.get("objective", "")
    materials = "\n".join([f"- {m}" for m in note_data.get("materials_and_conditions", [])])
    procedures = "\n".join([f"{i+1}. {p}" for i, p in enumerate(note_data.get("procedure_steps", []))])
    results_summary = note_data.get("results_summary", "")
    table_md = note_data.get("result_table_markdown", "")
    findings = "\n".join([f"- {f}" for f in note_data.get("key_findings", [])])
    discussion = note_data.get("discussion_and_conclusion", "")

    return f"""# {title}

**일시:** {date_str} | **연구자:** {experimenter}

---

## 1. 실험 목적 및 개요
{objective}

## 2. 재료 및 조건
{materials}

## 3. 실험 절차
{procedures}

## 4. 실험 결과 및 데이터
{results_summary}

{table_md}

### 주요 수치 및 관찰점
{findings}

## 5. 고찰 및 결론
{discussion}

---
*Generated by NoteEasy - One-Page AI Lab Assistant*
"""
