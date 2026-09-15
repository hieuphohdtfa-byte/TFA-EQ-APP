import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 🔗 TỰ ĐỘNG KẾT NỐI VỚI GOOGLE SHEET QUA WEB APP URL CỦA BẠN
# -----------------------------------------------------------------------------
GAS_URL = "https://script.google.com/macros/s/AKfycbwberqVIUJFxysiahO69QJT_3AJn2YDmrTvzUzdyC21sI_QbR0B-Xrz3mRD-Yo0vdDIkw/exec"

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG & GIAO DIỆN VÀNG - TRẮNG - XÁM (TFA BRAND)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The FIRST Academy - Hệ Thống Quản Lý Cảm Xúc EQ",
    layout="wide",
    page_icon="☀️"
)

st.markdown("""
    <style>
        .stApp { background-color: #FFFDF5; }
        .main-header {
            background: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
            padding: 20px 30px;
            border-radius: 12px;
            color: #1A1A1A;
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.25);
            margin-bottom: 25px;
        }
        .main-header h2 { color: #1A1A1A !important; font-weight: 800; margin: 0; font-size: 26px; }
        .main-header p { color: #2D2D2D; margin: 4px 0 0 0; font-size: 15px; font-weight: 500; }
        .login-card {
            background-color: #FFFFFF;
            padding: 25px 20px 15px 20px;
            border-radius: 16px;
            border: 2px solid #FFE082;
            box-shadow: 0 8px 20px rgba(0,0,0,0.06);
            text-align: center;
        }
        .stButton>button {
            background-color: #FFC107;
            color: #1A1A1A;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            padding: 10px 24px;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #FFB300;
            color: #000000;
            box-shadow: 0 4px 12px rgba(255, 179, 0, 0.4);
            transform: translateY(-2px);
        }
        section[data-testid="stSidebar"] {
            background-color: #FFF9E6;
            border-right: 1px solid #FFE082;
        }
        .info-card {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 16px;
            border: 1px solid #FFE58F;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            margin-bottom: 20px;
        }
        .campus-badge {
            background-color: #FFF3C4;
            color: #8C6200;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 13px;
            display: inline-block;
            margin: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. KHỜI TẠO MÃ CƠ SỞ & KHỐI LỚP CHUẨN
# -----------------------------------------------------------------------------
CAMPUS_MAP = {
    "HD": "Cơ sở TFA Hà Đô (Phường Cát Lái, TP.HCM)",
    "TTL": "Cơ sở TFA Trần Thị Lý (Đà Nẵng)",
    "DBM": "Cơ sở TFA Dương Bạch Mai (Quận 8, TP.HCM)",
    "HL": "Cơ sở TFA Him Lam (Phường Tân Hưng, Quận 7, TP.HCM)",
    "LVS": "Cơ sở TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)"
}

TFA_CLASSES = ["Toddler 1", "Toddler 2", "Pre-school", "Kindergarten", "Pre-primary"]
TFA_ROUTINES = [
    "Đón trẻ - Thể dục sáng", "Ăn sáng", "Hoạt động có chủ đích",
    "Ăn trưa", "Ăn xế", "Hoạt động chiều", "Trả trẻ", "Tình huống phát sinh"
]
MONTH_OPTIONS = ["Tất cả các tháng"] + [f"Tháng {m}" for m in range(1, 13)]
LOGO_FILE = "logo.png" if os.path.exists("logo.png") else ("Logo TFA Ver2.1 .png" if os.path.exists("Logo TFA Ver2.1 .png") else "logo.png")

# -----------------------------------------------------------------------------
# 3. DỮ LIỆU TÀI KHOẢN MẶC ĐỊNH & HÀM ĐỒNG BỘ GOOGLE SHEET
# -----------------------------------------------------------------------------
DEFAULT_USERS_DF = pd.DataFrame([
    {"username": "admin", "password": "admin123", "name": "Ban Giám Hiệu Tổng (Toàn Hệ Thống)", "role": "super_admin", "campus_code": "ALL", "campus": "Tất cả cơ sở", "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHD", "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin", "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHTTL", "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin", "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHDBM", "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin", "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHL", "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin", "campus_code": "HL", "campus": CAMPUS_MAP["HL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHLVS", "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin", "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"], "class_name": "Tất cả", "status": "active"}
])

def load_all_from_gas():
    try:
        res = requests.get(f"{GAS_URL}?action=read_all", timeout=12)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def save_sheet_to_gas(sheet_name, df):
    try:
        payload = {
            "action": "save_sheet",
            "sheet_name": sheet_name,
            "rows": df.astype(str).to_dict(orient="records")
        }
        res = requests.post(GAS_URL, json=payload, timeout=12)
        return res.status_code == 200
    except Exception as e:
        st.error(f"⚠️ Lỗi lưu Google Sheet: {e}")
        return False

# Nạp dữ liệu từ Google Sheet vào Session State
if 'gas_loaded' not in st.session_state:
    with st.spinner("🔄 Đang đồng bộ dữ liệu từ Google Trang tính..."):
        gas_data = load_all_from_gas()
        st.session_state.users_df = pd.DataFrame(gas_data.get("Users", [])) if gas_data.get("Users") else DEFAULT_USERS_DF
        st.session_state.students_df = pd.DataFrame(gas_data.get("Students", [])) if gas_data.get("Students") else pd.DataFrame(columns=["teacher_user", "student_name"])
        st.session_state.evaluations_df = pd.DataFrame(gas_data.get("Evaluations", [])) if gas_data.get("Evaluations") else pd.DataFrame(columns=["Teacher", "Campus", "Class", "Student", "Term", "TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "P_EQ", "Group_Clean", "Context", "Conclusion", "Plan"])
        st.session_state.daily_logs_df = pd.DataFrame(gas_data.get("DailyLogs", [])) if gas_data.get("DailyLogs") else pd.DataFrame(columns=["Teacher", "Campus", "Class", "Student", "Date", "Routine", "Emotions", "Note", "Intervention", "Summary"])
        st.session_state.comparisons_df = pd.DataFrame(gas_data.get("Comparisons", [])) if gas_data.get("Comparisons") else pd.DataFrame(columns=["Teacher", "Campus", "Class", "Student", "Score_Term1", "Score_Term2", "Delta", "Trend", "Conclusion", "Plan"])
        st.session_state.gas_loaded = True

if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

def get_users_dict():
    u_dict = {}
    for idx, row in st.session_state.users_df.iterrows():
        u_dict[row["username"]] = {
            "password": str(row["password"]),
            "name": row["name"],
            "role": row["role"],
            "campus_code": row["campus_code"],
            "campus": row["campus"],
            "class_name": row.get("class_name", "Chưa tạo lớp"),
            "status": row.get("status", "active")
        }
    return u_dict

# -----------------------------------------------------------------------------
# 4. HÀM HỖ TRỢ VẼ BIỂU ĐỒ
# -----------------------------------------------------------------------------
def render_eq_charts(eval_df, title_prefix=""):
    if eval_df.empty:
        st.info("Chưa có đủ dữ liệu để vẽ biểu đồ trực quan.")
        return
    
    st.markdown(f"#### 📊 BIỂU ĐỒ TRỰC QUAN PHÂN TÍCH CẢM XÚC EQ {title_prefix.upper()}")
    col_chart1, col_chart2 = st.columns(2)
    
    counts = eval_df["Group_Clean"].value_counts().reset_index()
    counts.columns = ["Nhóm EQ", "Số lượng"]
    color_map = { "DUY TRÌ": "#4CAF50", "CẦN CẢI THIỆN": "#FF9800", "HỖ TRỢ ĐẶC BIỆT": "#EF5350" }
    
    with col_chart1:
        fig_pie = px.pie(
            counts, names="Nhóm EQ", values="Số lượng", 
            title="<b>Tỉ lệ Phân bố các Nhóm Trạng Thái EQ</b>",
            color="Nhóm EQ", color_discrete_map=color_map, hole=0.45
        )
        fig_pie.update_traces(textinfo='percent+label', textfont_size=13)
        fig_pie.update_layout(showlegend=True, margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    tc_keys = ["TC1", "TC2", "TC3", "TC4", "TC5", "TC6"]
    tc_names = ["TC1: Nhận biết", "TC2: Bày tỏ", "TC3: Kiềm chế", "TC4: Đồng cảm", "TC5: Thích ứng", "TC6: Lắng nghe"]
    avg_scores = [round(pd.to_numeric(eval_df[k], errors='coerce').mean(), 2) for k in tc_keys if k in eval_df.columns]
    
    if len(avg_scores) == 6:
        df_tc = pd.DataFrame({"Tiêu chí": tc_names, "Điểm TB": avg_scores})
        with col_chart2:
            fig_bar = px.bar(
                df_tc, x="Tiêu chí", y="Điểm TB", text="Điểm TB",
                title="<b>Điểm Trung Bình 6 Tiêu Chí EQ (Thang 1-4)</b>",
                color="Điểm TB", color_continuous_scale=["#FFE082", "#FFC107", "#FF8F00"]
            )
            fig_bar.update_traces(textposition='outside')
            fig_bar.update_layout(yaxis_range=[0, 4.5], margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------------------------------------------------------
# 5. HEADER THƯƠNG HIỆU CHÍNH
# -----------------------------------------------------------------------------
head_col1, head_col2 = st.columns([1.2, 3.8])
with head_col1:
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=220)
    else: st.write("☀️ **THE FIRST ACADEMY**")
with head_col2:
    st.markdown("""
        <div class="main-header">
            <h2>THE FIRST ACADEMY (TFA) - EMOTIONAL INTELLIGENCE SYSTEM</h2>
            <p>Hệ thống Đánh giá & Theo dõi Xu hướng Phát triển Cảm xúc (EQ) Mầm Non Chuẩn Hóa</p>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. GIAO DIỆN BÌA NGOÀI / LANDING PAGE (CHƯA ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
users_dict = get_users_dict()

if st.session_state.logged_user is None:
    col_left, col_right = st.columns([1.1, 1.9], gap="large")
    
    with col_left:
        st.markdown("""
            <div class="login-card">
                <h3 style="color: #1A1A1A; margin-top: 5px; font-weight: 700;">🔐 ĐĂNG NHẬP HỆ THỐNG</h3>
                <p style="color: #666; font-size: 13px; margin-bottom: 15px;">Dành cho Ban Giám Hiệu & Giáo Viên TFA</p>
            </div>
        """, unsafe_allow_html=True)
        
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=260)
            
        login_user = st.text_input("👤 Tên đăng nhập:", key="login_u", placeholder="Nhập tên đăng nhập...").strip()
        login_pass = st.text_input("🔑 Mật khẩu:", type="password", key="login_p", placeholder="Nhập mật khẩu...").strip()
        
        st.write("")
        if st.button("🚀 CỔNG ĐĂNG NHẬP"):
            if login_user in users_dict:
                u_info = users_dict[login_user]
                if str(u_info["password"]) == str(login_pass):
                    if u_info.get("status", "active") == "inactive":
                        st.error("❌ Tài khoản này đã bị NGƯNG HIỆU LỰC hoạt động! Vui lòng liên hệ BGH.")
                    else:
                        st.session_state.logged_user = login_user
                        st.success(f"🎉 Đăng nhập thành công! Chào mừng {u_info['name']}")
                        st.rerun()
                else:
                    st.error("❌ Mật khẩu không chính xác! Vui lòng kiểm tra lại.")
            else:
                st.error("❌ Tên đăng nhập không tồn tại trên hệ thống!")

    with col_right:
        st.markdown("""
            <div class="info-card">
                <h3 style="color: #000; margin-top:0;">🏫 HỆ THỐNG TRƯỜNG MẦM NON SONG NGỮ THE FIRST ACADEMY</h3>
                <p style="color: #444; line-height: 1.6; font-size: 14.5px;">
                    <b>The FIRST Academy (TFA)</b> là môi trường giáo dục mầm non song ngữ hiện đại, nơi mỗi đứa trẻ được chăm sóc và phát triển toàn diện cả về <b>Trí tuệ (IQ)</b> lẫn <b>Cảm xúc (EQ)</b>.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📍 Mạng lưới 5 Cơ sở Toàn hệ thống")
        st.markdown("""
            <div>
                <span class="campus-badge">🏢 TFA Hà Đô (Phường Cát Lái, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Dương Bạch Mai (Quận 8, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Him Lam (Phường Tân Hưng, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Trần Thị Lý (Đà Nẵng)</span>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. KHÔNG GIAN LÀM VIỆC TRONG APP (SAU KHI ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
else:
    user_info = users_dict[st.session_state.logged_user]
    user_key = st.session_state.logged_user
    role = user_info.get("role", "teacher")
    
    if os.path.exists(LOGO_FILE): st.sidebar.image(LOGO_FILE, width=220)
    st.sidebar.markdown(f"### 👤 Người dùng: **{user_info['name']}**")
    
    if role == "super_admin":
        st.sidebar.error("👑 **Vai trò:** Admin Tổng (Toàn Hệ Thống)")
    elif role == "campus_admin":
        st.sidebar.warning(f"🏫 **Vai trò:** BGH - {user_info['campus']}")
    else:
        st.sidebar.info(f"🏢 **Cơ sở:** {user_info['campus']}\n\n👩‍🏫 **Lớp:** {user_info.get('class_name', 'Chưa tạo lớp')}")
    
    if st.sidebar.button("🚪 Đăng Xuất"):
        st.session_state.logged_user = None
        st.rerun()

    st.sidebar.markdown("---")

    # =========================================================================
    # VAI TRÒ 1: ADMIN TỔNG (SUPER ADMIN)
    # =========================================================================
    if role == "super_admin":
        main_menu = st.sidebar.radio("DANH MỤC SUPER ADMIN:", ["👑 1. Tạo & Quản lý Tài khoản BGH", "📊 2. Báo cáo EQ Toàn Hệ Thống", "📝 3. Nhật ký Cảm xúc Toàn Trường"])
        
        if main_menu == "👑 1. Tạo & Quản lý Tài khoản BGH":
            st.subheader("👑 TẠO & QUẢN LÝ TÀI KHOẢN BGH CƠ SỞ")
            col1, col2 = st.columns(2)
            with col1: BGH_code = st.selectbox("Chọn Cơ sở quản lý:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}")
            with col2: BGH_name = st.text_input("Tên đại diện BGH:", value=f"BGH {CAMPUS_MAP[BGH_code]}").strip()
            BGH_u = st.text_input("Tên đăng nhập BGH:", value=f"BGH{BGH_code}").strip()
            BGH_p = st.text_input("Mật khẩu BGH:", value="123456")
            
            if st.button("➕ Tạo Tài Khoản BGH Cơ Sở"):
                if BGH_u in users_dict:
                    st.warning(f"⚠️ Tên đăng nhập `{BGH_u}` đã tồn tại!")
                else:
                    new_row = pd.DataFrame([{
                        "username": BGH_u, "password": BGH_p, "name": BGH_name,
                        "role": "campus_admin", "campus_code": BGH_code,
                        "campus": CAMPUS_MAP[BGH_code], "class_name": "Tất cả", "status": "active"
                    }])
                    st.session_state.users_df = pd.concat([st.session_state.users_df, new_row], ignore_index=True)
                    save_sheet_to_gas("Users", st.session_state.users_df)
                    st.success(f"🎉 Đã lưu vĩnh viễn trên Google Sheets! Tên TK: `{BGH_u}` | Mật khẩu: `{BGH_p}`")
                    st.rerun()

            st.markdown("---")
            st.dataframe(st.session_state.users_df, use_container_width=True)

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ TOÀN HỆ THỐNG")
            st.dataframe(st.session_state.evaluations_df, use_container_width=True)
            render_eq_charts(st.session_state.evaluations_df, "(Toàn Trường)")

        else:
            st.subheader("📝 NHẬT KÝ CẢM XÚC TOÀN HỆ THỐNG")
            st.dataframe(st.session_state.daily_logs_df, use_container_width=True)

    # =========================================================================
    # VAI TRÒ 2: BGH TỪNG CƠ SỞ (CAMPUS ADMIN)
    # =========================================================================
    elif role == "campus_admin":
        my_campus = user_info['campus']
        my_code = user_info['campus_code']
        main_menu = st.sidebar.radio(f"DANH MỤC BGH ({my_code}):", [f"🏫 1. Tạo Giáo viên ({my_code})", f"📊 2. Báo cáo EQ Cơ sở ({my_code})"])
        
        if main_menu == f"🏫 1. Tạo Giáo viên ({my_code})":
            st.subheader(f"🏫 BGH QUẢN LÝ VÀ TẠO TÀI KHOẢN GIÁO VIÊN: {my_campus.upper()}")
            col1, col2 = st.columns(2)
            with col1: t_phone = st.text_input("Số điện thoại Giáo viên:").strip()
            with col2: t_name = st.text_input("Họ và tên Giáo viên:").strip()
            
            if st.button("➕ Tạo Tài Khoản Giáo Viên"):
                if t_phone and t_name:
                    gen_u = f"{t_phone}{my_code}"
                    if gen_u in users_dict:
                        st.warning(f"⚠️ Tài khoản `{gen_u}` đã tồn tại!")
                    else:
                        new_row = pd.DataFrame([{
                            "username": gen_u, "password": "123456", "name": t_name,
                            "role": "teacher", "campus_code": my_code,
                            "campus": my_campus, "class_name": "Chưa tạo lớp", "status": "active"
                        }])
                        st.session_state.users_df = pd.concat([st.session_state.users_df, new_row], ignore_index=True)
                        save_sheet_to_gas("Users", st.session_state.users_df)
                        st.success(f"🎉 Đã lưu vĩnh viễn trên Google Sheets! Tên TK: `{gen_u}` | Mật khẩu: `123456`")
                        st.rerun()

            st.markdown("---")
            gv_df = st.session_state.users_df[(st.session_state.users_df['role'] == 'teacher') & (st.session_state.users_df['campus_code'] == my_code)]
            st.dataframe(gv_df, use_container_width=True)

        else:
            df_c = st.session_state.evaluations_df[st.session_state.evaluations_df['Campus'] == my_campus]
            st.dataframe(df_c, use_container_width=True)

    # =========================================================================
    # VAI TRÒ 3: GIÁO VIÊN TỪNG LỚP
    # =========================================================================
    else:
        main_menu = st.sidebar.radio("DANH MỤC GIÁO VIÊN:", ["🏫 1. Quản lý Học sinh", "📝 2. Nhật ký Cảm xúc", "🎯 3. Đánh giá EQ 6 Tiêu chí", "📊 4. Báo cáo Lớp"])

        if main_menu == "🏫 1. Quản lý Học sinh":
            st.subheader("🏫 TỰ TẠO LỚP HỌC & QUẢN LÝ HỌC SINH")
            col_l1, col_l2 = st.columns(2)
            with col_l1: sel_class_type = st.selectbox("Chọn Khối lớp:", TFA_CLASSES)
            with col_l2: custom_class_name = st.text_input("Tên riêng của Lớp:", value=user_info.get("class_name", sel_class_type))
                
            if st.button("💾 Cập Nhật Tên Lớp"):
                user_idx = st.session_state.users_df[st.session_state.users_df['username'] == user_key].index
                if not user_idx.empty:
                    st.session_state.users_df.at[user_idx[0], "class_name"] = custom_class_name
                    save_sheet_to_gas("Users", st.session_state.users_df)
                    st.success(f"🎉 Đã lưu tên lớp: **{custom_class_name}**")
                    st.rerun()

            st.markdown("---")
            new_student = st.text_input("Họ và tên học sinh mới:").strip()
            if st.button("➕ Thêm Học Sinh Mới"):
                if new_student:
                    new_std_row = pd.DataFrame([{"teacher_user": user_key, "student_name": new_student}])
                    st.session_state.students_df = pd.concat([st.session_state.students_df, new_std_row], ignore_index=True)
                    save_sheet_to_gas("Students", st.session_state.students_df)
                    st.success(f"🎉 Đã lưu vĩnh viễn bé **{new_student}** vào Google Sheet!")
                    st.rerun()

            st.markdown("---")
            my_stds_df = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]
            if not my_stds_df.empty:
                st.dataframe(my_stds_df[['student_name']], use_container_width=True)
            else: st.info("Lớp chưa có học sinh nào.")

        elif main_menu == "📝 2. Nhật ký Cảm xúc":
            st.subheader("📝 NHẬT KÝ CẢM XÚC HẰNG NGÀY")
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds: st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng thêm học sinh trước!")
            else:
                col_s1, col_s2 = st.columns(2)
                with col_s1: std_select = st.selectbox("Chọn học sinh:", my_stds)
                with col_s2: log_date = st.date_input("Ngày theo dõi:")
                routine_sel = st.selectbox("Hoạt động trong ngày:", TFA_ROUTINES)
                emotions = st.multiselect("Cảm xúc nổi bật:", ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng 😮‍💨"])
                note = st.text_area("1. Bối cảnh & biểu hiện:")
                intervention = st.text_area("2. Can thiệp của giáo viên:")
                summary_note = st.text_input("3. Nhận xét chung:")
                
                if st.button("💾 Lưu Nhật Ký"):
                    new_log = pd.DataFrame([{
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_select,
                        "Date": str(log_date), "Routine": routine_sel,
                        "Emotions": ", ".join(emotions), "Note": note,
                        "Intervention": intervention, "Summary": summary_note
                    }])
                    st.session_state.daily_logs_df = pd.concat([st.session_state.daily_logs_df, new_log], ignore_index=True)
                    save_sheet_to_gas("DailyLogs", st.session_state.daily_logs_df)
                    st.success(f"🎉 Đã lưu vĩnh viễn nhật ký cho bé **{std_select}** lên Google Sheets!")

        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ CHUẨN")
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_e1, col_e2 = st.columns(2)
                with col_e1: std_eval = st.selectbox("Chọn học sinh:", my_stds)
                with col_e2: 
                    eval_month = st.selectbox("Chọn Tháng:", [f"Tháng {m}" for m in range(1, 13)], index=5)
                    term = f"{eval_month} / Kỳ {1 if int(eval_month.replace('Tháng ', '')) <= 6 else 2}"
                
                c1, c2 = st.columns(2)
                with c1:
                    tc1 = st.slider("TC1: Nhận biết", 1, 4, 2)
                    tc2 = st.slider("TC2: Bày tỏ", 1, 4, 2)
                    tc3 = st.slider("TC3: Kiềm chế", 1, 4, 2)
                with c2:
                    tc4 = st.slider("TC4: Đồng cảm", 1, 4, 2)
                    tc5 = st.slider("TC5: Thích ứng", 1, 4, 3)
                    tc6 = st.slider("TC6: Lắng nghe", 1, 4, 3)
                    
                peq = round((tc1 + tc2 + tc3 + tc4 + tc5 + tc6) / 6.0, 2)
                group_clean = "DUY TRÌ" if peq >= 3.2 else ("CẦN CẢI THIỆN" if peq >= 2.0 else "HỖ TRỢ ĐẶC BIỆT")
                st.metric("Điểm EQ Tổng hợp (PEQ):", peq, delta=group_clean)
                
                context_input = st.text_area("Bối cảnh minh chứng:", value=f"{std_eval} thường...")
                conclusion_input = st.text_area("Kết luận xu hướng:", value=f"Xu hướng của {std_eval}...")
                plan_input = st.text_area("Kế hoạch tác động:", value=f"Hướng dẫn {std_eval}...")
                
                if st.button("💾 Lưu Đánh Giá EQ"):
                    new_eval = pd.DataFrame([{
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_eval, "Term": term,
                        "TC1": tc1, "TC2": tc2, "TC3": tc3, "TC4": tc4, "TC5": tc5, "TC6": tc6,
                        "P_EQ": peq, "Group_Clean": group_clean,
                        "Context": context_input, "Conclusion": conclusion_input, "Plan": plan_input
                    }])
                    st.session_state.evaluations_df = pd.concat([st.session_state.evaluations_df, new_eval], ignore_index=True)
                    save_sheet_to_gas("Evaluations", st.session_state.evaluations_df)
                    st.success(f"🎉 Đã lưu vĩnh viễn đánh giá EQ cho bé **{std_eval}** lên Google Sheets!")

        else:
            st.subheader("📊 BÁO CÁO CẢM XÚC VÀ ĐÁNH GIÁ CỦA LỚP")
            my_evals = st.session_state.evaluations_df[st.session_state.evaluations_df['Teacher'] == user_info['name']]
            if not my_evals.empty:
                st.dataframe(my_evals, use_container_width=True)
                render_eq_charts(my_evals, f"Lớp {user_info['class_name']}")
            else: st.info("Chưa có dữ liệu đánh giá EQ.")
