# ----------------------------------------------------
# 🖼️ 로고 이미지 안전 로딩 (Streamlit Cloud & Local 호환)
# ----------------------------------------------------
logo_loaded = False
current_dir = os.getcwd()

# 현재 폴더 내에서 파일명이 'logo'로 시작하는 모든 이미지 탐색 (대소문자 무관)
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

# 만약 로컬 C:\python 경로에도 존재하면 보조적으로 탐색
if not logo_loaded and os.path.exists(r"C:\python"):
    for filename in os.listdir(r"C:\python"):
        if filename.lower().startswith("logo"):
            try:
                img = Image.open(os.path.join(r"C:\python", filename))
                st.image(img, width=300)
                logo_loaded = True
                break
            except Exception:
                pass
# ----------------------------------------------------
