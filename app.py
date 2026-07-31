import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import urllib.request
import io

# 1. Page UI 구성 (사이드바 기본 펼침 설정)
st.set_page_config(
    page_title="연구소 HW팀 부품 재고 관리 시스템", 
    page_icon="🧊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 💎 고급스러운 모던 커스텀 CSS 스타일링
# ----------------------------------------------------
st.markdown("""
<style>
    /* 메인 배경 및 기본 폰트 설정 */
    .main {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* 상단 통합 브랜드 헤더 (타이틀 전용) */
    .brand-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .brand-subtitle {
        font-size: 0.95rem;
        color: #64748B;
        margin-top: 0.2rem;
    }

    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    [data-testid="stSidebar"] * {
        color: #F1F5F9 !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 600;
        font-size: 0.9rem;
        color: #94A3B8 !important;
        margin-bottom: 0.5rem;
    }
    
    /* 고급스러운 카드 컨테이너 스타일 */
    .content-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .card-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 1rem;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 0.5rem;
    }

    /* 버튼 스타일 커스텀 */
    .stButton>button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button[kind="primary"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }

    /* 데이터프레임 테두리 라운딩 */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
    }

    /* 구분선 정돈 */
    hr {
        margin: 1.5rem 0 !important;
        border-color: #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

# DB 설정 및 테이블 초기화
DB_FILE = "inventory.db"
ADMIN_PASSWORD = "admin" # 관리자 비밀번호

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            safety_stock INTEGER DEFAULT 5,
            datasheet_url TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL,
            user_name TEXT NOT NULL,
            trans_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

init_db()

# ----------------------------------------------------
# 🖼️ 사이드바 전용 로고 이미지 안전 로딩
# ----------------------------------------------------
GITHUB_LOGO_URL = "https://raw.githubusercontent.com/USER_NAME/REPO_NAME/main/logo.jpg"
IMAGE_DIR = r"C:\python"

sidebar_logo_img = None

# 1. 로컬 C:\python 디렉토리 검색
if os.path.exists(IMAGE_DIR):
    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().startswith("logo"):
            full_path = os.path.join(IMAGE_DIR, filename)
            try:
                sidebar_logo_img = Image.open(full_path)
                break
            except Exception:
                pass

# 2. 상대 경로 logo.jpg 검색
if sidebar_logo_img is None and os.path.exists("logo.jpg"):
    try:
        sidebar_logo_img = Image.open("logo.jpg")
    except Exception:
        pass

# 3. GitHub URL 로딩
if sidebar_logo_img is None:
    try:
        req = urllib.request.Request(
            GITHUB_LOGO_URL, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            image_data = response.read()
            sidebar_logo_img = Image.open(io.BytesIO(image_data))
    except Exception:
        pass

# 사이드바에만 로고 표시
if sidebar_logo_img:
    st.sidebar.image(sidebar_logo_img, use_container_width=True)

# ----------------------------------------------------
# 🏛️ 상단 브랜드 헤더 (타이틀)
# ----------------------------------------------------
st.markdown("""
<div style="padding: 0.5rem 0 1rem 0;">
    <div class="brand-title">HARDWARE R&D INVENTORY SYSTEM</div>
    <div class="brand-subtitle">연구소 HW팀 부품 통합 재고 추적 및 수량 관리 플랫폼</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 0px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# 세션 상태 초기화
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if "modal_msg" not in st.session_state:
    st.session_state["modal_msg"] = None

@st.dialog("알림 - 처리 완료")
def show_confirm_modal(message):
    st.success(message)
    st.write("요청하신 데이터 변경 작업이 성공적으로 저장되었습니다.")
    if st.button("확인", type="primary", use_container_width=True):
        st.session_state["modal_msg"] = None
        st.rerun()

if st.session_state["modal_msg"]:
    show_confirm_modal(st.session_state["modal_msg"])

CATEGORY_LIST = [
    "저항 (Resistors)", 
    "커패시터 (Capacitors)", 
    "인덕터/비드 (Inductors/Beads)",
    "Power/Analog IC", 
    "MCU/Processor", 
    "트랜지스터/MOSFET (FET/BJT)",
    "다이오드/LED (Diodes/LEDs)",
    "스위치/버튼 (Switches/Buttons)",
    "퓨즈/보호소자 (Fuses/TVS)",
    "커넥터/케이블 (Connectors/Cables)", 
    "모듈/기판 (Modules)", 
    "기구/기타 (Hardware)"
]

# ----------------------------------------------------
# 사이드바 메뉴
# ----------------------------------------------------
st.sidebar.markdown("### NAVIGATION")
menu = st.sidebar.radio(
    "메뉴 선택", 
    ["부품 검색 및 출고 처리", "부품 신규 등록 및 수정", "입출고 히스토리 조회"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### SYSTEM AUTHENTICATION")

if st.session_state["is_admin"]:
    st.sidebar.success("관리자 권한 활성화됨")
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state["is_admin"] = False
        st.rerun()
else:
    with st.sidebar.form("sidebar_login"):
        pwd_input = st.text_input("관리자 비밀번호", type="password", placeholder="비밀번호 입력")
        login_btn = st.form_submit_button("인증하기", use_container_width=True)
        if login_btn:
            if pwd_input == ADMIN_PASSWORD:
                st.session_state["is_admin"] = True
                st.success("인증에 성공했습니다.")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")

# ----------------------------------------------------
# 1. 부품 검색 및 출고 처리
# ----------------------------------------------------
if menu == "부품 검색 및 출고 처리":
    conn = get_connection()
    df_components = pd.read_sql_query("SELECT * FROM components", conn)
    conn.close()

    # 상단 요약 메트릭 카드
    m1, m2, m3 = st.columns(3)
    total_items = len(df_components)
    total_qty = df_components["quantity"].sum() if not df_components.empty else 0
    low_stock = len(df_components[df_components["quantity"] <= df_components["safety_stock"]]) if not df_components.empty else 0

    m1.metric("등록 총 부품 수", f"{total_items:,} 종")
    m2.metric("전체 재고 보유 수량", f"{total_qty:,} 개")
    m3.metric("안전재고 미달 품목", f"{low_stock:,} 종", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # 부품 현황 데이터 테이블 카드
    st.markdown('<div class="content-card"><div class="card-title">부품 재고 현황 및 검색</div>', unsafe_allow_html=True)
    
    c_search, c_cat = st.columns([3, 1])
    with c_search:
        search_query = st.text_input("검색어 (Part Number, 사양, 보관 위치)", placeholder="검색할 키워드를 입력하세요...")
    with c_cat:
        categories = ["전체 카테고리"] + (df_components["category"].unique().tolist() if not df_components.empty else [])
        selected_category = st.selectbox("카테고리 필터", categories)
        
    filtered_df = df_components.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df["part_number"].str.contains(search_query, case=False, na=False) |
            filtered_df["description"].str.contains(search_query, case=False, na=False) |
            filtered_df["location"].str.contains(search_query, case=False, na=False)
        ]
    if selected_category != "전체 카테고리":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]
        
    if filtered_df.empty:
        st.info("조회된 부품 데이터가 없습니다.")
    else:
        st.dataframe(
            filtered_df.rename(columns={
                "part_number": "파트 넘버 (P/N)",
                "category": "카테고리",
                "description": "설명/사양",
                "location": "보관 위치",
                "quantity": "현재 수량",
                "safety_stock": "안전 재고",
                "datasheet_url": "데이터시트"
            })[["파트 넘버 (P/N)", "카테고리", "보관 위치", "현재 수량", "안전 재고", "설명/사양", "데이터시트"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "데이터시트": st.column_config.LinkColumn(
                    label="데이터시트",
                    display_text="문서 열기"
                )
            }
        )
        
        # 관리자 빠른 수정
        with st.expander("선택 부품 정보 빠른 수정 (관리자 전용)"):
            if not st.session_state["is_admin"]:
                st.warning("관리자 로그인 후 수정이 가능합니다.")
            else:
                edit_pn_list = filtered_df["part_number"].tolist()
                selected_edit_pn = st.selectbox("수정할 부품 선택", edit_pn_list, key="quick_edit_sel")
                
                target_row = filtered_df[filtered_df["part_number"] == selected_edit_pn].iloc[0]
                cat_index = CATEGORY_LIST.index(target_row["category"]) if target_row["category"] in CATEGORY_LIST else 0
                
                with st.form("quick_edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_part_number = st.text_input("파트 넘버 (P/N)", value=target_row["part_number"])
                        e_category = st.selectbox("카테고리", CATEGORY_LIST, index=cat_index)
                        e_location = st.text_input("보관 위치", value=target_row["location"])
                    
                    with col2:
                        e_quantity = st.number_input("현재 재고 수량", min_value=0, value=int(target_row["quantity"]))
                        e_safety_stock = st.number_input("안전 재고 수량", min_value=0, value=int(target_row["safety_stock"]))
                        e_datasheet_url = st.text_input("데이터시트 URL", value=target_row["datasheet_url"] if target_row["datasheet_url"] else "")
                        
                    e_description = st.text_area("부품 사양 상세", value=target_row["description"] if target_row["description"] else "")
                    
                    quick_edit_submit = st.form_submit_button("변경 사항 저장", type="primary")
                    
                    if quick_edit_submit:
                        conn = get_connection()
                        c = conn.cursor()
                        try:
                            c.execute("""
                                UPDATE components 
                                SET part_number = ?, category = ?, description = ?, location = ?, quantity = ?, safety_stock = ?, datasheet_url = ?
                                WHERE id = ?
                            """, (e_part_number.strip(), e_category, e_description, e_location.strip(), e_quantity, e_safety_stock, e_datasheet_url, int(target_row["id"])))
                            
                            conn.commit()
                            conn.close()
                            
                            st.session_state["modal_msg"] = f"부품 [{e_part_number}] 데이터 수정이 완료되었습니다."
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("동일한 이름의 파트 넘버가 이미 등록되어 있습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    # 빠른 출고/입고 카드
    st.markdown('<div class="content-card"><div class="card-title">실시간 입출고 반영</div>', unsafe_allow_html=True)
    if not df_components.empty:
        part_list = df_components["part_number"].tolist()
        
        with st.form("checkout_form"):
            col_p, col_u, col_q, col_t = st.columns([2.5, 1.5, 1, 1])
            with col_p:
                selected_pn = st.selectbox("대상 부품 선택 (P/N)", part_list)
            with col_u:
                user_name = st.text_input("작업자 성명", placeholder="홍길동")
            with col_q:
                trans_qty = st.number_input("수량", min_value=1, value=1, step=1)
            with col_t:
                trans_type = st.radio("구분", ["출고 (-)", "입고 (+)"])
                
            note = st.text_input("사유 / 프로젝트명", placeholder="예: 시제품 검증용 PCB 실장")
            submit_btn = st.form_submit_button("입출고 트랜잭션 실행", type="primary", use_container_width=True)
            
            if submit_btn:
                if not user_name.strip():
                    st.error("작업자 성명을 반드시 입력해야 합니다.")
                else:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("SELECT quantity FROM components WHERE part_number = ?", (selected_pn,))
                    current_qty = c.fetchone()[0]
                    
                    is_checkout = "출고" in trans_type
                    change_qty = -trans_qty if is_checkout else trans_qty
                    new_qty = current_qty + change_qty
                    
                    if is_checkout and current_qty < trans_qty:
                        st.error(f"재고가 부족합니다. (현재 재고 수량: {current_qty}개)")
                    else:
                        c.execute("UPDATE components SET quantity = ? WHERE part_number = ?", (new_qty, selected_pn))
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("""
                            INSERT INTO transactions (part_number, user_name, trans_type, quantity, timestamp, note)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (selected_pn, user_name, "CHECK_OUT" if is_checkout else "CHECK_IN", trans_qty, now_str, note))
                        
                        conn.commit()
                        conn.close()
                        
                        st.session_state["modal_msg"] = f"[{selected_pn}] {trans_type} {trans_qty}개가 반영되었습니다. (최종 재고: {new_qty}개)"
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 부품 신규 등록 및 수정
# ----------------------------------------------------
elif menu == "부품 신규 등록 및 수정":
    if not st.session_state["is_admin"]:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.warning("해당 메뉴는 관리자 권한이 필요합니다. 사이드바에서 비밀번호 인증을 완료해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        reg_tab, edit_tab, excel_tab = st.tabs([
            "개별 신규 등록", 
            "기존 데이터 수정 및 삭제", 
            "대량 등록 (엑셀/CSV)"
        ])
        
        # 1) 개별 등록
        with reg_tab:
            st.markdown('<div class="content-card"><div class="card-title">신규 부품 마스터 등록</div>', unsafe_allow_html=True)
            with st.form("register_form"):
                col1, col2 = st.columns(2)
                with col1:
                    part_number = st.text_input("파트 넘버 (P/N) *", placeholder="예: RC0603FR-0710KL")
                    category = st.selectbox("카테고리 *", CATEGORY_LIST)
                    location = st.text_input("보관 위치 *", placeholder="예: Rack A-01")
                
                with col2:
                    init_quantity = st.number_input("초기 입고 수량 *", min_value=0, value=100, step=10)
                    safety_stock = st.number_input("안전 재고 수량", min_value=0, value=10, step=5)
                    datasheet_url = st.text_input("데이터시트 URL", placeholder="https://...")
                    
                description = st.text_area("부품 상세 사양 / 비고")
                reg_submit = st.form_submit_button("신규 등록 실행", type="primary", use_container_width=True)
                
                if reg_submit:
                    if not part_number.strip() or not location.strip():
                        st.error("파트 넘버와 보관 위치는 필수 입력 항목입니다.")
                    else:
                        try:
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO components (part_number, category, description, location, quantity, safety_stock, datasheet_url)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (part_number.strip(), category, description, location.strip(), init_quantity, safety_stock, datasheet_url))
                            
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("""
                                INSERT INTO transactions (part_number, user_name, trans_type, quantity, timestamp, note)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (part_number.strip(), "ADMIN", "CHECK_IN", init_quantity, now_str, "최초 재고 등록"))
                            
                            conn.commit()
                            conn.close()
                            
                            st.session_state["modal_msg"] = f"신규 부품 [{part_number}]이 등록되었습니다."
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"이미 존재하는 파트 넘버입니다: {part_number}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 2) 개별 수정 및 삭제
        with edit_tab:
            st.markdown('<div class="content-card"><div class="card-title">등록 부품 변경 및 완전 삭제</div>', unsafe_allow_html=True)
            conn = get_connection()
            df_comp = pd.read_sql_query("SELECT * FROM components", conn)
            conn.close()
            
            if df_comp.empty:
                st.info("등록된 부품 데이터가 없습니다.")
            else:
                p_list = df_comp["part_number"].tolist()
                selected_edit_pn = st.selectbox("대상 부품 선택 (P/N)", p_list, key="tab_edit_sel")
                target_row = df_comp[df_comp["part_number"] == selected_edit_pn].iloc[0]
                cat_index = CATEGORY_LIST.index(target_row["category"]) if target_row["category"] in CATEGORY_LIST else 0
                
                with st.form("edit_component_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_part_number = st.text_input("파트 넘버 (P/N)", value=target_row["part_number"])
                        e_category = st.selectbox("카테고리", CATEGORY_LIST, index=cat_index)
                        e_location = st.text_input("보관 위치", value=target_row["location"])
                    
                    with col2:
                        e_quantity = st.number_input("현재 재고 수량", min_value=0, value=int(target_row["quantity"]))
                        e_safety_stock = st.number_input("안전 재고 수량", min_value=0, value=int(target_row["safety_stock"]))
                        e_datasheet_url = st.text_input("데이터시트 URL", value=target_row["datasheet_url"] if target_row["datasheet_url"] else "")
                        
                    e_description = st.text_area("부품 상세 사양", value=target_row["description"] if target_row["description"] else "")
                    
                    edit_submit = st.form_submit_button("수정 데이터 저장", type="primary")
                    
                    if edit_submit:
                        conn = get_connection()
                        c = conn.cursor()
                        try:
                            c.execute("""
                                UPDATE components 
                                SET part_number = ?, category = ?, description = ?, location = ?, quantity = ?, safety_stock = ?, datasheet_url = ?
                                WHERE id = ?
                            """, (e_part_number.strip(), e_category, e_description, e_location.strip(), e_quantity, e_safety_stock, e_datasheet_url, int(target_row["id"])))
                            conn.commit()
                            conn.close()
                            
                            st.session_state["modal_msg"] = f"부품 [{e_part_number}] 정보가 성공적으로 수정되었습니다."
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("동일한 이름의 파트 넘버가 존재합니다.")

                # 완전 삭제 영역
                st.divider()
                st.markdown("##### 부품 완전 삭제")
                del_confirm = st.checkbox(f"위험: [{selected_edit_pn}] 항목을 데이터베이스에서 영구 삭제합니다.")
                if st.button("부품 삭제 실행", disabled=not del_confirm):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM components WHERE part_number = ?", (selected_edit_pn,))
                    conn.commit()
                    conn.close()
                    st.session_state["modal_msg"] = f"부품 [{selected_edit_pn}]이 완전히 삭제되었습니다."
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # 3) 대량 업로드 / 다운로드
        with excel_tab:
            st.markdown('<div class="content-card"><div class="card-title">대량 데이터 가져오기/내보내기</div>', unsafe_allow_html=True)
            col_dn, col_up = st.columns(2)
            
            with col_dn:
                st.markdown("##### 1. 대량 등록용 양식 다운로드")
                st.caption("표준 포맷에 맞춰 부품 데이터를 한꺼번에 입력할 수 있습니다.")
                template_df = pd.DataFrame([{
                    "part_number": "RC0603FR-0710KL",
                    "category": "저항 (Resistors)",
                    "description": "10K ohm 1% 0603",
                    "location": "A-01-01",
                    "quantity": 100,
                    "safety_stock": 10,
                    "datasheet_url": "https://example.com"
                }])
                csv_data = template_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="CSV 입력 표준 양식 다운로드",
                    data=csv_data,
                    file_name="부품등록_양식.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_up:
                st.markdown("##### 2. 파일 업로드")
                st.caption("작성된 CSV 또는 XLSX 파일을 업로드해주세요.")
                uploaded_file = st.file_uploader("파일 선택", type=["csv", "xlsx"], label_visibility="collapsed")
            
            if uploaded_file:
                st.divider()
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)
                        
                    st.markdown("##### 업로드 데이터 미리보기")
                    st.dataframe(df_upload.head(), use_container_width=True, hide_index=True)
                    
                    if st.button("데이터베이스 대량 반영 실행", type="primary", use_container_width=True):
                        conn = get_connection()
                        c = conn.cursor()
                        success_count = 0
                        skip_count = 0
                        
                        for _, row in df_upload.iterrows():
                            pn = str(row.get("part_number", "")).strip()
                            cat = str(row.get("category", "기구/기타 (Hardware)")).strip()
                            desc = str(row.get("description", "")) if pd.notna(row.get("description")) else ""
                            loc = str(row.get("location", "미정")).strip()
                            qty = int(row.get("quantity", 0)) if pd.notna(row.get("quantity")) else 0
                            s_stock = int(row.get("safety_stock", 5)) if pd.notna(row.get("safety_stock")) else 5
                            ds_url = str(row.get("datasheet_url", "")) if pd.notna(row.get("datasheet_url")) else ""
                            
                            if not pn or pn.lower() == "nan":
                                continue
                                
                            try:
                                c.execute("""
                                    INSERT INTO components (part_number, category, description, location, quantity, safety_stock, datasheet_url)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (pn, cat, desc, loc, qty, s_stock, ds_url))
                                
                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                c.execute("""
                                    INSERT INTO transactions (part_number, user_name, trans_type, quantity, timestamp, note)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (pn, "ADMIN_EXCEL", "CHECK_IN", qty, now_str, "엑셀 대량 등록"))
                                
                                success_count += 1
                            except sqlite3.IntegrityError:
                                skip_count += 1
                                
                        conn.commit()
                        conn.close()
                        
                        st.session_state["modal_msg"] = f"대량 등록 완료 (신규 성공: {success_count}건, 중복 건너뜀: {skip_count}건)"
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"파일을 읽는 과정에서 오류가 발생했습니다: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 3. 입출고 히스토리 조회
# ----------------------------------------------------
elif menu == "입출고 히스토리 조회":
    st.markdown('<div class="content-card"><div class="card-title">전체 입출고 감사 기록 (Audit Log)</div>', unsafe_allow_html=True)
    
    conn = get_connection()
    df_tx = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
    conn.close()
    
    if df_tx.empty:
        st.info("기록된 입출고 히스토리가 없습니다.")
    else:
        st.dataframe(
            df_tx.rename(columns={
                "id": "트랜잭션 ID",
                "part_number": "파트 넘버",
                "user_name": "작업자",
                "trans_type": "구분",
                "quantity": "수량",
                "timestamp": "일시",
                "note": "비고 / 프로젝트명"
            })[["트랜잭션 ID", "일시", "파트 넘버", "구분", "수량", "작업자", "비고 / 프로젝트명"]],
            use_container_width=True,
            hide_index=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
