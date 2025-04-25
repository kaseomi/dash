import streamlit as st
import pandas as pd
import numpy as np
from modules.model_loader import load_all_models  # ✅ 캐시된 모델 로드
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

# ✅ 모델 로드 (캐시된 버전)
failure_model, utils, rul_models, risk_model = load_all_models()
sensor_cols = utils["sensor_cols"]

def main():
    # ✅ 상단 설명 박스
    st.markdown(
    """
    <div style="
        background-color: #ffffff;
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
        text-align: center;
        margin-bottom: 10px;
    ">
        <h1 style="font-size: 35px; font-weight: 500; margin: 0;">
            ⚙️ 센서 입력 기반 예측 대시보드
        </h1>
        <p style="font-size: 17px; color: #666666; margin-top: 10px;">
            센서 값을 수동으로 입력해 다운타임 리스크와 잔존수명을 예측합니다.
        </p>
    </div>
    """, unsafe_allow_html=True
    )   

    # ✅ 입력값 설정
    st.markdown("""
    <div style='font-size:20px;margin-top:-10px;'>
        <strong>🧪 입력값 설정</strong>
    </div><br>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            machine_id = st.selectbox("🔧 머신 ID", list(rul_models.keys()), index=0)
        with col2:
            col21, col22, col23 = st.columns(3)
            with col21:
                temperature = st.slider("🌡️ 온도 (°C)", 40.0, 120.0, 75.0)
                pressure = st.slider("💨 압력 (Bar)", 0.5, 10.0, 3.0)
            with col22:
                vibration = st.slider("🎛️ 진동 (Hz)", 0.0, 100.0, 50.0)
                humidity = st.slider("💧 습도 (%)", 10.0, 100.0, 60.0)
            with col23:
                energy = st.slider("⚡ 에너지 (kWh)", 0.0, 10.0, 2.5)

    st.markdown("""<br><hr style='margin:20px 0'>""", unsafe_allow_html=True)

    # ✅ 예측 실행
    if st.button("🔍 예측 실행"):
        input_df = pd.DataFrame([{
            "temperature": temperature,
            "vibration": vibration,
            "pressure": pressure,
            "humidity": humidity,
            "energy_consumption": energy
        }])

        # 예측
        risk_input = input_df[["temperature", "vibration"]]
        risk_pred = int(risk_model.predict(risk_input)[0])

        rul_model_entry = rul_models[machine_id]
        rul_model = rul_model_entry["model"]
        rul_scaler = rul_model_entry.get("scaler", None)
        X_rul = input_df[sensor_cols].values
        if rul_scaler:
            X_rul = rul_scaler.transform(X_rul)
        rul_pred = float(rul_model.predict(X_rul)[0])

        # ✅ 예측 결과 텍스트
        st.markdown("""
        <div style='font-size:20px;margin-top:10px;'>
            <strong>📈 예측 결과</strong>
        </div><br>
        """, unsafe_allow_html=True)

        # ✅ 예측 값 출력 (디자인 적용됨)
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: flex-start;'>
                <div style='font-size:14px; font-weight:600; color:#444;'>📉 다운타임 리스크</div>
                <div style='font-size:32px; font-weight:500; color:#212529; margin-top:4px;'>{risk_pred}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: flex-start;'>
                <div style='font-size:14px; font-weight:600; color:#444;'>🛢️ 잔존수명 (RUL)</div>
                <div style='font-size:32px; font-weight:500; color:#212529; margin-top:4px;'>{rul_pred:.2f} hr</div>
            </div>
            """, unsafe_allow_html=True)

        # ✅ 상태 메시지 (깔끔한 스타일)
        if rul_pred <= 20 or risk_pred == 1:
            st.markdown("""
            <div style="display:flex;justify-content:center;align-items:center;background-color:#F8D7DA;padding:15px;border-radius:10px;font-size:18px;font-weight:500;color:#842029;width:100%;">
            ⚠️ 유지보수가 필요합니다!
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex;justify-content:center;align-items:center;background-color:#D1E7DD;padding:15px;border-radius:10px;font-size:18px;font-weight:500;color:#0f5132;width:100%;">
            ✅ 정상 작동 중입니다.
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
