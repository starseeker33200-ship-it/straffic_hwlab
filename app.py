import os
from datetime import datetime
import pandas as pd
from PIL import Image
import sqlite3
import streamlit as st

# 1. Page UI 구성 (반드시 최상단에 명시)
st.set_page_config(
    page_title="연구소 HW팀 부품 재고 관리",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------
# 🖼️ 사이드바 로고 안전 로딩
# ----------------------------------------------------
current_dir = os.getcwd()
logo_loaded = False

if os.path.exists(current_dir):
  for filename in os.listdir(current_dir):
    if filename.lower().startswith('logo'):
      full_path = os.path.join(current_dir, filename)
      try:
        img = Image.open(full_path)
        st.sidebar.image(img, use_container_width=True)
        logo_loaded = True
        break
      except Exception:
        pass

if not logo_loaded and os.path.exists(r'C:\python'):
  for filename in os.listdir(r'C:\python'):
    if filename.lower().startswith('logo'):
      try:
        img = Image.open(os.path.join(r'C:\python', filename))
        st.sidebar.image(img, use_container_width=True)
        logo_loaded = True
        break
      except Exception:
        pass

# ----------------------------------------------------
# 📌 사이드바 메뉴 및 메인 화면 구성
# ----------------------------------------------------
st.sidebar.title("📌 메뉴")
menu = st.sidebar.radio(
    "원하는 작업을 선택하세요",
    [
        "홈 (재고 현황)",
        "입/출고 등록",
        "부품 신규 등록",
        "입/출고 이력 조회",
    ],
)

# ----------------------------------------------------
# 🏠 1. 홈 (재고 현황)
# ----------------------------------------------------
if menu == "홈 (재고 현황)":
  st.title("📦 연구소 HW팀 부품 재고 현황")
  st.write("실시간 부품 재고 및 수량을 확인하는 기본 홈 화면입니다.")

  # 대시보드 요약 카드리더 예시 (Metric)
  col1, col2, col3 = st.columns(3)
  col1.metric("총 등록 부품 수", "12 종")
  col2.metric("이번 달 입고 건수", "5 건")
  col3.metric("이번 달 출고 건수", "3 건")

  st.divider()
  st.subheader("📋 전체 부품 목록")
  # 데이터베이스 연결 및 테이블 표시 로직이 들어가는 위치입니다.
  st.info(
      "사이드바 메뉴를 통해 입/출고 등록 및 부품 관리 작업을 진행할 수 있습니다."
  )

elif menu == "입/출고 등록":
  st.title("🔄 부품 입/출고 등록")
  st.write("부품 수량을 변경할 입/출고 작업을 입력해 주세요.")

elif menu == "부품 신규 등록":
  st.title("➕ 신규 부품 등록")
  st.write("새로운 HW 부품을 시스템에 등록합니다.")

elif menu == "입/출고 이력 조회":
  st.title("📜 입/출고 이력 조회")
  st.write("과거 입/출고 내역을 조회하고 Excel로 다운로드할 수 있습니다.")
