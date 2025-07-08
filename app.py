import streamlit as st
from openai import OpenAI
import base64
import os
import json
import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from pptx import Presentation
from docx import Document
from PIL import Image
import pytesseract
import io
import time

# 설정
st.set_page_config(page_title="CAMPER - Final Enhanced", page_icon="📧", layout="wide")

# CSS 스타일 추가 (Bootstrap Icons CDN 포함 + 블러 문제 해결)
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
<style>
    /* 블러 문제 해결을 위한 기본 설정 */
    .stApp {
        background-color: white !important;
    }
    
    .main .block-container {
        background-color: white !important;
        opacity: 1 !important;
    }
    
    /* 입력 필드 포커스 시 블러 방지 */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > div:focus {
        background-color: white !important;
        opacity: 1 !important;
    }
    
    /* 메인 헤더 */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* 섹션 헤더 */
    .section-header {
        background: #f8f9fa;
        padding: 0.5rem 1rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    /* 단계별 제목 강조 (더 강하게) */
    .stExpander > div > div > div > div > p {
        font-size: 1.4em !important;
        font-weight: 700 !important;
        color: white !important;
        background: linear-gradient(135deg, #354F9B, #667eea) !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        margin: 0 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3) !important;
    }
    
    /* 소제목 강조 (더 부드럽게) */
    .step-subtitle {
        font-size: 1.0em;
        font-weight: 500;
        color: #666;
        margin: 15px 0 8px 0;
        padding: 6px 10px;
        background-color: #f8f9fa;
        border-left: 2px solid #ddd;
        border-radius: 3px;
    }
    
    /* 입력 그룹 영역 구분 */
    .input-group {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    
    /* 버튼 그룹 우측 정렬 */
    .button-group {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin: 15px 0;
        padding: 10px;
        background-color: #fafafa;
        border-radius: 6px;
        border: 1px solid #e8e8e8;
    }
    
    /* 도움말 텍스트 */
    .help-text {
        background: #e3f2fd;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.9em;
        color: #1565c0;
        margin-bottom: 1rem;
    }
    
    /* 상태 메시지 */
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    /* 탭 스타일 개선 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }

</style>
""", unsafe_allow_html=True)

# OpenAI 클라이언트 초기화 및 연결 테스트
def initialize_openai_client():
    """OpenAI 클라이언트를 초기화하고 연결을 테스트합니다."""
    try:
        # API 키 확인 (우선순위: secrets.toml > 환경변수 > .env 파일)
        api_key = None
        
        # 1. Streamlit secrets에서 확인
        try:
            api_key = st.secrets["openai"]["api_key"]
        except KeyError:
            pass
        
        # 2. 환경변수에서 확인
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        # 3. .env 파일에서 확인
        if not api_key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("OPENAI_API_KEY")
            except ImportError:
                pass
        
        if not api_key:
            st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
            st.markdown("""
            **API 키 설정 방법:**
            1. `.streamlit/secrets.toml` 파일에 설정 (권장)
            2. 환경변수 `OPENAI_API_KEY` 설정
            3. `.env` 파일에 설정
            """)
            st.stop()
        
        # OpenAI 클라이언트 초기화
        client = OpenAI(api_key=api_key)
        
        # 연결 테스트
        try:
            test_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )

            return client
            
        except Exception as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                st.error("❌ OpenAI API 사용량 한도를 초과했습니다. 새로운 API 키가 필요합니다.")
            elif "invalid_api_key" in error_msg or "authentication" in error_msg.lower():
                st.error("❌ OpenAI API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            elif "model_not_found" in error_msg:
                st.error("❌ GPT-4 모델에 접근할 수 없습니다. API 키 권한을 확인해주세요.")
            else:
                st.error(f"❌ OpenAI API 연결 오류: {error_msg}")
            
            st.markdown("""
            **문제 해결 방법:**
            1. API 키가 유효한지 확인
            2. API 사용량 한도 확인
            3. GPT-4 모델 접근 권한 확인
            4. 인터넷 연결 상태 확인
            """)
            st.stop()
            
    except Exception as e:
        st.error(f"❌ OpenAI 클라이언트 초기화 실패: {str(e)}")
        st.stop()

# OpenAI 클라이언트 초기화
client = initialize_openai_client()