import streamlit as st
from openai import OpenAI
import base64
import os
import json
import shutil
import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from pptx import Presentation
from docx import Document
from PIL import Image
import pytesseract
import io

# 설정
st.set_page_config(page_title="CAMPER", page_icon="📧", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
except KeyError:
    st.error("OpenAI API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
    st.stop()

os.makedirs("images", exist_ok=True)

# 자료 처리 함수들
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        # 불필요한 태그 제거
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # 공백 정리
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return ' '.join(chunk for chunk in chunks if chunk)
    except Exception as e:
        st.error(f"URL 처리 오류: {str(e)}")
        return None

def extract_text_from_pdf(file):
    try:
        reader = PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"PDF 처리 오류: {str(e)}")
        return None

def extract_text_from_pptx(file):
    try:
        prs = Presentation(io.BytesIO(file.read()))
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"PPTX 처리 오류: {str(e)}")
        return None

def extract_text_from_docx(file):
    try:
        doc = Document(io.BytesIO(file.read()))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"DOCX 처리 오류: {str(e)}")
        return None

def extract_text_from_image(file):
    try:
        image = Image.open(io.BytesIO(file.read()))
        text = pytesseract.image_to_string(image, lang='kor+eng')
        return text.strip()
    except Exception as e:
        st.error(f"이미지 처리 오류: {str(e)}")
        return None

def summarize_content(text):
    if not text or len(text.strip()) < 50:
        return "요약할 내용이 부족합니다."
    
    prompt = f"""다음 내용을 3줄 이내(최대 250자)로 핵심만 간단히 요약해주세요:

{text[:3000]}  # 너무 긴 텍스트는 잘라서 처리

요구사항:
- 3줄 이내로 압축
- 핵심 내용만 포함
- 비즈니스 관점에서 중요한 정보 우선
- 최대 250자 제한"""
    
    try:
        r = client.chat.completions.create(
            model="gpt-4", 
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"요약 처리 오류: {str(e)}")
        return "요약 처리 중 오류가 발생했습니다."

# 배경 밝기에 따른 로고 선택 함수
def select_logo_by_brightness(theme_color, light_logo, dark_logo):
    # 색상 밝기 계산 (hex -> RGB -> 밝기)
    hex_color = theme_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    brightness = (r * 0.299 + g * 0.587 + b * 0.114)
    return dark_logo if brightness > 128 else light_logo

# 헬퍼 함수들
def load_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def generate_svg_icon(keyword, color1, color2, filename):
    prompt = f"""Create a minimal square SVG icon for '{keyword}'. Use colors: {color1} and {color2}. No text, simple shapes only. Output: <svg>...</svg> code"""
    try:
        r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        svg_match = re.search(r"<svg[\s\S]*?</svg>", r.choices[0].message.content)
        if svg_match:
            with open(f"images/{filename}", "w", encoding="utf-8") as f:
                f.write(svg_match.group())
            return f"images/{filename}"
    except Exception as e:
        st.error(f"SVG 생성 오류: {str(e)}")
    return None

def generate_banner_svg(tone, color1, color2):
    prompt = f"""
Create a wide banner SVG (700x200px) with a '{tone}' theme.  
This is for a B2B IT marketing email banner.  
Use only {color1} and {color2}, with soft gradients and clean tones.  
Do not include realistic or artistic details.  
Do not use complex illustrations, buildings, people, or nature.  
Design should be minimal, clean, and professional, with visual balance.  
Leave enough blank space for overlaid title and subtitle text.  
Output: <svg>...</svg> code.
"""
    try:
        r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        svg_match = re.search(r"<svg[\s\S]*?</svg>", r.choices[0].message.content)
        if svg_match:
            return svg_match.group()
    except Exception as e:
        st.error(f"SVG 배너 생성 오류: {str(e)}")
    return None

