import streamlit as st
import sqlite3
import pandas as pd
import os  # <--- 이 줄이 빠져있어서 에러가 발생한 것입니다!
from datetime import datetime
from PIL import Image

# 1. Page UI 구성 (사이드바 기본 펼침 설정)
st.set_page_config(
    page_title="연구소 HW팀 부품 재고 관리", 
    page_icon="📦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 🖼️ 로고 이미지 안전 로딩
# ----------------------------------------------------
logo_loaded = False
current_dir = os.getcwd()

if os.path.exists(current_dir):
    for filename in os.listdir(current_dir):
        if filename.lower().startswith("logo"):
            full_path = os.path.join(current_dir, filename)
            try:
                img = Image.open(full_path)
                st.image(img, width=300)
                logo_loaded = True
                break
            except Exception:
                pass
