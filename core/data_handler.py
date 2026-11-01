import io
import math
import pandas as pd
from typing import Dict, Any, Optional, Tuple

def parse_uploaded_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], str]:
    """
    업로드된 파일(CSV, Excel, TXT, JSON)을 파싱하여 DataFrame과 요약 텍스트를 반환합니다.
    """
    filename = uploaded_file.name.lower()
    df = None
    summary = ""
    
    try:
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="cp949")
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        elif filename.endswith(".json"):
            df = pd.read_json(uploaded_file)
        elif filename.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            summary = f"**텍스트 파일 내용 미리보기 ({len(content)} 글자)**:\n\n{content[:500]}..."
            return None, summary
        else:
            return None, f"지원되지 않는 파일 형식입니다: {filename}"
        
        if df is not None:
            shape_info = f"총 {df.shape[0]}행 × {df.shape[1]}열"
            cols = ", ".join(list(df.columns[:8]))
            if len(df.columns) > 8:
                cols += f" 외 {len(df.columns) - 8}개"
            summary = f"**데이터셋 정보**: {uploaded_file.name} ({shape_info})\n- 열 목록: {cols}\n"
            
            # 수치형 요약
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                desc = df[numeric_cols].describe().round(2).to_dict()
                summary += f"- 주요 수치 요약 컬럼 수: {len(numeric_cols)}개"
            
            return df, summary
    except Exception as e:
        return None, f"파일 파싱 중 오류가 발생했습니다: {str(e)}"

def dataframe_to_markdown_summary(df: pd.DataFrame, max_rows: int = 8) -> str:
    """DataFrame의 상위 행과 기초 통계를 마크다운 형태로 변환합니다."""
    if df is None or df.empty:
        return ""
    preview = df.head(max_rows).to_markdown(index=False)
    summary_text = f"### [데이터 표 미리보기 (상위 {min(len(df), max_rows)}행)]\n{preview}\n\n"
    
    num_cols = df.select_dtypes(include=["number"]).columns
    if len(num_cols) > 0:
        desc_df = df[num_cols].agg(['mean', 'std', 'min', 'max']).round(3)
        summary_text += f"### [기초 통계량 (평균/표준편차/최소/최대)]\n{desc_df.to_markdown()}\n"
    return summary_text

def safe_calculate(expression: str) -> Dict[str, Any]:
    """
    간단한 수학 및 과학 연산 수식을 안전하게 계산합니다.
    """
    safe_dict = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "pi": math.pi,
        "e": math.e
    }
    
    clean_expr = expression.strip()
    try:
        # 안전한 eval 환경 (내장함수 제한)
        result = eval(clean_expr, {"__builtins__": None}, safe_dict)
        if isinstance(result, float):
            formatted_result = f"{result:.4g}" if abs(result) < 1e-4 or abs(result) > 1e6 else f"{result:.4f}".rstrip('0').rstrip('.')
        else:
            formatted_result = str(result)
        return {
            "success": True,
            "expression": clean_expr,
            "result": formatted_result,
            "raw": result
        }
    except Exception as e:
        return {
            "success": False,
            "expression": clean_expr,
            "error": f"계산 오류: {str(e)}"
        }
