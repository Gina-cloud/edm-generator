def main():
    st.markdown("""
    <div class="main-header">
        <h1>📧 AI 기반 e-DM Generator</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # 2열 레이아웃
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-header"><h2>📝 콘텐츠 입력</h2></div>', unsafe_allow_html=True)
        
        # 1. EDM 기본 설정
        with st.expander("⚙️ **1단계: EDM 기본 설정**", expanded=True):
            edm_type = st.radio("EDM 유형", ["초청형", "소개형"])
            core = st.text_area("핵심 메시지 (필수)", placeholder="예: 차세대 ERP 솔루션으로 디지털 전환을 가속화하세요")
            title_suggestion = st.text_input("타이틀 제안 (선택)", placeholder="AI가 25자 이내로 최적화합니다")
            target = st.text_input("타겟 고객", placeholder="예: IT관리자, CTO, 제조업 담당자")
        
        # 2. 솔루션 소개 자료
        with st.expander("📄 **2단계: 솔루션 소개 자료**", expanded=True):
            st.markdown("**🌐 웹페이지 URL**")
            url_input = st.text_input("웹페이지 URL", placeholder="https://www.woongjin.com")
            
            st.markdown("**📁 파일 업로드**")
            uploaded_file = st.file_uploader("파일 선택", type=["pdf", "pptx", "docx", "jpg", "png"])
        
        # 3. 솔루션 소개
        if edm_type == "초청형":
            with st.expander("📅 **3단계: 행사 세부 정보**", expanded=True):
                invitation_text = st.text_area("초청의 글", placeholder="행사 목적, 주요 내용을 작성해주세요")
        else:
            with st.expander("🛠️ **3단계: 솔루션 소개**", expanded=True):
                st.markdown('<div class="step-subtitle">📋 제품/서비스 설명</div>', unsafe_allow_html=True)
                desc = st.text_area("제품/서비스 설명", placeholder="제품의 주요 특징과 장점을 설명해주세요")
                
                st.markdown('<div class="step-subtitle">🔧 주요 기능</div>', unsafe_allow_html=True)
                # 기능 입력 UI
                
                st.markdown('<div class="step-subtitle">📈 기대효과</div>', unsafe_allow_html=True)
                expected_effects = st.text_area("기대효과 설명", placeholder="예:\n재고 관리 효율화\n운영비용 절감\n실시간 모니터링 가능")
        
        # 4. 디자인 설정
        with st.expander("🎨 **4단계: 디자인 설정**", expanded=True):
            bg_main_color = st.color_picker("메인 컬러", "#354F9B")
        
        # 5. 로고 설정
        with st.expander("🏷️ **5단계: 로고 설정**", expanded=True):
            st.markdown("**회사 로고 (웅진IT 기본 설정)**")
            st.info("✅ 웅진IT 로고가 자동으로 설정되어 배경에 따라 최적의 로고가 선택됩니다.")
        
        # 6. Footer 설정
        with st.expander("📄 **6단계: Footer 설정**", expanded=True):
            use_custom_footer = st.checkbox("커스텀 Footer 사용")
        
        # 생성 버튼
        st.markdown("---")
        generate_btn = st.button("🚀 AI EDM 생성하기", use_container_width=True, type="primary")
    
    with col2:
        st.markdown('<div class="section-header"><h2>👀 EDM 미리보기</h2></div>', unsafe_allow_html=True)
        st.info("📝 좌측에서 EDM을 생성하면 여기에 미리보기가 표시됩니다.")

if __name__ == "__main__":
    main()