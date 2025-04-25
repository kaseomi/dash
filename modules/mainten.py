import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.express as px
from modules.model_loader import load_all_models  # ✅ 캐시된 모델 로드

# ✅ 모델 불러오기
failure_model, utils, rul_models, risk_model = load_all_models()
sensor_cols = utils["sensor_cols"]
feature_cols = sensor_cols + ["delta_minutes"]
seq_length = utils["seq_length"]
scaler = utils["scaler"]
label_encoder = utils["label_encoder"]

# ✅ 랜덤 센서 생성 함수
def generate_random_sensor():
    return {
        'temperature': np.random.normal(75, 10),
        'vibration': np.random.normal(50, 15),
        'pressure': np.random.uniform(1, 5),
        'humidity': np.random.uniform(30, 80),
        'energy_consumption': np.random.uniform(0.5, 5),
        'delta_minutes': 1.0
    }

# ✅ 머신 전체 평가 함수
def evaluate_all_machines():
    result = []
    all_ready = True
    for mid in range(1, 51):
        seq = st.session_state.machine_sequences[mid]
        seq.append(generate_random_sensor())
        if len(seq) > seq_length:
            seq.pop(0)
        row_latest = seq[-1]
        df_latest = pd.DataFrame([row_latest])
        rul_model_entry = rul_models[mid]
        X_rul = df_latest[sensor_cols].values
        if rul_model_entry.get("scaler"):
            X_rul = rul_model_entry["scaler"].transform(X_rul)
        rul_pred = float(rul_model_entry["model"].predict(X_rul)[0])
        risk_input = df_latest[["temperature", "vibration"]].values
        risk_pred = int(risk_model.predict(risk_input)[0])
        if len(seq) == seq_length:
            df_seq = pd.DataFrame(seq)
            scaled_seq = scaler.transform(df_seq[feature_cols])
            X_seq = scaled_seq.reshape(1, seq_length, len(feature_cols))
            y_pred = failure_model.predict(X_seq)
            failure_class = label_encoder.inverse_transform([np.argmax(y_pred)])[0]
        else:
            failure_class = "예측 불가"
            all_ready = False
        maintenance_required = (
            (len(seq) == seq_length) and (
                (rul_pred <= 20) or
                (risk_pred == 1) or
                (failure_class != "Normal")
            )
        )
        result.append({
            "machine_id": mid,
            "predicted_rul": rul_pred,
            "downtime_risk": risk_pred,
            "failure_type": failure_class,
            "maintenance_required": maintenance_required,
            **row_latest
        })
    return pd.DataFrame(result), all_ready

# ✅ 메인 대시보드 함수
def maintenance_monitoring():
    st.markdown("""
        <style>
        .main-title { font-size: 30px; font-weight: 600; text-align: center; padding: 15px; margin-bottom: 10px; }
        .subtext { font-size: 16px; color: gray; text-align: center; margin-bottom: 20px; }
        .warn-box {
            background-color: #fff3cd; color: #856404; padding: 12px 20px;
            border-radius: 12px; border: 1px solid #ffeeba; margin: 20px 0; text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
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
            📈 실시간 유지보수 예측 대시보드
        </h1>
        <p style="font-size: 17px; color: #666666; margin-top: 10px;">
            센서 기반 실시간 예측을 통해 유지보수 필요 여부를 분석합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 초기화 및 설정
    if st.sidebar.button("🔄 시퀀스 초기화"):
        st.session_state.machine_sequences = {mid: [] for mid in range(1, 51)}
    if 'machine_sequences' not in st.session_state:
        st.session_state.machine_sequences = {mid: [] for mid in range(1, 51)}

    refresh_rate = st.sidebar.slider("⏱ 새로고침 주기 (초)", 5, 10, 5)
    run = st.sidebar.toggle("▶ 실시간 감시 시작")
    placeholder = st.empty()

    while run:
        start_time = time.time()
        timestamp_key = datetime.now().strftime("%Y%m%d%H%M%S%f")
        df, all_ready = evaluate_all_machines()
        filtered = df[df["maintenance_required"]].reset_index(drop=True)

        with placeholder.container():
            now_time = datetime.now().strftime('%H:%M:%S')
            st.markdown(f"<p class='subtext'>⏰ 예측 시각: {now_time}</p>", unsafe_allow_html=True)

            colA, colB, colC = st.columns(3)
            colA.metric("🧯 유지보수 필요 머신 수", len(filtered))
            colB.metric("🛠 전체 머신 수", len(df))
            avg_rul = round(df['predicted_rul'].mean(), 1) if not df.empty else "-"
            colC.metric("⏳ 평균 잔존수명", f"{avg_rul} hr")

            if not all_ready:
                st.markdown("""
                <div class='warn-box'>
                📍 데이터가 부족합니다. 유지보수 상태를 판단할 수 없습니다.
                </div>
                """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                fig = px.pie(df, names="downtime_risk", title="💥 다운타임 리스크 비율", hole=0.4)
                fig.update_traces(textinfo='label+percent')
                st.plotly_chart(fig, use_container_width=True, key=f"pie_risk_{timestamp_key}")
            with col2:
                fig = px.line(df.sort_values("machine_id"), x="machine_id", y="predicted_rul",
                              title="📉 잔존수명 분포", markers=True)
                st.plotly_chart(fig, use_container_width=True, key=f"line_rul_{timestamp_key}")
            with col3:
                failure_df = df["failure_type"].value_counts().reset_index()
                failure_df.columns = ["failure_type", "count"]
                fig = px.bar(
                    failure_df,
                    x="failure_type",
                    y="count",
                    labels={"failure_type": "고장유형", "count": "수량"},
                    title="🔧 고장 유형 분포"
                )
                st.plotly_chart(fig, use_container_width=True, key=f"bar_failure_{timestamp_key}")
            with col4:
                pie_df = pd.DataFrame({
                    "status": ["정상", "유지보수 필요"],
                    "count": [len(df) - len(filtered), len(filtered)]
                })
                fig = px.pie(pie_df, names="status", values="count", title="🧭 유지보수 비율", hole=0.4)
                fig.update_traces(textinfo='label+percent')
                st.plotly_chart(fig, use_container_width=True, key=f"pie_maint_{timestamp_key}")

            st.divider()
            st.markdown("### 📋 유지보수 대상 머신 목록")
            st.dataframe(
                filtered[["machine_id", "failure_type", "predicted_rul", "downtime_risk"] + sensor_cols]
                .style.hide(axis='index'),
                use_container_width=True
            )

        elapsed = time.time() - start_time
        time.sleep(max(0, refresh_rate - elapsed))
