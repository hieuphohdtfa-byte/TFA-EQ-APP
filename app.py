import streamlit as st
import pandas as pd
import os

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG & GIAO DIỆN VÀNG - TRẮNG - XÁM (TFA BRAND)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The FIRST Academy - Hệ Thống Quản Lý Cảm Xúc EQ",
    layout="wide",
    page_icon="☀️"
)

# Custom CSS giao diện thương hiệu TFA (Vàng - Trắng - Xám)
st.markdown("""
    <style>
        .stApp {
            background-color: #FFFDF5;
        }
        .main-header {
            background: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
            padding: 20px 30px;
            border-radius: 12px;
            color: #1A1A1A;
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.25);
            margin-bottom: 25px;
        }
        .main-header h2 {
            color: #1A1A1A !important;
            font-weight: 800;
            margin: 0;
            font-size: 26px;
        }
        .main-header p {
            color: #2D2D2D;
            margin: 4px 0 0 0;
            font-size: 15px;
            font-weight: 500;
        }
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
# 2. KHỞI TẠO MÃ CƠ SỞ & KHỐI LỚP CHUẨN
# -----------------------------------------------------------------------------
CAMPUS_MAP = {
    "HD": "Cơ sở TFA Hà Đô (Cát Lái, TP.HCM)",
    "TTL": "Cơ sở TFA Trần Thị Lý (Đà Nẵng)",
    "DBM": "Cơ sở TFA Dương Bạch Mai (Quận 8, TP.HCM)",
    "HL": "Cơ sở TFA Him Lam (Quận 7, TP.HCM)",
    "LVS": "Cơ sở TFA Lê Văn Sỹ (Quận 3, TP.HCM)"
}

TFA_CLASSES = [
    "Toddler ",
    "Pre-school",
    "Kindergarten",
    "Pre-primary"
]

TFA_ROUTINES = [
    "Đón trẻ - Thể dục sáng",
    "Ăn sáng",
    "Hoạt động có chủ đích",
    "Ăn trưa",
    "Ăn xế",
    "Hoạt động chiều",
    "Trả trẻ",
    "Tình huống phát sinh"
]

LOGO_FILE = "logo.png" if os.path.exists("logo.png") else ("Logo TFA Ver2.1 .png" if os.path.exists("Logo TFA Ver2.1 .png") else "logo.png")

# -----------------------------------------------------------------------------
# 3. LƯU TRỮ SESSION STATE (CƠ SỞ DỮ LIỆU TẠM THỜI)
# -----------------------------------------------------------------------------
if 'users' not in st.session_state:
    st.session_state.users = {
        "admin": {
            "password": "admin123",
            "name": "Ban Giám Hiệu Tổng (Toàn Hệ Thống)",
            "role": "super_admin",
            "campus_code": "ALL",
            "campus": "Tất cả cơ sở",
            "status": "active"
        },
        "BGHHD": {
            "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin",
            "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "status": "active"
        },
        "BGHTTL": {
            "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin",
            "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"], "status": "active"
        },
        "BGHDBM": {
            "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin",
            "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"], "status": "active"
        },
        "BGHHL": {
            "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin",
            "campus_code": "HL", "campus": CAMPUS_MAP["HL"], "status": "active"
        },
        "BGHLVS": {
            "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin",
            "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"], "status": "active"
        }
    }

if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

if 'students_db' not in st.session_state:
    st.session_state.students_db = {}

if 'evaluations_db' not in st.session_state:
    st.session_state.evaluations_db = []

if 'daily_logs_db' not in st.session_state:
    st.session_state.daily_logs_db = []

if 'comparisons_db' not in st.session_state:
    st.session_state.comparisons_db = []

# -----------------------------------------------------------------------------
# 4. HEADER THƯƠNG HIỆU CHÍNH
# -----------------------------------------------------------------------------
head_col1, head_col2 = st.columns([1.2, 3.8])
with head_col1:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=220)
    else:
        st.write("☀️ **THE FIRST ACADEMY**")
with head_col2:
    st.markdown("""
        <div class="main-header">
            <h2>THE FIRST ACADEMY (TFA) - EMOTIONAL INTELLIGENCE SYSTEM</h2>
            <p>Hệ thống Đánh giá & Theo dõi Xu hướng Phát triển Cảm xúc (EQ) Mầm Non Chuẩn Hóa</p>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. GIAO DIỆN BÌA NGOÀI / LANDING PAGE (CHƯA ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
if st.session_state.logged_user is None:
    col_left, col_right = st.columns([1.1, 1.9], gap="large")
    
    with col_left:
        st.markdown("""
            <div class="login-card">
                <h3 style="color: #1A1A1A; margin-top: 5px; font-weight: 700;">🔐 ĐĂNG NHẬP HỆ THỐNG</h3>
                <p style="color: #666; font-size: 13px; margin-bottom: 15px;">
                    Dành cho Ban Giám Hiệu & Giáo Viên TFA
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=260)
            
        login_user = st.text_input("👤 Tên đăng nhập:", key="login_u", placeholder="Nhập tên đăng nhập...").strip()
        login_pass = st.text_input("🔑 Mật khẩu:", type="password", key="login_p", placeholder="Nhập mật khẩu...").strip()
        
        st.write("")
        if st.button("🚀 CỔNG ĐĂNG NHẬP"):
            if login_user in st.session_state.users:
                u_info = st.session_state.users[login_user]
                if u_info["password"] == login_pass:
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
                    Ứng dụng được thiết kế nhằm theo dõi nhật ký cảm xúc hằng ngày và phân tích xu hướng phát triển EQ của trẻ theo bộ tiêu chí chuẩn hóa.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📍 Mạng lưới 5 Cơ sở Toàn hệ thống")
        st.markdown("""
            <div>
                <span class="campus-badge">🏢 TFA Hà Đô (Cát Lái, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Lê Văn Sỹ (Quận 3, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Dương Bạch Mai (Quận 8, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Him Lam (Quận 7, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Trần Thị Lý (Đà Nẵng)</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.markdown("#### 🎨 Các Khối Lớp Đào Tạo Chuẩn")
        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            st.info("👶 **Toddler 1 & 2**\n\n*(Nhóm trẻ từ 12–36 tháng)*")
        with col_k2:
            st.warning("🌱 **Pre-school & Kindergarten**\n\n*(Khối Lớp Mầm & Chồi 3–5 tuổi)*")
        with col_k3:
            st.success("🎓 **Pre-primary**\n\n*(Khối Lớp Lá 5–6 tuổi chuẩn bị vào Lớp 1)*")

        st.markdown("""
            <div style="background-color: #FFFDF5; padding: 15px; border-radius: 12px; border: 1px solid #FFE082; margin-top: 15px;">
                <b>🎯 Mục tiêu chương trình EQ tại TFA:</b>
                <ul style="margin-bottom: 0; color: #444; font-size: 13.5px;">
                    <li>Nhận biết và gọi tên chính xác các trạng thái cảm xúc.</li>
                    <li>Rèn luyện khả năng tự điều chỉnh và kiểm soát hành vi tích cực.</li>
                    <li>Nuôi dưỡng sự đồng cảm, giao tiếp xã hội và giải quyết xung đột lành mạnh.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. KHÔNG GIAN LÀM VIỆC TRONG APP (SAU KHI ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
else:
    user_info = st.session_state.users[st.session_state.logged_user]
    user_key = st.session_state.logged_user
    role = user_info.get("role", "teacher")
    
    if os.path.exists(LOGO_FILE):
        st.sidebar.image(LOGO_FILE, width=220)
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
    
    # --- CÁC HÀM XUẤT DATAFRAME CHUẨN MẪU FILE NGUỒN ---
    def prepare_eq_report_df(eval_list):
        formatted_rows = []
        for idx, item in enumerate(eval_list, 1):
            formatted_rows.append({
                "STT": idx,
                "Tên học sinh": item.get("Student", ""),
                "TC1": item.get("TC1", 0),
                "TC2": item.get("TC2", 0),
                "TC3": item.get("TC3", 0),
                "TC4": item.get("TC4", 0),
                "TC5": item.get("TC5", 0),
                "TC6": item.get("TC6", 0),
                "Điểm TB (PEQ)": item.get("P_EQ", 0),
                "Nhóm Trạng Thái": item.get("Group_Clean", item.get("Group", "").replace("🟢 ", "").replace("🟠 ", "").replace("🔴 ", "")),
                "Bối cảnh/Minh chứng điển hình (hành vi cụ thể)": item.get("Context", ""),
                "Kết luận xu hướng": item.get("Conclusion", ""),
                "Kế hoạch tác động tiếp theo": item.get("Plan", ""),
                "Lớp": item.get("Class", ""),
                "Cơ sở": item.get("Campus", ""),
                "Kỳ đánh giá": item.get("Term", ""),
                "Giáo viên": item.get("Teacher", "")
            })
        return pd.DataFrame(formatted_rows)

    def prepare_daily_log_df(log_list):
        formatted_rows = []
        for idx, item in enumerate(log_list, 1):
            formatted_rows.append({
                "STT": idx,
                "Họ và tên trẻ": item.get("Student", ""),
                "Lớp": item.get("Class", ""),
                "Ngày": item.get("Date", ""),
                "Hoạt động trong ngày": item.get("Routine", "Tất cả hoạt động"),
                "Cảm xúc nổi bật": item.get("Emotions", ""),
                "Bối cảnh & biểu hiện nổi bật": item.get("Note", ""),
                "Can thiệp & hỗ trợ": item.get("Intervention", ""),
                "Nhận xét / Xu hướng": item.get("Summary", ""),
                "Cơ sở": item.get("Campus", ""),
                "Giáo viên": item.get("Teacher", "")
            })
        return pd.DataFrame(formatted_rows)

    def prepare_comparison_df(comp_list):
        formatted_rows = []
        for idx, item in enumerate(comp_list, 1):
            formatted_rows.append({
                "STT": idx,
                "Tên học sinh": item.get("Student", ""),
                "Điểm tháng 6 (Kỳ 1)": item.get("Score_Term1", 0.0),
                "Điểm tháng 7 (Kỳ 2)": item.get("Score_Term2", 0.0),
                "Biến thiên": item.get("Delta", 0.0),
                "Xu hướng EQ": item.get("Trend", ""),
                "Kết luận xu hướng": item.get("Conclusion", ""),
                "Kế hoạch tác động tiếp theo": item.get("Plan", ""),
                "Lớp": item.get("Class", ""),
                "Cơ sở": item.get("Campus", ""),
                "Giáo viên": item.get("Teacher", "")
            })
        return pd.DataFrame(formatted_rows)

    def compute_summary_stats(eval_list_term1, eval_list_term2):
        total_t1 = len(eval_list_term1) if len(eval_list_term1) > 0 else 1
        total_t2 = len(eval_list_term2) if len(eval_list_term2) > 0 else 1

        duytri_t1 = sum(1 for e in eval_list_term1 if e.get("P_EQ", 0) >= 3.2)
        caithien_t1 = sum(1 for e in eval_list_term1 if 2.0 <= e.get("P_EQ", 0) < 3.2)
        hotro_t1 = sum(1 for e in eval_list_term1 if e.get("P_EQ", 0) < 2.0)

        duytri_t2 = sum(1 for e in eval_list_term2 if e.get("P_EQ", 0) >= 3.2)
        caithien_t2 = sum(1 for e in eval_list_term2 if 2.0 <= e.get("P_EQ", 0) < 3.2)
        hotro_t2 = sum(1 for e in eval_list_term2 if e.get("P_EQ", 0) < 2.0)

        pct_dt1, pct_dt2 = round(duytri_t1 / total_t1 * 100, 2), round(duytri_t2 / total_t2 * 100, 2)
        pct_ct1, pct_ct2 = round(caithien_t1 / total_t1 * 100, 2), round(caithien_t2 / total_t2 * 100, 2)
        pct_ht1, pct_ht2 = round(hotro_t1 / total_t1 * 100, 2), round(hotro_t2 / total_t2 * 100, 2)

        diff_dt = round(pct_dt2 - pct_dt1, 2)
        diff_ct = round(pct_ct2 - pct_ct1, 2)
        diff_ht = round(pct_ht2 - pct_ht1, 2)

        stats_data = [
            {
                "Chỉ số thống kê nhóm EQ": "Tỉ lệ nhóm DUY TRÌ (PEQ >= 3.2)",
                "Kỳ 1 (Tháng 6)": f"{pct_dt1}%",
                "Kỳ 2 (Tháng 7)": f"{pct_dt2}%",
                "Thay đổi": f"{'+' if diff_dt > 0 else ''}{diff_dt}% ({'Tiến bộ' if diff_dt >= 0 else 'Cần lưu ý'})"
            },
            {
                "Chỉ số thống kê nhóm EQ": "Tỉ lệ nhóm CẦN CẢI THIỆN (2.0 <= PEQ < 3.2)",
                "Kỳ 1 (Tháng 6)": f"{pct_ct1}%",
                "Kỳ 2 (Tháng 7)": f"{pct_ct2}%",
                "Thay đổi": f"{'+' if diff_ct > 0 else ''}{diff_ct}%"
            },
            {
                "Chỉ số thống kê nhóm EQ": "Tỉ lệ nhóm HỖ TRỢ ĐẶC BIỆT (PEQ < 2.0)",
                "Kỳ 1 (Tháng 6)": f"{pct_ht1}%",
                "Kỳ 2 (Tháng 7)": f"{pct_ht2}%",
                "Thay đổi": f"{'+' if diff_ht > 0 else ''}{diff_ht}% ({'Tốt (Giảm)' if diff_ht <= 0 else 'Tăng (Cần lưu ý)'})"
            }
        ]
        return pd.DataFrame(stats_data)

    # =========================================================================
    # VAI TRÒ 1: ADMIN TỔNG (SUPER ADMIN)
    # =========================================================================
    if role == "super_admin":
        main_menu = st.sidebar.radio(
            "DANH MỤC SUPER ADMIN:",
            [
                "👑 1. Tạo & Quản lý Tài khoản BGH Cơ Sở",
                "📊 2. Báo cáo EQ Toàn Hệ Thống",
                "📈 3. Bảng So Sánh & Xác Nhận Xu Hướng EQ",
                "📝 4. Nhật ký Cảm xúc Toàn Hệ Thống"
            ]
        )
        
        if main_menu == "👑 1. Tạo & Quản lý Tài khoản BGH Cơ Sở":
            st.subheader("👑 TẠO & QUẢN LÝ TÀI KHOẢN BGH CƠ SỞ")
            st.info("💡 **Phân quyền:** Admin Tổng chịu trách nhiệm tạo và quản lý tài khoản cho **Ban Giám Hiệu 5 Cơ sở**. BGH mỗi cơ sở sẽ tự tạo và quản lý tài khoản Giáo viên thuộc cơ sở đó.")
            
            tab_acc1, tab_acc2 = st.tabs(["➕ Tạo Tài Khoản BGH Mới", "📋 Danh Sách Tài Khoản Toàn Trường (Khóa / Xóa)"])
            
            with tab_acc1:
                st.markdown("##### ➕ Tạo Tài khoản Ban Giám Hiệu Cơ sở mới")
                c1, c2 = st.columns(2)
                with c1: 
                    BGH_code = st.selectbox("Chọn Cơ sở quản lý:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}", key="BGH_c")
                with c2: 
                    BGH_name = st.text_input("Tên đại diện BGH:", value=f"BGH {CAMPUS_MAP[BGH_code]}").strip()
                
                BGH_u = st.text_input("Tên đăng nhập BGH (Ví dụ: BGHHD, BGHHL...):", value=f"BGH{BGH_code}").strip()
                BGH_p = st.text_input("Mật khẩu BGH:", value="123456")
                
                if st.button("➕ Tạo Tài Khoản BGH Cơ Sở"):
                    if bgh_u in st.session_state.users:
                        st.warning(f"⚠️ Tên đăng nhập `{BGH_u}` đã tồn tại!")
                    else:
                        st.session_state.users[BGH_u] = {
                            "password": BGH_p, "name": BGH_name, "role": "campus_admin",
                            "campus_code": BGH_code, "campus": CAMPUS_MAP[BGH_code], "status": "active"
                        }
                        st.success(f"🎉 Đã tạo thành công! Tên TK BGH: `{BGH_u}` | Mật khẩu: `{BGH_p}`")

            with tab_acc2:
                st.markdown("##### 📋 Quản lý trạng thái & Xóa tài khoản hệ thống")
                
                for u_id, u_data in list(st.session_state.users.items()):
                    if u_id == "admin":
                        continue
                    
                    col_u1, col_u2, col_u3, col_u4, col_u5 = st.columns([1.5, 1.5, 2, 1.2, 1.8])
                    status_text = "🟢 Hoạt động" if u_data.get("status", "active") == "active" else "🔴 Đã khóa"
                    role_text = "BGH Cơ sở" if u_data.get("role") == "campus_admin" else "Giáo viên"
                    
                    with col_u1:
                        st.write(f"**TK:** `{u_id}`")
                    with col_u2:
                        st.write(f"**Tên:** {u_data.get('name')}\n*({role_text})*")
                    with col_u3:
                        st.write(f"**Cơ sở:** {u_data.get('campus_code', 'ALL')}")
                    with col_u4:
                        st.write(f"**Trạng thái:** {status_text}")
                    with col_u5:
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if u_data.get("status", "active") == "active":
                                if st.button("🔒 Khóa", key=f"lock_{u_id}"):
                                    st.session_state.users[u_id]["status"] = "inactive"
                                    st.success(f"Đã khóa TK `{u_id}`")
                                    st.rerun()
                            else:
                                if st.button("🔓 Mở", key=f"unlock_{u_id}"):
                                    st.session_state.users[u_id]["status"] = "active"
                                    st.success(f"Đã mở khóa TK `{u_id}`")
                                    st.rerun()
                        with btn_c2:
                            if st.button("🗑️ Xóa", key=f"del_{u_id}"):
                                del st.session_state.users[u_id]
                                if u_id in st.session_state.students_db:
                                    del st.session_state.students_db[u_id]
                                st.warning(f"Đã xóa tài khoản `{u_id}`")
                                st.rerun()
                    st.markdown("---")

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP & PHÂN TÍCH XU HƯỚNG EQ TOÀN HỆ THỐNG")
            sel_c = st.selectbox("Lọc Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()))
            evals = st.session_state.evaluations_db
            if sel_c != "Tất cả cơ sở": evals = [e for e in evals if e.get('Campus') == sel_c]
            
            if evals:
                df_all = prepare_eq_report_df(evals)
                st.dataframe(df_all, use_container_width=True)
                csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel / CSV Báo Cáo EQ Chuẩn Mẫu", csv_data, "Bao_Cao_EQ_Chuanti_TFA.csv", "text/csv")
            else: st.info("Chưa có dữ liệu đánh giá EQ nào.")

        elif main_menu == "📈 3. Bảng So Sánh & Xác Nhận Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XÁC NHẬN XU HƯỚNG PHÁT TRIỂN EQ CỦA TRẺ (GIỮA 2 KỲ/THÁNG)")
            sel_c = st.selectbox("Lọc Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()), key="comp_c")
            comps = st.session_state.comparisons_db
            evals = st.session_state.evaluations_db
            
            if sel_c != "Tất cả cơ sở":
                comps = [c for c in comps if c.get('Campus') == sel_c]
                evals = [e for e in evals if e.get('Campus') == sel_c]
                
            tab_c1, tab_c2 = st.tabs(["📋 Bảng So Sánh Xu Hướng Từng Học Sinh", "📊 Thống Kê Phân Tích Tổng Hợp Toàn Lớp"])
            
            with tab_c1:
                if comps:
                    df_comp = prepare_comparison_df(comps)
                    st.dataframe(df_comp, use_container_width=True)
                    csv_comp = df_comp.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất File Excel/CSV Bảng So Sánh Xu Hướng Của Trẻ", csv_comp, "Bang_So_Sanh_Xu_Huong_EQ_TFA.csv", "text/csv")
                else:
                    st.info("Chưa có dữ liệu bảng so sánh xu hướng. (Giáo viên từng lớp sẽ tạo bảng so sánh ở giao diện Giáo viên).")

            with tab_c2:
                eval_t1 = [e for e in evals if "Kỳ 1" in e.get("Term", "") or "Tháng 6" in e.get("Term", "")]
                eval_t2 = [e for e in evals if "Kỳ 2" in e.get("Term", "") or "Tháng 7" in e.get("Term", "")]
                
                st.markdown("##### 📊 Thông tin phân tích tổng hợp tỉ lệ các nhóm EQ giữa 2 kỳ")
                df_stats = compute_summary_stats(eval_t1, eval_t2)
                st.table(df_stats)
                csv_stats = df_stats.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel/CSV Thống Kê Phân Tích Tỉ Lệ EQ Toàn Lớp", csv_stats, "Thong_Ke_Ti_Le_Nhom_EQ_TFA.csv", "text/csv")

        else:
            st.subheader("📝 NHẬT KÝ CẢM XÚC HẰNG NGÀY TOÀN HỆ THỐNG")
            sel_c = st.selectbox("Lọc Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()), key="log_c")
            logs = st.session_state.daily_logs_db
            if sel_c != "Tất cả cơ sở": logs = [l for l in logs if l.get('Campus') == sel_c]
            if logs:
                df_l = prepare_daily_log_df(logs)
                st.dataframe(df_l, use_container_width=True)
                csv_l = df_l.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel / CSV Nhật Ký Chuẩn Mẫu", csv_l, "Nhat_Ky_Cam_Xuc_TFA.csv", "text/csv")
            else: st.info("Chưa có dữ liệu nhật ký hằng ngày.")

    # =========================================================================
    # VAI TRÒ 2: BGH TỪNG CƠ SỞ (CAMPUS ADMIN)
    # =========================================================================
    elif role == "campus_admin":
        my_campus = user_info['campus']
        my_code = user_info['campus_code']
        
        main_menu = st.sidebar.radio(
            f"DANH MỤC BGH ({my_code}):",
            [
                f"🏫 1. Tạo Giáo viên & Quản lý ({my_code})",
                f"📊 2. Báo cáo EQ Cơ sở ({my_code})",
                f"📈 3. Bảng So Sánh Xu Hướng EQ ({my_code})",
                f"📝 4. Nhật ký Cảm xúc Cơ sở ({my_code})"
            ]
        )
        
        if main_menu == f"🏫 1. Tạo Giáo viên & Quản lý ({my_code})":
            st.subheader(f"🏫 BGH QUẢN LÝ VÀ TẠO TÀI KHOẢN GIÁO VIÊN: {my_campus.upper()}")
            st.info(f"💡 **Quy tắc tạo tài khoản Giáo viên:** Nhập **Số điện thoại** của cô. Tên đăng nhập sẽ tự động ghép thành **`SĐT + Mã Cơ sở`** (ví dụ: `0900000000{my_code}`) với Mật khẩu mặc định là `123456`.")
            
            st.markdown("##### ➕ Tạo tài khoản Giáo viên mới")
            col1, col2 = st.columns(2)
            with col1: t_phone = st.text_input("Số điện thoại Giáo viên (VD: 0912345678):").strip()
            with col2: t_name = st.text_input("Họ và tên Giáo viên:").strip()
            
            if st.button("➕ Tạo Tài Khoản Giáo Viên"):
                if t_phone and t_name:
                    gen_u = f"{t_phone}{my_code}"
                    if gen_u in st.session_state.users:
                        st.warning(f"⚠️ Tài khoản `{gen_u}` đã tồn tại trên hệ thống!")
                    else:
                        st.session_state.users[gen_u] = {
                            "password": "123456", "name": t_name, "role": "teacher",
                            "campus_code": my_code, "campus": my_campus, 
                            "class_name": "Chưa tạo lớp", "status": "active"
                        }
                        st.session_state.students_db[gen_u] = []
                        st.success(f"🎉 Tạo thành công! Tên Tài khoản: `{gen_u}` | Mật khẩu: `123456`")
                else: st.error("Vui lòng điền đủ SĐT và Họ tên Giáo viên!")

            st.markdown("---")
            st.markdown(f"##### 📋 Danh sách & Quản lý Giáo viên thuộc {my_campus}")
            
            has_teacher = False
            for u_id, u_data in list(st.session_state.users.items()):
                if u_data.get("role") == "teacher" and u_data.get("campus_code") == my_code:
                    has_teacher = True
                    col_u1, col_u2, col_u3, col_u4 = st.columns([1.5, 1.5, 1.5, 1.5])
                    status_text = "🟢 Hoạt động" if u_data.get("status", "active") == "active" else "🔴 Đã khóa"
                    
                    with col_u1:
                        st.write(f"**TK:** `{u_id}` | Pass: `{u_data.get('password')}`")
                    with col_u2:
                        st.write(f"**GV:** {u_data.get('name')}")
                    with col_u3:
                        st.write(f"**Lớp:** {u_data.get('class_name', 'Chưa tạo')}")
                    with col_u4:
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if u_data.get("status", "active") == "active":
                                if st.button("🔒 Khóa", key=f"lock_c_{u_id}"):
                                    st.session_state.users[u_id]["status"] = "inactive"
                                    st.success(f"Đã khóa TK `{u_id}`")
                                    st.rerun()
                            else:
                                if st.button("🔓 Mở", key=f"unlock_c_{u_id}"):
                                    st.session_state.users[u_id]["status"] = "active"
                                    st.success(f"Đã mở khóa TK `{u_id}`")
                                    st.rerun()
                        with btn_c2:
                            if st.button("🗑️ Xóa", key=f"del_c_{u_id}"):
                                del st.session_state.users[u_id]
                                if u_id in st.session_state.students_db:
                                    del st.session_state.students_db[u_id]
                                st.warning(f"Đã xóa tài khoản `{u_id}`")
                                st.rerun()
                    st.markdown("---")
                    
            if not has_teacher:
                st.info("Cơ sở chưa có tài khoản giáo viên nào được tạo.")

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            st.subheader(f"📊 BÁO CÁO TỔNG HỢP & PHÂN TÍCH XU HƯỚNG EQ - {my_campus.upper()}")
            campus_evals = [e for e in st.session_state.evaluations_db if e.get('Campus') == my_campus]
            
            if campus_evals:
                df_c = prepare_eq_report_df(campus_evals)
                st.dataframe(df_c, use_container_width=True)
                csv_c = df_c.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label=f"📥 Xuất Báo Cáo EQ {my_code} (Chuẩn Mẫu File)", data=csv_c, file_name=f"Bao_Cao_EQ_{my_code}_Chuanti.csv", mime="text/csv")
            else: st.info(f"Chưa có dữ liệu đánh giá EQ nào thuộc {my_campus}.")

        elif main_menu == f"📈 3. Bảng So Sánh Xu Hướng EQ ({my_code})":
            st.subheader(f"📈 BẢNG SO SÁNH & XÁC NHẬN XU HƯỚNG EQ - {my_campus.upper()}")
            campus_comps = [c for c in st.session_state.comparisons_db if c.get('Campus') == my_campus]
            campus_evals = [e for e in st.session_state.evaluations_db if e.get('Campus') == my_campus]
            
            tab_c1, tab_c2 = st.tabs(["📋 Bảng So Sánh Xu Hướng Từng Học Sinh", "📊 Thống Kê Phân Tích Tổng Hợp Cơ Sở"])
            with tab_c1:
                if campus_comps:
                    df_comp = prepare_comparison_df(campus_comps)
                    st.dataframe(df_comp, use_container_width=True)
                    csv_comp = df_comp.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất File Excel/CSV Bảng So Sánh Xu Hướng EQ Cơ Sở", csv_comp, f"Bang_So_Sanh_Xu_Huong_{my_code}.csv", "text/csv")
                else: st.info("Chưa có dữ liệu so sánh xu hướng nào thuộc cơ sở.")

            with tab_c2:
                eval_t1 = [e for e in campus_evals if "Kỳ 1" in e.get("Term", "") or "Tháng 6" in e.get("Term", "")]
                eval_t2 = [e for e in campus_evals if "Kỳ 2" in e.get("Term", "") or "Tháng 7" in e.get("Term", "")]
                
                st.markdown("##### 📊 Thông tin phân tích tổng hợp tỉ lệ các nhóm EQ giữa 2 kỳ")
                df_stats = compute_summary_stats(eval_t1, eval_t2)
                st.table(df_stats)
                csv_stats = df_stats.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel/CSV Thống Kê Phân Tích Tỉ Lệ EQ Cơ Sở", csv_stats, f"Thong_Ke_Ti_Le_Nhom_EQ_{my_code}.csv", "text/csv")

        else:
            st.subheader(f"📝 NHẬT KÝ CẢM XÚC - {my_campus.upper()}")
            campus_logs = [l for l in st.session_state.daily_logs_db if l.get('Campus') == my_campus]
            
            if campus_logs:
                df_cl = prepare_daily_log_df(campus_logs)
                st.dataframe(df_cl, use_container_width=True)
                csv_cl = df_cl.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label=f"📥 Xuất Nhật Ký Cảm Xúc {my_code} (Chuẩn Mẫu File)", data=csv_cl, file_name=f"Nhat_Ky_Cam_Xuc_{my_code}.csv", mime="text/csv")
            else: st.info(f"Chưa có nhật ký cảm xúc nào thuộc {my_campus}.")

    # =========================================================================
    # VAI TRÒ 3: GIÁO VIÊN TỪNG LỚP
    # =========================================================================
    else:
        main_menu = st.sidebar.radio(
            "DANH MỤC GIÁO VIÊN:",
            [
                "🏫 1. Tạo Lớp & Quản lý Học sinh", 
                "📝 2. Nhật ký Cảm xúc Hằng ngày", 
                "🎯 3. Đánh giá EQ 6 Tiêu chí",
                "📈 4. Bảng So Sánh & Xác Nhận Xu Hướng EQ", 
                "📊 5. Báo cáo & Xuất File Lớp"
            ]
        )

        if main_menu == "🏫 1. Tạo Lớp & Quản lý Học sinh":
            st.subheader("🏫 TỰ TẠO LỚP HỌC & QUẢN LÝ HỌC SINH")
            st.write(f"**Cơ sở phụ trách:** {user_info['campus']}")
            
            st.markdown("---")
            col_l1, col_l2 = st.columns(2)
            with col_l1: sel_class_type = st.selectbox("Chọn Khối lớp:", TFA_CLASSES)
            with col_l2: custom_class_name = st.text_input("Tên riêng của Lớp (VD: Toddler 1A, Kindergarten 2):", value=user_info.get("class_name", sel_class_type))
                
            if st.button("💾 Cập Nhật Tên Lớp"):
                st.session_state.users[user_key]["class_name"] = custom_class_name
                st.success(f"🎉 Đã cập nhật tên lớp: **{custom_class_name}** ({user_info['campus']})")
                st.rerun()

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("##### ➕ Thêm Học sinh mới")
                new_student = st.text_input("Họ và tên học sinh mới:").strip()
                if st.button("Thêm Học Sinh"):
                    if new_student:
                        st.session_state.students_db[user_key].append(new_student)
                        st.success(f"Đã thêm bé **{new_student}** vào lớp!")
                        st.rerun()
                    else: st.warning("Vui lòng nhập tên học sinh!")

            with col_b:
                st.markdown(f"##### 📋 Danh sách Học sinh hiện tại ({user_info.get('class_name')})")
                students = st.session_state.students_db.get(user_key, [])
                if students:
                    for idx, s in enumerate(students, 1): st.write(f"{idx}. **{s}**")
                else: st.info("Lớp chưa có học sinh nào.")

        elif main_menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
            st.subheader(f"📝 NHẬT KÝ CẢM XÚC HẰNG NGÀY - LỚP {user_info.get('class_name').upper()}")
            students = st.session_state.students_db.get(user_key, [])
            
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Tạo Lớp & Quản lý Học sinh' để thêm bé!")
            else:
                col_s1, col_s2 = st.columns(2)
                with col_s1: std_select = st.selectbox("Chọn học sinh:", students)
                with col_s2: log_date = st.date_input("Ngày theo dõi:")
                
                routine_sel = st.selectbox("Hoạt động trong ngày:", TFA_ROUTINES)
                emotions = st.multiselect("Cảm xúc nổi bật trong ngày:", ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng / Chán nản 😮‍💨", "Tự hào 🌟"])
                
                note = st.text_area("1. Bối cảnh & biểu hiện nổi bật:", placeholder="Ví dụ: Bé khóc khi chia tay mẹ, dậm chân khi bạn giành đồ chơi...")
                intervention = st.text_area("2. Can thiệp & hỗ trợ của giáo viên:", placeholder="Ví dụ: Ôm vỗ về, gợi ý bé vào góc bình tĩnh, dùng thẻ hình cảm xúc...")
                summary_note = st.text_input("3. Đánh giá / Nhận xét ngắn cuối ngày:", placeholder="Ví dụ: Tốt, biết gọi tên cảm xúc sau khi được cô hỗ trợ...")
                
                if st.button("💾 Lưu Nhật Ký Ngày"):
                    st.session_state.daily_logs_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_select,
                        "Date": str(log_date), "Routine": routine_sel,
                        "Emotions": ", ".join(emotions), "Note": note,
                        "Intervention": intervention, "Summary": summary_note
                    })
                    st.success(f"🎉 Đã lưu nhật ký cho bé **{std_select}** chuẩn mẫu!")

        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader(f"🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ - LỚP {user_info.get('class_name').upper()}")
            students = st.session_state.students_db.get(user_key, [])
            
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Tạo Lớp & Quản lý Học sinh' để thêm bé!")
            else:
                col_e1, col_e2 = st.columns(2)
                with col_e1: std_eval = st.selectbox("Chọn học sinh đánh giá:", students)
                with col_e2: term = st.selectbox("Chọn Kỳ đánh giá:", ["Tháng 6 / Kỳ 1", "Tháng 7 / Kỳ 2"])
                
                st.markdown("##### 📐 Chấm điểm 6 Tiêu chí (Thang Mức 1 - Mức 4)")
                c1, c2 = st.columns(2)
                with c1:
                    tc1 = st.slider("TC1: Nhận biết cảm xúc bản thân", 1, 4, 2)
                    tc2 = st.slider("TC2: Gọi tên và diễn đạt cảm xúc", 1, 4, 2)
                    tc3 = st.slider("TC3: Điều chỉnh & kiểm soát cảm xúc", 1, 4, 2)
                with c2:
                    tc4 = st.slider("TC4: Đồng cảm & quan hệ xã hội", 1, 4, 2)
                    tc5 = st.slider("TC5: Ảnh hưởng môi trường đến cảm xúc", 1, 4, 3)
                    tc6 = st.slider("TC6: Phản ứng khi cảm xúc được công nhận", 1, 4, 3)
                    
                peq = round((tc1 + tc2 + tc3 + tc4 + tc5 + tc6) / 6.0, 2)
                if peq >= 3.2: 
                    group = "🟢 Nhóm Duy trì"
                    group_clean = "DUY TRÌ"
                elif peq >= 2.0: 
                    group = "🟠 Nhóm Cần cải thiện"
                    group_clean = "CẦN CẢI THIỆN"
                else: 
                    group = "🔴 Nhóm HỖ TRỢ ĐẶC BIỆT"
                    group_clean = "HỖ TRỢ ĐẶC BIỆT"
                    
                st.metric("Điểm EQ Tổng hợp (PEQ):", peq, delta=group)
                
                st.markdown("##### 📝 Chi tiết nhận định chuẩn file báo cáo nguồn")
                context_input = st.text_area("Bối cảnh / Minh chứng điển hình (Hành vi cụ thể):", value=f"{std_eval} thường có biểu hiện...")
                conclusion_input = st.text_area("Kết luận xu hướng:", value=f"Xu hướng cảm xúc của {std_eval}...")
                plan_input = st.text_area("Kế hoạch tác động tiếp theo:", value=f"Tập trung hướng dẫn {std_eval}...")
                
                if st.button("💾 Lưu Kết Quả Đánh Giá Chuẩn Mẫu"):
                    st.session_state.evaluations_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_eval, "Term": term,
                        "TC1": tc1, "TC2": tc2, "TC3": tc3, "TC4": tc4, "TC5": tc5, "TC6": tc6,
                        "P_EQ": peq, "Group": group, "Group_Clean": group_clean,
                        "Context": context_input, "Conclusion": conclusion_input, "Plan": plan_input
                    })
                    st.success(f"🎉 Đã lưu đánh giá EQ chuẩn mẫu file nguồn cho bé **{std_eval}**!")

        elif main_menu == "📈 4. Bảng So Sánh & Xác Nhận Xu Hướng EQ":
            st.subheader(f"📈 BẢNG SO SÁNH & XÁC NHẬN XU HƯỚNG EQ - LỚP {user_info.get('class_name').upper()}")
            students = st.session_state.students_db.get(user_key, [])
            
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Tạo Lớp & Quản lý Học sinh' để thêm bé!")
            else:
                st.markdown("##### ➕ Tạo/Cập nhật nhận định so sánh xu hướng 2 tháng (Kỳ 1 vs Kỳ 2)")
                col_cmp1, col_cmp2 = st.columns(2)
                with col_cmp1:
                    std_comp = st.selectbox("Chọn học sinh so sánh:", students, key="std_cmp")
                    score_t1 = st.number_input("Điểm Kỳ 1 (Tháng 6):", min_value=1.0, max_value=4.0, value=2.2, step=0.1)
                with col_cmp2:
                    score_t2 = st.number_input("Điểm Kỳ 2 (Tháng 7):", min_value=1.0, max_value=4.0, value=3.0, step=0.1)
                    
                delta_score = round(score_t2 - score_t1, 2)
                if delta_score >= 0.5:
                    trend_tag = "TIẾN BỘ VƯỢT BẬC"
                elif delta_score > 0:
                    trend_tag = "TIẾN BỘ"
                elif delta_score == 0:
                    trend_tag = "DUY TRÌ ÔN ĐỊNH"
                else:
                    trend_tag = "CẦN LƯU Ý (THỤT LÙI)"
                    
                st.metric("Biến thiên điểm (Delta):", delta_score, delta=trend_tag)
                
                c_input = st.text_area("Kết luận xu hướng:", value=f"Bé {std_comp} có xu hướng {trend_tag.lower()}...")
                p_input = st.text_area("Kế hoạch tác động tiếp theo:", value=f"Tiếp tục hỗ trợ bé {std_comp}...")
                
                if st.button("💾 Lưu Bảng So Sánh Xu Hướng"):
                    st.session_state.comparisons_db = [c for c in st.session_state.comparisons_db if not (c['Teacher'] == user_info['name'] and c['Student'] == std_comp)]
                    st.session_state.comparisons_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_comp,
                        "Score_Term1": score_t1, "Score_Term2": score_t2,
                        "Delta": delta_score, "Trend": trend_tag,
                        "Conclusion": c_input, "Plan": p_input
                    })
                    st.success(f"🎉 Đã lưu bảng so sánh xu hướng cho bé **{std_comp}**!")

                st.markdown("---")
                st.markdown("##### 📋 Bảng So Sánh Xu Hướng Toàn Lớp (Tháng 6 vs Tháng 7)")
                my_comps = [c for c in st.session_state.comparisons_db if c['Teacher'] == user_info['name']]
                
                if my_comps:
                    df_my_comp = prepare_comparison_df(my_comps)
                    st.dataframe(df_my_comp, use_container_width=True)
                    csv_my_comp = df_my_comp.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất File Excel/CSV Bảng So Sánh Xu Hướng Lớp", csv_my_comp, f"Bang_So_Sanh_Xu_Huong_{user_info['class_name']}.csv", "text/csv")

                st.markdown("---")
                st.markdown("##### 📊 Thông tin phân tích tổng hợp tỉ lệ nhóm EQ toàn lớp")
                my_evals_t1 = [e for e in st.session_state.evaluations_db if e['Teacher'] == user_info['name'] and ("Kỳ 1" in e.get("Term", "") or "Tháng 6" in e.get("Term", ""))]
                my_evals_t2 = [e for e in st.session_state.evaluations_db if e['Teacher'] == user_info['name'] and ("Kỳ 2" in e.get("Term", "") or "Tháng 7" in e.get("Term", ""))]
                df_my_stats = compute_summary_stats(my_evals_t1, my_evals_t2)
                st.table(df_my_stats)
                csv_my_stats = df_my_stats.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel/CSV Thống Kê Phân Tích Tỉ Lệ EQ Lớp", csv_my_stats, f"Thong_Ke_Ti_Le_Nhom_EQ_{user_info['class_name']}.csv", "text/csv")

        else:
            st.subheader(f"📊 BÁO CÁO & XUẤT FILE LỚP {user_info.get('class_name').upper()}")
            my_evals = [e for e in st.session_state.evaluations_db if e['Teacher'] == user_info['name']]
            my_logs = [l for l in st.session_state.daily_logs_db if l['Teacher'] == user_info['name']]
            my_comps = [c for c in st.session_state.comparisons_db if c['Teacher'] == user_info['name']]
            
            tab_r1, tab_r2, tab_r3 = st.tabs(["🎯 Báo cáo EQ Lớp Chuẩn Mẫu", "📈 Bảng So Sánh Xu Hướng EQ", "📝 Nhật ký Cảm xúc Lớp"])
            
            with tab_r1:
                if my_evals:
                    df_eval = prepare_eq_report_df(my_evals)
                    st.dataframe(df_eval, use_container_width=True)
                    csv_eval = df_eval.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất File Excel / CSV Báo Cáo EQ Chuẩn Mẫu", csv_eval, f"Bao_Cao_EQ_{user_info['class_name']}_Chuanti.csv", "text/csv")
                else: st.info("Chưa có dữ liệu đánh giá EQ nào.")

            with tab_r2:
                if my_comps:
                    df_comp = prepare_comparison_df(my_comps)
                    st.dataframe(df_comp, use_container_width=True)
                    csv_comp = df_comp.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất File Excel/CSV Bảng So Sánh Xu Hướng", csv_comp, f"Bang_So_Sanh_Xu_Huong_{user_info['class_name']}.csv", "text/csv")
                else: st.info("Chưa có dữ liệu so sánh xu hướng.")

            with tab_r3:
                if my_logs:
                    df_logs = prepare_daily_log_df(my_logs)
                    st.dataframe(df_logs, use_container_width=True)
                    csv_logs = df_logs.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất Nhật Ký Lớp Chuẩn Mẫu (CSV/Excel)", csv_logs, f"Nhat_Ky_{user_info['class_name']}.csv", "text/csv")
                else: st.info("Chưa có nhật ký cảm xúc nào.")