def create_html_edm(content, edm_type, company_logo_light, company_logo_dark, partner_logo, icons, cta_url, sessions=None, theme_color="#8EC5FC", bg_image_path=None, event_info=None, features_data=None, layout_option="자동", bg_svg_code=None):
    # 배경색에 따라 적절한 로고 선택
    selected_logo = select_logo_by_brightness(theme_color, company_logo_light, company_logo_dark)
    company_logo_b64 = base64.b64encode(selected_logo.read()).decode() if selected_logo else ""
    partner_logo_b64 = base64.b64encode(partner_logo.read()).decode() if partner_logo else ""

    # 배경 이미지와 헤더 통합
    header_section = ""
    if bg_svg_code:
        header_section = f'''
        <div class="hero-section" style="position:relative; height:200px; display:flex; flex-direction:column; justify-content:center; align-items:center; color:white; text-shadow:2px 2px 4px rgba(0,0,0,0.7); overflow:hidden;">
            <div style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:1;">
                {bg_svg_code}
            </div>
            <div style="position:relative; z-index:2; text-align:center;">
                <div class="logo-section" style="margin-bottom:10px;">
                    <img src="data:image/png;base64,{company_logo_b64}" style="height:40px; margin-right:15px;">
                    {f'<img src="data:image/png;base64,{partner_logo_b64}" style="height:40px;">' if partner_logo_b64 else ''}
                </div>
                <h1 style="font-size:1.8em; margin:5px 0; text-align:center;">{content.get('title')}</h1>
                <h3 style="font-size:1.1em; margin:5px 0; text-align:center;">{content.get('subtitle')}</h3>
            </div>
        </div>'''
    elif bg_image_path and os.path.exists(bg_image_path):
        bg_b64 = load_image_base64(bg_image_path)
        header_section = f'''
        <div class="hero-section" style="position:relative; background-image:url(data:image/png;base64,{bg_b64}); background-size:cover; background-position:center; height:200px; display:flex; flex-direction:column; justify-content:center; align-items:center; color:white; text-shadow:2px 2px 4px rgba(0,0,0,0.7);">
            <div class="logo-section" style="margin-bottom:10px;">
                <img src="data:image/png;base64,{company_logo_b64}" style="height:40px; margin-right:15px;">
                {f'<img src="data:image/png;base64,{partner_logo_b64}" style="height:40px;">' if partner_logo_b64 else ''}
            </div>
            <h1 style="font-size:1.8em; margin:5px 0; text-align:center;">{content.get('title')}</h1>
            <h3 style="font-size:1.1em; margin:5px 0; text-align:center;">{content.get('subtitle')}</h3>
        </div>'''
    else:
        # 배경 이미지가 없을 때는 기본 헤더
        header_section = f'''
        <div class="header" style="text-align:center; background:linear-gradient(135deg, {theme_color}, {theme_color}aa); color:white; padding:40px 20px;">
            <div class="logo-section" style="margin-bottom:20px;">
                <img src="data:image/png;base64,{company_logo_b64}" style="height:60px; margin-right:20px;">
                {f'<img src="data:image/png;base64,{partner_logo_b64}" style="height:60px;">' if partner_logo_b64 else ''}
            </div>
            <h1 style="font-size:2.5em; margin:10px 0;">{content.get('title')}</h1>
            <h3 style="font-size:1.5em; margin:10px 0;">{content.get('subtitle')}</h3>
        </div>'''

    # 소개형 기능 섹션 생성
    features_html = ""
    if edm_type == "소개형" and features_data:
        valid_features = [f for f in features_data if f['feature_name'].strip()]
        if valid_features:
            # 레이아웃에 따른 컬럼 수 결정
            if layout_option == "1xN (세로)":
                cols_per_row = 1
            elif layout_option == "2xN (2열)":
                cols_per_row = 2
            elif layout_option == "3xN (3열)":
                cols_per_row = 3
            else:  # 자동
                cols_per_row = 3 if len(valid_features) > 4 else 2 if len(valid_features) > 2 else 1
            
            features_html = f'<div class="features-section" style="margin: 30px 20px;"><h3 style="color: {theme_color}; margin-bottom: 20px;">주요 기능</h3>'
            features_html += f'<div style="display: grid; grid-template-columns: repeat({cols_per_row}, 1fr); gap: 20px; margin-bottom: 20px;">'
            
            for i, feature in enumerate(valid_features):
                icon_html = f'<img src="data:image/svg+xml;base64,{load_image_base64(icons[i])}" style="width:40px;height:40px;margin-bottom:10px;">' if i < len(icons) else ''
                features_html += f'''
                <div style="text-align: center; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; background: #fafafa;">
                    {icon_html}
                    <h4 style="color: {theme_color}; margin: 10px 0 5px 0; font-size: 1.1em;">{feature['feature_name']}</h4>
                    <p style="color: #666; font-size: 0.9em; line-height: 1.4; margin: 0;">{feature['feature_desc']}</p>
                </div>'''
            
            features_html += '</div></div>'
    
    # 기존 아이콘 HTML (초청형용)
    icons_html = "".join([f'<img src="data:image/svg+xml;base64,{load_image_base64(icon)}" style="width:50px;height:50px;margin:10px;">' for icon in icons[:8]]) if edm_type == "초청형" else ""

    # 초청형 행사 정보 박스
    event_info_html = ""
    if edm_type == "초청형" and event_info:
        event_info_html = f'''
        <div class="event-info-box" style="background: {theme_color}dd; color: white; margin: 20px; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <table style="width: 100%; color: white; border-collapse: collapse;">
                <tr><td style="font-weight: bold; padding: 8px 0; width: 20%;">일시</td><td style="padding: 8px 0;">{event_info.get('date', '미정')}</td></tr>
                <tr><td style="font-weight: bold; padding: 8px 0;">장소</td><td style="padding: 8px 0;">{event_info.get('location', '미정')}</td></tr>
                <tr><td style="font-weight: bold; padding: 8px 0;">대상</td><td style="padding: 8px 0;">{event_info.get('target', '미정')}</td></tr>
                <tr><td style="font-weight: bold; padding: 8px 0;">주최</td><td style="padding: 8px 0;">{event_info.get('host', '미정')}</td></tr>
            </table>
        </div>'''

    agenda_html = ""
    if edm_type == "초청형" and sessions:
        rows = "".join([f"<tr><td>{s['time']}</td><td>{s['title']}</td><td>{s['speaker']}</td></tr>" for s in sessions])
        agenda_html = f"<h3>AGENDA</h3><table border='1' width='100%' cellpadding='5' cellspacing='0'><tr><th>Time</th><th>Title</th><th>발표자</th></tr>{rows}</table>"

    return f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>{content.get('title')}</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; background: #f5f5f5; margin:0; padding:0; }}
        .container {{ max-width: 700px; margin: auto; background: #fff; }}
        .section {{ margin: 20px; }}
        .cta {{ text-align: center; margin: 30px 0; }}
        .cta-button {{ background: {theme_color}dd; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .highlight-text {{ color: {theme_color}; font-weight: 600; }}
        .footer-bar {{ background-color: #555555; color: white; font-size: 12px; display: flex; justify-content: space-between; align-items: center; padding: 20px; }}
        .footer-bar a {{ color: white; text-decoration: none; }}
    </style>
    </head><body><div class='container'>
    {header_section}
    {event_info_html}
    <div class='section'><strong class="highlight-text">{content.get('highlight')}</strong></div>
    <div class='section'>{content.get('body').replace('\n', '<br>')}</div>
    {agenda_html}
    <div class='section'>{icons_html}</div>
    {features_html}
    <div class='section'>{content.get('closing')}</div>
    <div class='cta'><a href='{cta_url}' class='cta-button'>{content.get('cta')}</a></div>
    <div class='footer-bar'>
        <img src="data:image/png;base64,{company_logo_b64}" style="height:40px;">
        <div style="text-align:right; line-height:1.6;">
            ㈜웅진 &nbsp;&nbsp;|&nbsp;&nbsp;
            서울특별시 중구 청계천로24 케이스퀘어시티 7층 &nbsp;&nbsp;|&nbsp;&nbsp;
            <a href="https://www.woongjin.com">www.woongjin.com</a>
        </div>
    </div></body></html>"""

def main():
    st.title("📧 Camper의 e-DM Generator")
    
    # 2열 레이아웃
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 입력 폼")
        
        # 솔루션 소개 자료 영역 (최상단)
        st.subheader("📄 솔루션 소개 자료 (선택)")
        
        # URL 또는 파일 선택
        input_type = st.radio("자료 입력 방식", ["없음", "URL", "파일 업로드"], horizontal=True)
        
        material_summary = ""
        if input_type == "URL":
            url_input = st.text_input("웹페이지 URL", placeholder="https://example.com")
            if url_input and st.button("URL 분석", key="analyze_url"):
                with st.spinner("웹페이지 내용을 분석 중..."):
                    extracted_text = extract_text_from_url(url_input)
                    if extracted_text:
                        material_summary = summarize_content(extracted_text)
        
        elif input_type == "파일 업로드":
            uploaded_file = st.file_uploader(
                "파일 선택", 
                type=["pdf", "pptx", "docx", "jpg", "png"],
                help="PDF, PPTX, DOCX, JPG, PNG 파일을 지원합니다."
            )
            if uploaded_file and st.button("파일 분석", key="analyze_file"):
                with st.spinner("파일 내용을 분석 중..."):
                    file_type = uploaded_file.type
                    extracted_text = None
                    
                    if "pdf" in file_type:
                        extracted_text = extract_text_from_pdf(uploaded_file)
                    elif "presentation" in file_type or "pptx" in uploaded_file.name:
                        extracted_text = extract_text_from_pptx(uploaded_file)
                    elif "document" in file_type or "docx" in uploaded_file.name:
                        extracted_text = extract_text_from_docx(uploaded_file)
                    elif "image" in file_type:
                        extracted_text = extract_text_from_image(uploaded_file)
                    
                    if extracted_text:
                        material_summary = summarize_content(extracted_text)
        
        # 요약 결과 표시
        if material_summary:
            st.info(f"📋 **자료 요약**\n\n{material_summary}")
        
        st.divider()
        
        # e-DM 컨텐츠 (기본 설정)
        st.subheader("📧 e-DM 컨텐츠")
        edm_type = st.radio("유형", ["초청형", "소개형"])
        
        core = st.text_area("핵심 메시지 (필수)", placeholder="e-DM의 타이틀, 본문, 톤앤매너가 정해집니다.")
        
        title_suggestion = st.text_input("타이틀 (선택)", placeholder="입력하면 GPT가 비즈니스적으로 다듬어줍니다.", key="title_suggest")
        
        subtitle_suggestion = st.text_input("서브타이틀 (선택)", placeholder="입력하면 GPT가 비즈니스적으로 다듬어줍니다.", key="subtitle_suggest")
        
        target = st.text_input("타겟 고객", "예: IT 관리자")
        
        # 세부 정보
        if edm_type == "초청형":
            st.subheader("행사 세부 정보")
            invitation_text = st.text_area("초청의 글", placeholder="행사 목적, 주요 내용, 참석 베네핏을 비즈니스 정중체로 작성해주세요.")
            event_date = st.text_input("일시", "2024년 12월 15일 (금) 14:00-17:00")
            event_location = st.text_input("장소", "서울 강남구 컨퍼런스홀")
            event_target = st.text_input("대상", "IT 관리자, CTO")
            event_host = st.text_input("주최", "㈜웅진")
            session_n = st.number_input("세션 수", 1, 5, 2)
            sessions = []
            for i in range(int(session_n)):
                with st.expander(f"세션 {i+1}"):
                    t = st.text_input("시간", key=f"t_{i}")
                    ti = st.text_input("제목", key=f"ti_{i}")
                    sp = st.text_input("발표자", key=f"sp_{i}")
                    sessions.append({"time": t, "title": ti, "speaker": sp})
            event_url = st.text_input("신청 링크")
            cta = st.text_input("버튼 문구", "신청하기")
            info = f"초청의 글: {invitation_text}\n세션 제목들: {[s['title'] for s in sessions if s['title']]}"
            cta_url = event_url
        else:
            st.subheader("솔루션 소개")
            desc = st.text_area("제품/서비스 설명")
            
            # 레이아웃 옵션
            layout_option = st.selectbox("기능 레이아웃", ["1xN (세로)", "2xN (2열)", "3xN (3열)", "자동"])
            
            st.markdown("**기능 입력 (최대 10개)**")
            
            # 세션 상태 초기화
            if 'features_data' not in st.session_state:
                st.session_state.features_data = [{
                    'icon_keyword': '',
                    'feature_name': '',
                    'feature_desc': ''
                } for _ in range(10)]
            
            # 표 입력 모드
            input_mode = st.radio("입력 방식", ["표 입력", "블록 수정"], horizontal=True)
            
            if input_mode == "표 입력":
                st.markdown("표에서 데이터를 입력하면 블록에 자동 반영됩니다.")
                
                # 표 헤더
                cols = st.columns([2, 3, 5])
                with cols[0]:
                    st.markdown("**아이콘 키워드**")
                with cols[1]:
                    st.markdown("**기능명**")
                with cols[2]:
                    st.markdown("**기능 설명**")
                
                # 표 데이터 입력
                for i in range(10):
                    cols = st.columns([2, 3, 5])
                    with cols[0]:
                        icon_kw = st.text_input(f"아이콘{i+1}", value=st.session_state.features_data[i]['icon_keyword'], key=f"table_icon_{i}", label_visibility="collapsed")
                    with cols[1]:
                        feat_name = st.text_input(f"기능{i+1}", value=st.session_state.features_data[i]['feature_name'], key=f"table_name_{i}", label_visibility="collapsed")
                    with cols[2]:
                        feat_desc = st.text_input(f"설명{i+1}", value=st.session_state.features_data[i]['feature_desc'], key=f"table_desc_{i}", label_visibility="collapsed")
                    
                    # 데이터 동기화
                    st.session_state.features_data[i] = {
                        'icon_keyword': icon_kw,
                        'feature_name': feat_name,
                        'feature_desc': feat_desc
                    }
            
            else:  # 블록 수정 모드
                st.markdown("블록을 수정하면 표에 자동 반영됩니다.")
                
                # 비어있지 않은 기능들만 표시
                active_features = [i for i, f in enumerate(st.session_state.features_data) if f['feature_name'].strip()]
                
                if not active_features:
                    st.info("표 입력 모드에서 기능을 먼저 입력해주세요.")
                else:
                    for idx in active_features:
                        with st.expander(f"기능 {idx+1}: {st.session_state.features_data[idx]['feature_name']}"):
                            cols = st.columns([1, 4])
                            with cols[0]:
                                if st.button(f"삭제", key=f"del_{idx}"):
                                    st.session_state.features_data[idx] = {'icon_keyword': '', 'feature_name': '', 'feature_desc': ''}
                                    st.rerun()
                            
                            icon_kw = st.text_input("아이콘 키워드", value=st.session_state.features_data[idx]['icon_keyword'], key=f"block_icon_{idx}")
                            feat_name = st.text_input("기능명", value=st.session_state.features_data[idx]['feature_name'], key=f"block_name_{idx}")
                            feat_desc = st.text_area("기능 설명", value=st.session_state.features_data[idx]['feature_desc'], key=f"block_desc_{idx}")
                            
                            # 데이터 동기화
                            st.session_state.features_data[idx] = {
                                'icon_keyword': icon_kw,
                                'feature_name': feat_name,
                                'feature_desc': feat_desc
                            }
            
            # 기능 데이터 정리
            valid_features = [f for f in st.session_state.features_data if f['feature_name'].strip()]
            icon_kw = ", ".join([f['icon_keyword'] for f in valid_features if f['icon_keyword'].strip()])
            
            product_url = st.text_input("상세 URL")
            cta = st.text_input("버튼 문구", "문의하기")
            info = f"{desc}\n기능들: {[f['feature_name'] for f in valid_features]}"
            cta_url = product_url
        
        st.divider()
        
        # 디자인 톤 & 배경 효과
        st.subheader("🎨 디자인 톤 & 배경 효과")
        bg_main_color = st.color_picker("메인 컬러", "#8EC5FC")
        
        # 배경 요소 체크박스 일렬 구성
        st.markdown("**배경 효과**")
        cols = st.columns(5)
        bg_elements = []
        with cols[0]:
            if st.checkbox("그라데이션", key="bg_grad"):
                bg_elements.append("a soft gradient background")
        with cols[1]:
            if st.checkbox("반짝이", key="bg_spark"):
                bg_elements.append("sparkles")
        with cols[2]:
            if st.checkbox("빛망울", key="bg_bokeh"):
                bg_elements.append("bokeh-style dots")
        with cols[3]:
            if st.checkbox("곡선", key="bg_lines"):
                bg_elements.append("soft lines")
        with cols[4]:
            if st.checkbox("추상", key="bg_shapes"):
                bg_elements.append("abstract glowing shapes")
        
        uploaded_bg = st.file_uploader("배경 이미지 업로드 (선택)", type=["png", "jpg", "jpeg"])
        
        st.divider()
        
        # 로고 업로드 (제일 아래로)
        st.subheader("🏷️ 로고 업로드")
        company_logo_light = st.file_uploader("회사 로고 (밝은 배경용)", type=["png", "jpg"], help="밝은 배경에서 사용할 어두운 로고")
        company_logo_dark = st.file_uploader("회사 로고 (어두운 배경용)", type=["png", "jpg"], help="어두운 배경에서 사용할 밝은 로고")
        partner_logo = st.file_uploader("파트너 로고 (필요시 추가)", type=["png", "jpg"])
        
        # 생성 버튼
        generate_btn = st.button("🔨 e-DM 생성", use_container_width=True)
    
    with col2:
        st.header("🔍 미리보기")
        
        # 고정 설정
        st.markdown("**🔒 고정 설정**")
        lock_cols = st.columns(2)
        with lock_cols[0]:
            lock_text = st.checkbox("텍스트")
        with lock_cols[1]:
            lock_icons = st.checkbox("아이콘")
        
        st.divider()
        
        if generate_btn:
            with st.spinner("생성 중..."):
                # 배너 이미지 생성
                bg_image_path = None
                if uploaded_bg:
                    bg_path = f"images/uploaded_bg_{uploaded_bg.name}"
                    with open(bg_path, "wb") as f:
                        f.write(uploaded_bg.read())
                    bg_image_path = bg_path
                else:
                    # 배경 효과에 따른 톤 결정
                    if bg_elements:
                        if "sparkles" in bg_elements or "bokeh-style dots" in bg_elements:
                            tone = "bright and fresh"
                        elif "soft lines" in bg_elements or "abstract glowing shapes" in bg_elements:
                            tone = "tech-inspired"
                        else:
                            tone = "clean and professional"
                    else:
                        tone = "clean and professional"
                    
                    color1, color2 = bg_main_color, f"{bg_main_color}aa"
                    bg_svg_code = generate_banner_svg(tone, color1, color2)
                
                # 문구 생성
                default_content = {"title": "e-DM 제목", "subtitle": "부제목", "highlight": "핵심 메시지", "body": "본문 내용", "closing": "감사합니다", "cta": "자세히 보기"}
                
                if not lock_text:
                    # 타이틀/서브타이틀 제안이 있으면 GPT로 다듬기
                    refined_title = title_suggestion
                    refined_subtitle = subtitle_suggestion
                    
                    if title_suggestion:
                        title_refine_prompt = f"""다음 타이틀을 비즈니스 B2B 마케팅에 적합하게 다듬어주세요:
원본: {title_suggestion}
타겟: {target}
핵심 메시지: {core}

요구사항:
- 전문적이고 신뢰감 있는 톤
- 간결하면서도 임팩트 있게
- B2B 고객에게 어필할 수 있도록
- 20자 이내로 간결하게

다듬어진 타이틀만 응답해주세요."""
                        try:
                            r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": title_refine_prompt}])
                            refined_title = r.choices[0].message.content.strip().strip('"')
                        except:
                            refined_title = title_suggestion
                    
                    if subtitle_suggestion:
                        subtitle_refine_prompt = f"""다음 서브타이틀을 비즈니스 B2B 마케팅에 적합하게 다듬어주세요:
원본: {subtitle_suggestion}
타겟: {target}
핵심 메시지: {core}

요구사항:
- 타이틀을 보완하는 설명적 역할
- 전문적이고 명확한 표현
- 고객의 관심을 끌 수 있는 베네핏 강조
- 30자 이내로 간결하게

다듬어진 서브타이틀만 응답해주세요."""
                        try:
                            r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": subtitle_refine_prompt}])
                            refined_subtitle = r.choices[0].message.content.strip().strip('"')
                        except:
                            refined_subtitle = subtitle_suggestion
                    
                    # 다듬어진 타이틀/서브타이틀 반영
                    title_hint = f"\n타이틀: {refined_title}" if refined_title else ""
                    subtitle_hint = f"\n서브타이틀: {refined_subtitle}" if refined_subtitle else ""
                    
                    if edm_type == "초청형":
                        prompt = f"""다음 정보를 바탕으로 초청형 eDM 문구를 JSON 형식으로 생성해주세요:
타겟: {target}\n핵심: {core}\n{info}{title_hint}{subtitle_hint}

주의사항:
- 제공된 타이틀/서브타이틀이 있으면 반드시 그대로 사용
- body는 제공된 '초청의 글'을 기반으로 비즈니스 정중체로 작성
- 행사 목적, 주요 내용, 참석 베네핏을 간결하고 신뢰감 있게 표현
- 세션 제목들을 참고하여 내용 구성 가능

다음 형식으로 응답해주세요:
{{"title": "제목", "subtitle": "부제목", "highlight": "핵심 메시지", "body": "초청 문구 본문", "closing": "마무리 멘트", "cta": "버튼 텍스트"}}"""
                    else:
                        prompt = f"""다음 정보를 바탕으로 {edm_type} eDM 문구를 JSON 형식으로 생성해주세요:
타겟: {target}\n핵심: {core}\n정보: {info}{title_hint}{subtitle_hint}

주의사항:
- 제공된 타이틀/서브타이틀이 있으면 반드시 그대로 사용
- 비즈니스 B2B 톤으로 전문적이고 신뢰감 있게 작성

다음 형식으로 응답해주세요:
{{"title": "제목", "subtitle": "부제목", "highlight": "핵심 메시지", "body": "본문 내용", "closing": "마무리 멘트", "cta": "버튼 텍스트"}}"""
                    
                    try:
                        r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
                        j = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", r.choices[0].message.content, re.DOTALL)
                        content = json.loads(j.group()) if j else default_content
                        # 버튼 문구는 사용자 입력값 그대로 사용
                        content['cta'] = cta
                    except:
                        content = default_content
                        content['cta'] = cta
                        st.warning("JSON 파싱 실패로 기본값을 사용합니다.")
                else:
                    content = st.session_state.get("locked_content", default_content)
                    # 버튼 문구는 사용자 입력값 그대로 사용
                    content['cta'] = cta

                # 아이콘 생성
                color1, color2 = bg_main_color, f"{bg_main_color}aa"
                icons = []
                if not lock_icons and edm_type == "소개형":
                    if hasattr(st.session_state, 'features_data'):
                        valid_features = [f for f in st.session_state.features_data if f['icon_keyword'].strip()]
                        for i, feature in enumerate(valid_features[:8]):
                            if icon_path := generate_svg_icon(feature['icon_keyword'], color1, color2, f"icon_{i}.svg"):
                                icons.append(icon_path)
                    elif icon_kw:
                        for i, kw in enumerate([k.strip() for k in icon_kw.split(",")][:8]):
                            if icon_path := generate_svg_icon(kw, color1, color2, f"icon_{i}.svg"):
                                icons.append(icon_path)
                
                # 초청형 행사 정보 준비
                event_info_dict = None
                if edm_type == "초청형":
                    event_info_dict = {
                        'date': event_date,
                        'location': event_location,
                        'target': event_target,
                        'host': event_host
                    }
                
                # 소개형 추가 데이터 준비
                features_data = None
                layout_opt = "자동"
                if edm_type == "소개형" and hasattr(st.session_state, 'features_data'):
                    features_data = st.session_state.features_data
                    layout_opt = layout_option
                
                html_content = create_html_edm(
                    content, edm_type, company_logo_light, company_logo_dark, partner_logo, icons, cta_url, 
                    sessions if edm_type == "초청형" else None, 
                    bg_main_color, bg_image_path, event_info_dict, features_data, layout_opt, bg_svg_code
                )
                
                st.success("✅ 생성 완료!")
                st.download_button("📧 HTML 다운로드", html_content, file_name="edm_result.html", mime="text/html")
                
                # 미리보기 표시
                st.components.v1.html(html_content, height=800, scrolling=True)
        else:
            st.info("좌측에서 설정을 완료하고 'e-DM 생성' 버튼을 눌러주세요.")

if __name__ == "__main__":
    main()