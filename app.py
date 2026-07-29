import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import io

# 1. Page UI 구성 (사이드바 기본 펼침 설정)
st.set_page_config(
    page_title="연구소 HW팀 부품 재고 관리", 
    page_icon="📦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# 🖼️ 로고 이미지 안전 로딩
# ----------------------------------------------------
IMAGE_DIR = r"C:\python"
logo_loaded = False

if os.path.exists(IMAGE_DIR):
    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().startswith("logo"):
            full_path = os.path.join(IMAGE_DIR, filename)
            try:
                img = Image.open(full_path)
                st.image(img, width=300)
                logo_loaded = True
                break
            except Exception:
                pass

if not logo_loaded and os.path.exists("logo.jpg"):
    try:
        img = Image.open("logo.jpg")
        st.image(img, width=300)
        logo_loaded = True
    except Exception:
        pass

st.title("📦 연구소 HW팀 부품 재고 관리")
st.caption("팀 내부 부품 위치 조회, 부품 등록/수정 및 실시간 출고/입고 관리")
st.divider()

# 세션 상태 초기화
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if "modal_msg" not in st.session_state:
    st.session_state["modal_msg"] = None

@st.dialog("✅ 처리 완료 안내")
def show_confirm_modal(message):
    st.success(message)
    st.write("요청하신 작업이 성공적으로 반영되었습니다.")
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
st.sidebar.title("📌 메뉴 선택")
menu = st.sidebar.radio(
    "원하시는 작업을 선택하세요:", 
    ["🔍 부품 조회 및 출고", "🛠️ 부품 등록 및 관리", "📜 입출고 내역 조회"]
)

st.sidebar.divider()
# 사이드바 로그인 관리
if st.session_state["is_admin"]:
    st.sidebar.success("🔓 관리자 권한 로그인됨")
    if st.sidebar.button("로그아웃"):
        st.session_state["is_admin"] = False
        st.rerun()
else:
    st.sidebar.info("🔒 관리자 로그인")
    with st.sidebar.form("sidebar_login"):
        pwd_input = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("인증")
        if login_btn:
            if pwd_input == ADMIN_PASSWORD:
                st.session_state["is_admin"] = True
                st.success("인증 완료!")
                st.rerun()
            else:
                st.error("비밀번호 오류")

# ----------------------------------------------------
# 1. 부품 조회 및 출고
# ----------------------------------------------------
if "🔍 부품 조회" in menu:
    st.subheader("🔍 부품 검색 및 재고/출고 관리")
    
    conn = get_connection()
    df_components = pd.read_sql_query("SELECT * FROM components", conn)
    conn.close()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("부품명 / 제조사 파트넘버 / 보관위치 검색", "")
    with col2:
        categories = ["전체"] + (df_components["category"].unique().tolist() if not df_components.empty else [])
        selected_category = st.selectbox("카테고리 필터", categories)
        
    filtered_df = df_components.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df["part_number"].str.contains(search_query, case=False, na=False) |
            filtered_df["description"].str.contains(search_query, case=False, na=False) |
            filtered_df["location"].str.contains(search_query, case=False, na=False)
        ]
    if selected_category != "전체":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]
        
    st.markdown("### 📦 현재 부품 재고 현황")
    if filtered_df.empty:
        st.info("등록된 부품이 없거나 검색 결과가 없습니다.")
    else:
        st.dataframe(
            filtered_df.rename(columns={
                "part_number": "파트 넘버 (P/N)",
                "category": "카테고리",
                "description": "설명",
                "location": "보관 위치",
                "quantity": "수량",
                "safety_stock": "안전 재고",
                "datasheet_url": "데이터시트"
            })[["파트 넘버 (P/N)", "카테고리", "보관 위치", "수량", "안전 재고", "설명", "데이터시트"]],
            use_container_width=True,
            column_config={
                "데이터시트": st.column_config.LinkColumn(
                    label="📄 데이터시트",
                    help="클릭 시 데이터시트 페이지로 이동합니다.",
                    display_text="열기 🔗"
                )
            }
        )
        
        # ✏️ 조회된 부품 바로 수정하는 창 (관리자 전용)
        with st.expander("✏️ 조회된 부품 정보 수정 (관리자 전용)"):
            if not st.session_state["is_admin"]:
                st.warning("🔒 오른쪽 사이드바에서 관리자 로그인 후 이용하실 수 있습니다.")
            else:
                edit_pn_list = filtered_df["part_number"].tolist()
                selected_edit_pn = st.selectbox("수정할 부품 (P/N) 선택", edit_pn_list, key="quick_edit_sel")
                
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
                        e_safety_stock = st.number_input("안전 재고", min_value=0, value=int(target_row["safety_stock"]))
                        e_datasheet_url = st.text_input("데이터시트 URL", value=target_row["datasheet_url"] if target_row["datasheet_url"] else "")
                        
                    e_description = st.text_area("부품 설명 / 사양", value=target_row["description"] if target_row["description"] else "")
                    
                    quick_edit_submit = st.form_submit_button("수정사항 저장")
                    
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
                            
                            st.session_state["modal_msg"] = f"부품 [{e_part_number}] 정보가 정상적으로 수정되었습니다!"
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("이미 동일한 이름의 파트 넘버가 존재합니다.")

    st.divider()
    
    st.subheader("⚡ 빠른 출고 및 수량 변경")
    if not df_components.empty:
        part_list = df_components["part_number"].tolist()
        
        with st.form("checkout_form"):
            col_p, col_u, col_q, col_t = st.columns([2, 1.5, 1, 1])
            with col_p:
                selected_pn = st.selectbox("부품 선택 (P/N)", part_list)
            with col_u:
                user_name = st.text_input("사용자 이름", placeholder="예: 홍길동")
            with col_q:
                trans_qty = st.number_input("수량", min_value=1, value=1, step=1)
            with col_t:
                trans_type = st.radio("구분", ["출고 (-)", "입고 (+)"])
                
            note = st.text_input("비고 / 프로젝트명", placeholder="예: 샘플 기판 검증용")
            submit_btn = st.form_submit_button("재고 반영 및 기록")
            
            if submit_btn:
                if not user_name.strip():
                    st.error("사용자 이름을 입력해주세요.")
                else:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("SELECT quantity FROM components WHERE part_number = ?", (selected_pn,))
                    current_qty = c.fetchone()[0]
                    
                    is_checkout = "출고" in trans_type
                    change_qty = -trans_qty if is_checkout else trans_qty
                    new_qty = current_qty + change_qty
                    
                    if is_checkout and current_qty < trans_qty:
                        st.error(f"재고가 부족합니다. (현재 재고: {current_qty}개)")
                    else:
                        c.execute("UPDATE components SET quantity = ? WHERE part_number = ?", (new_qty, selected_pn))
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("""
                            INSERT INTO transactions (part_number, user_name, trans_type, quantity, timestamp, note)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (selected_pn, user_name, "CHECK_OUT" if is_checkout else "CHECK_IN", trans_qty, now_str, note))
                        
                        conn.commit()
                        conn.close()
                        
                        st.session_state["modal_msg"] = f"[{selected_pn}] {trans_type} ({trans_qty}개) 반영 완료! (잔여: {new_qty}개)"
                        st.rerun()

# ----------------------------------------------------
# 2. 부품 등록 및 관리
# ----------------------------------------------------
elif "🛠️ 부품 등록" in menu:
    st.subheader("🛠️ 부품 신규 등록 및 정보 수정 (관리자 전용)")
    
    if not st.session_state["is_admin"]:
        st.warning("🔒 부품 관리 권한이 필요합니다. 사이드바 메뉴에서 관리자로 로그인해주세요.")
    else:
        reg_tab, edit_tab, excel_tab = st.tabs([
            "➕ 신규 부품 등록", 
            "📝 기존 부품 정보 수정 및 삭제", 
            "📂 엑셀/CSV 일괄 등록 (업로드/다운로드)"
        ])
        
        # 1) 개별 부품 신규 등록
        with reg_tab:
            with st.form("register_form"):
                col1, col2 = st.columns(2)
                with col1:
                    part_number = st.text_input("파트 넘버 (P/N) *", placeholder="예: RC0603FR-0710KL")
                    category = st.selectbox("카테고리 *", CATEGORY_LIST)
                    location = st.text_input("보관 위치 *", placeholder="예: A-01-03")
                
                with col2:
                    init_quantity = st.number_input("초기 수량 *", min_value=0, value=100, step=10)
                    safety_stock = st.number_input("안전 재고", min_value=0, value=10, step=5)
                    datasheet_url = st.text_input("데이터시트 URL", placeholder="https://...")
                    
                description = st.text_area("부품 설명 / 사양")
                reg_submit = st.form_submit_button("부품 등록하기")
                
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
                            
                            st.session_state["modal_msg"] = f"신규 부품 [{part_number}]이 등록되었습니다!"
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"이미 존재하는 파트 넘버입니다: {part_number}")

        # 2) 개별 부품 수정 및 삭제
        with edit_tab:
            conn = get_connection()
            df_comp = pd.read_sql_query("SELECT * FROM components", conn)
            conn.close()
            
            if df_comp.empty:
                st.info("등록된 부품이 없습니다.")
            else:
                p_list = df_comp["part_number"].tolist()
                selected_edit_pn = st.selectbox("수정/삭제할 부품 (P/N) 선택", p_list, key="tab_edit_sel")
                target_row = df_comp[df_comp["part_number"] == selected_edit_pn].iloc[0]
                cat_index = CATEGORY_LIST.index(target_row["category"]) if target_row["category"] in CATEGORY_LIST else 0
                
                with st.form("edit_component_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_part_number = st.text_input("파트 넘버 (P/N)", value=target_row["part_number"])
                        e_category = st.selectbox("카테고리", CATEGORY_LIST, index=cat_index)
                        e_location = st.text_input("보관 위치", value=target_row["location"])
                    
                    with col2:
                        e_quantity = st.number_input("현재 수량", min_value=0, value=int(target_row["quantity"]))
                        e_safety_stock = st.number_input("안전 재고", min_value=0, value=int(target_row["safety_stock"]))
                        e_datasheet_url = st.text_input("데이터시트 URL", value=target_row["datasheet_url"] if target_row["datasheet_url"] else "")
                        
                    e_description = st.text_area("부품 설명 / 사양", value=target_row["description"] if target_row["description"] else "")
                    
                    edit_submit = st.form_submit_button("부품 정보 저장")
                    
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
                            
                            st.session_state["modal_msg"] = f"부품 [{e_part_number}] 정보가 성공적으로 수정되었습니다!"
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("이미 동일한 이름의 파트 넘버가 존재합니다.")

                # 🗑️ 부품 삭제 섹션 (실수 방지 유연성 포함)
                st.divider()
                st.markdown("#### 🗑️ 선택한 부품 삭제")
                del_confirm = st.checkbox(f"⚠️ 정말로 [{selected_edit_pn}] 부품을 삭제하시겠습니까?")
                if st.button("부품 완전 삭제", type="primary", disabled=not del_confirm):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM components WHERE part_number = ?", (selected_edit_pn,))
                    conn.commit()
                    conn.close()
                    st.session_state["modal_msg"] = f"부품 [{selected_edit_pn}]이 완전히 삭제되었습니다."
                    st.rerun()

        # 3) 엑셀 / CSV 대량 업로드 및 양식 다운로드
        with excel_tab:
            st.markdown("### 📥 대량 부품 등록 양식 다운로드")
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
                label="📄 대량 등록용 CSV 양식 다운로드",
                data=csv_data,
                file_name="부품등록_양식.csv",
                mime="text/csv"
            )
            
            st.divider()
            st.markdown("### 📤 엑셀/CSV 업로드 (대량 등록)")
            uploaded_file = st.file_uploader("CSV 또는 XLSX 파일 선택", type=["csv", "xlsx"])
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)
                        
                    st.write("📋 **업로드 미리보기:**")
                    st.dataframe(df_upload.head(), use_container_width=True)
                    
                    if st.button("🚀 데이터베이스에 반영하기"):
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
                        
                        st.session_state["modal_msg"] = f"대량 등록 완료! (성공: {success_count}건, 중복 건너뜀: {skip_count}건)"
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")

# ----------------------------------------------------
# 3. 입출고 내역 조회
# ----------------------------------------------------
elif "📜 입출고 내역" in menu:
    st.subheader("📜 전체 입출고 내역 기록")
    
    conn = get_connection()
    df_tx = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
    conn.close()
    
    if df_tx.empty:
        st.info("아직 기록된 입출고 내역이 없습니다.")
    else:
        st.dataframe(
            df_tx.rename(columns={
                "id": "기록 ID",
                "part_number": "파트 넘버",
                "user_name": "사용자",
                "trans_type": "구분",
                "quantity": "수량",
                "timestamp": "일시",
                "note": "비고/목적"
            })[["기록 ID", "일시", "파트 넘버", "구분", "수량", "사용자", "비고/목적"]],
            use_container_width=True
        )
