import os
import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide", page_title="제조 대시보드", page_icon="🏭")

# 💙 사이드바 하늘색 테마
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background-color: #EAF4FB;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------
# 모듈 임포트
# ----------------------
import modules.monitoring as monitoring
import modules.manual_input as manual_input  # ← 예측 페이지 모듈
import modules.mainten as mainten  # ← 유지보수 모니터링 모듈 추가

# ----------------------
# 대시보드 표지 정의
# ----------------------
def main_page():
    image_path = 'ppp.png'
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.write("이미지 파일을 찾을 수 없습니다.")

    st.markdown(
        """
        <style>
        .overlay-container {
            position: relative;
            text-align: center;
            margin-top: -920px;
            height: 0;
        }
        .overlay-text {
            position: relative;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            padding: 8px 45px;
            border-radius: 16px;
            box-shadow: 0px 3px 15px rgba(0, 0, 0, 0.4);
            display: inline-block;
        }
        .overlay-text h1 {
            font-size: 38px;
            margin-bottom: 12px;
        }
        .overlay-text h3 {
            font-size: 22px;
            margin-top: 0;
        }
        </style>
        <div class="overlay-container">
            <div class="overlay-text">
                <h1> 🏭 제조 IoT 모니터링 대시보드 📊</h1>
                <h3> 3조 팀원 : 강성민&nbsp;&nbsp;남혜지&nbsp;&nbsp;이기쁨&nbsp;&nbsp;정지원</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------------
# 메뉴 구성 (option_menu 사용)
# ----------------------
with st.sidebar:
    selected = option_menu(
        menu_title="제조 IoT 모니터링",  # 사이드 타이틀
        options=["대시보드 표지", "유지보수 필요 머신 모니터링", "실시간 머신 모니터링", "센서 입력 기반 예측"],  # 메뉴 항목
        icons=["house", "activity", "sliders", "cpu"],  # 아이콘
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "10px", "background-color": "#E3F2FD"},
            "icon": {"color": "#0D47A1", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px 0",
                "--hover-color": "#BBDEFB",
            },
            "nav-link-selected": {
                "background-color": "#2196F3",
                "color": "white",
                "font-weight": "bold",
            },
        }
    )

# ----------------------
if selected == "대시보드 표지":
    main_page()
elif selected == "실시간 머신 모니터링":
    monitoring.main()
elif selected == "센서 입력 기반 예측":
    manual_input.main()
elif selected == "유지보수 필요 머신 모니터링":
    mainten.maintenance_monitoring()  # 🔥 연결 완료

