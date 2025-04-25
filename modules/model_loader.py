# modules/model_loader.py

import pickle
import os
import streamlit as st
from tensorflow.keras.models import load_model

# 모델 파일 경로 정의
BASE_DIR = os.path.dirname(__file__)
PKL_PATH = os.path.join(BASE_DIR, "model_utils.pkl")
H5_PATH = os.path.join(BASE_DIR, "failure_prediction_model.h5")
RUL_PATH = os.path.join(BASE_DIR, "random_forest_regressors_by_machine.pkl")
RISK_PATH = os.path.join(BASE_DIR, "downtime_risk_model.pkl")

@st.cache_resource
def load_utils():
    with open(PKL_PATH, "rb") as f:
        return pickle.load(f)

@st.cache_resource
def load_failure_model():
    return load_model(H5_PATH)

@st.cache_resource
def load_rul_model():
    with open(RUL_PATH, "rb") as f:
        return pickle.load(f)

@st.cache_resource
def load_risk_model():
    with open(RISK_PATH, "rb") as f:
        return pickle.load(f)

def load_all_models():
    return (
        load_failure_model(),
        load_utils(),
        load_rul_model(),
        load_risk_model()
    )
