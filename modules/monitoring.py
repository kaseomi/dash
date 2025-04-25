import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
import plotly.graph_objects as go
import os
from streamlit_autorefresh import st_autorefresh
from modules.model_loader import load_all_models

# 모델 캐싱 로드 (최상단에서 한 번만!)
failure_model, utils, rul_models, risk_model = load_all_models()

def main():
    scaler = utils['scaler']
    label_encoder = utils['label_encoder']
    sensor_cols = utils['sensor_cols']
    seq_length = utils['seq_length']
    feature_cols = sensor_cols + ['delta_minutes']

    def generate_random_sensor_sequence(seq_length=1):
        now = datetime.now()
        timestamps = [now + timedelta(seconds=i) for i in range(seq_length)]
        df = pd.DataFrame({
            'temperature': np.random.normal(75.02, 9.88, size=seq_length),
            'vibration': np.random.normal(50.00, 14.77, size=seq_length),
            'pressure': np.random.uniform(1.0, 5.0, size=seq_length),
            'humidity': np.random.uniform(30.0, 80.0, size=seq_length),
            'energy_consumption': np.random.uniform(0.5, 5.0, size=seq_length),
            'timestamp': timestamps
        })
        return df

    if 'sensor_log' not in st.session_state:
        st.session_state.sensor_log = pd.DataFrame()
    if 'maint_log' not in st.session_state:
        st.session_state.maint_log = []

    refresh_rate = st.sidebar.slider("⏱️ 새로고침 주기 (초)", 1, 10, 1)
    run = st.sidebar.toggle("▶️ 실시간 예측 시작")
    selected_machine_id = st.sidebar.selectbox("💡 머신 ID 선택", list(range(1, 51)))

    if run:
        st_autorefresh(interval=refresh_rate * 1000, key="refresh")

    new_data = generate_random_sensor_sequence(1)
    st.session_state.sensor_log = pd.concat([st.session_state.sensor_log, new_data], ignore_index=True)

    seq_df = st.session_state.sensor_log.tail(seq_length).copy()
    seq_df['timestamp'] = pd.to_datetime(seq_df['timestamp'])
    seq_df['delta_minutes'] = seq_df['timestamp'].diff().dt.total_seconds().div(60).fillna(0)
    latest = seq_df.iloc[-1][sensor_cols]
    latest_array = latest.values.reshape(1, -1)

    try:
        risk_input = latest[['temperature', 'vibration']].values.reshape(1, -1)
        downtime_risk_pred = int(risk_model.predict(risk_input)[0])
    except:
        downtime_risk_pred = None

    try:
        model_entry = rul_models[selected_machine_id]
        rul_model = model_entry['model']
        rul_scaler = model_entry.get('scaler', None)
        latest_scaled = rul_scaler.transform(latest_array) if rul_scaler else latest_array
        predicted_rul = float(rul_model.predict(latest_scaled)[0])
    except:
        predicted_rul = None

    try:
        scaled = scaler.transform(seq_df[feature_cols])
        X_input = scaled.reshape(1, seq_length, len(feature_cols))
        y_pred = failure_model.predict(X_input)
        failure_class = label_encoder.inverse_transform([np.argmax(y_pred)])[0]
    except:
        failure_class = "예측 불가"

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
            🎛️ 실시간 예측 대시보드
        </h1>
        <p style="font-size: 17px; color: #666666; margin-top: 10px;">
            센서데이터를 바탕으로 현재 상태와 잔존수명을 실시간으로 분석합니다.
        </p>
    </div>
    """, unsafe_allow_html=True
    )   

    col1, col2, col3 = st.columns(3)
    col1.metric("🔧 고장 유형", failure_class)
    col2.metric("📉 다운타임 리스크", downtime_risk_pred)
    col3.metric("🟩 RUL", f"{predicted_rul:.2f} hr" if predicted_rul else "모델 없음")

    with st.container():
        if failure_class == "예측 불가":
            st.markdown("""
            <div style="display:flex;justify-content:center;align-items:center;background-color:#FFFBEA;padding:15px;border-radius:10px;font-size:18px;font-weight:500;color:#665c00;width:100%;">
            📍 데이터가 부족합니다. 유지보수 상태를 판단할 수 없습니다.
            </div>
            """, unsafe_allow_html=True)
        elif isinstance(predicted_rul, (int, float)) and (predicted_rul <= 20 or downtime_risk_pred == 1 or failure_class != "Normal"):
            st.markdown("""
            <div style="display:flex;justify-content:center;align-items:center;background-color:#F8D7DA;padding:15px;border-radius:10px;font-size:18px;font-weight:500;color:#842029;width:100%;">
            ⚠️ 유지보수가 필요합니다!
            </div>
            """, unsafe_allow_html=True)
            st.session_state.maint_log.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "failure_class": failure_class,
                "risk": downtime_risk_pred,
                "rul": predicted_rul
            })
        else:
            st.markdown("""
            <div style="display:flex;justify-content:center;align-items:center;background-color:#D1E7DD;padding:15px;border-radius:10px;font-size:18px;font-weight:500;color:#0f5132;width:100%;">
            ✅ 정상 작동 중입니다.
            </div>
            """, unsafe_allow_html=True)

    sensor_latest = seq_df.iloc[-1]
    st.subheader("📟 센서 상태")
    gauge_cols = st.columns(5)
    for col, metric, title, minv, maxv in zip(
        gauge_cols,
        ["temperature", "vibration", "pressure", "humidity", "energy_consumption"],
        ["🌡️ 온도 (°C)", "🎷 진동 (Hz)", "💨 압력 (Bar)", "💧 습도 (%)", "⚡ 에너지 (kWh)"],
        [50, 0, 1, 30, 0.5],
        [100, 100, 5, 90, 5]
    ):
        val = float(sensor_latest[metric])
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            gauge={
                'axis': {'range': [minv, maxv]},
                'bar': {'color': "royalblue"},
                'bgcolor': "white",
                'steps': [
                    {'range': [minv, (minv+maxv)/2], 'color': '#cce5ff'},
                    {'range': [(minv+maxv)/2, maxv], 'color': '#99ccff'}
                ]
            },
            title={'text': title, 'font': {'size': 16}}
        ))
        fig.update_layout(paper_bgcolor="#E6F0FA", height=250, margin=dict(t=10, b=10, l=10, r=10))
        col.plotly_chart(fig, use_container_width=True)

    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🔐 최근 유지보수 필요 기록 (최근 5개)")
        maint_df = pd.DataFrame(st.session_state.maint_log[-5:])
        if not maint_df.empty:
            st.dataframe(maint_df, use_container_width=True)
    with col2:
        st.subheader("📊 최근 고장 유형 비율")
        try:
            pie_df = pd.DataFrame(st.session_state.maint_log)["failure_class"].value_counts().reset_index()
            pie_df.columns = ["Failure Type", "Count"]
            fig = go.Figure(data=[go.Pie(
                labels=pie_df["Failure Type"],
                values=pie_df["Count"],
                hole=0.5,
                textinfo='label+percent',
                textposition='inside',
                insidetextorientation='horizontal',
                marker=dict(colors=['#cce5ff','#d4edda','#f8d7da','#ffeeba'])
            )])
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.markdown("""
            <div style="display:flex;justify-content:center;align-items:center;background-color:#FFFBEA;padding:20px;border-radius:10px;font-size:18px;font-weight:500;color:#665c00;width:100%;">
            아직 고장 데이터가 부족합니다.
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📈 실시간 센서 시계열 그래프")
    st.line_chart(seq_df.set_index('timestamp')[sensor_cols].tail(20))

