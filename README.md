# 📧 CAMPER - e-DM Generator

AI 기반 이메일 마케팅 템플릿 생성기

## 🚀 주요 기능

- **초청형/소개형** 두 가지 e-DM 유형 지원
- **AI 기반 콘텐츠 생성** (OpenAI GPT-4)
- **다양한 파일 형식 지원** (PDF, PPTX, DOCX, 이미지)
- **웹페이지 URL 분석** 및 자동 요약
- **커스텀 디자인** (색상, 배경, 로고)
- **반응형 HTML** 이메일 템플릿 생성

## 📋 요구사항

- Python 3.8+
- OpenAI API 키
- Tesseract OCR (이미지 텍스트 추출용)

## 🛠️ 설치 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd camper-edm-generator
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. Tesseract OCR 설치 (선택사항)
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt install tesseract-ocr`

4. OpenAI API 키 설정
`.streamlit/secrets.toml` 파일 생성:
```toml
[openai]
api_key = "your-openai-api-key-here"
```

## 🎯 사용 방법

1. 애플리케이션 실행
```bash
streamlit run test_0703_1624.py
```

2. 브라우저에서 `http://localhost:8501` 접속

3. 좌측 패널에서 설정:
   - 솔루션 소개 자료 업로드 (선택)
   - e-DM 유형 선택 (초청형/소개형)
   - 핵심 메시지 입력
   - 디자인 설정
   - 로고 업로드

4. "e-DM 생성" 버튼 클릭

5. 우측에서 미리보기 확인 후 HTML 다운로드

## 📁 프로젝트 구조

```
camper-edm-generator/
├── test_0703_1624.py    # 메인 애플리케이션
├── requirements.txt     # Python 의존성
├── README.md           # 프로젝트 문서
├── .streamlit/         # Streamlit 설정
│   └── secrets.toml    # API 키 설정
└── images/             # 생성된 이미지 저장소
```

## 🔧 주요 함수

- `extract_text_from_*()`: 다양한 파일 형식에서 텍스트 추출
- `summarize_content()`: AI 기반 콘텐츠 요약
- `generate_svg_icon()`: SVG 아이콘 생성
- `create_html_edm()`: HTML 이메일 템플릿 생성

## ⚠️ 주의사항

- OpenAI API 사용량에 따른 비용 발생
- 이미지 OCR 기능은 Tesseract 설치 필요
- 생성된 HTML은 이메일 클라이언트 호환성 테스트 권장

## 📄 라이선스

MIT License

## 🤝 기여

이슈 리포트 및 풀 리퀘스트 환영합니다.