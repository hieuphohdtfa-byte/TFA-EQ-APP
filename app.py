import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

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
# 2. KHỞI TẠO MÃ CƠ SỞ & KHỐI LỚP CHUẨN
# -----------------------------------------------------------------------------
CAMPUS_MAP = {
    "HD": "Cơ sở TFA Hà Đô (Cát Lái, TP.HCM)",
    "TTL": "Cơ sở TFA Trần Thị Lý (Đà Nẵng)",
    "DBM": "Cơ sở TFA Dương Bạch Mai (Quận 8, TP.HCM)",
    "HL": "Cơ sở TFA Him Lam (Quận 7, TP.HCM)",
    "LVS": "Cơ sở TFA Lê Văn Sỹ (Quận 3, TP.HCM)"
}

TFA_CLASSES = ["Toddler 1", "Toddler 2", "Pre-school", "Kindergarten", "Pre-primary"]
TFA_ROUTINES = [
    "Đón trẻ - Thể dục sáng", "Ăn sáng", "Hoạt động có chủ đích",
    "Ăn trưa", "Ăn xế", "Hoạt động chiều", "Trả trẻ", "Tình huống phát sinh"
]
MONTH_OPTIONS = ["Tất cả các tháng"] + [f"Tháng {m}" for m in range(1, 13)]
LOGO_FILE = "logo.png" if os.path.exists("logo.png") else ("Logo TFA Ver2.1 .png" if os.path.exists("Logo TFA Ver2.1 .png") else "logo.png")
DB_FILE = "tfa_database.json"

# -----------------------------------------------------------------------------
# 3. MÔ-ĐỦN TỰ ĐỘNG LƯU VÀ ĐỌC DỮ LIỆU VĨNH VIỄN (FILE DB)
# -----------------------------------------------------------------------------
DEFAULT_USERS = {
    "admin": {
        "password": "admin123", "name": "Ban Giám Hiệu Tổng (Toàn Hệ Thống)",
        "role": "super_admin", "campus_code": "ALL", "campus": "Tất cả cơ sở", "status": "active"
    },
    "BGHHD": {
        "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin",
        "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "status": "active"
    },
    "BGHHL": {
        "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin",
        "campus_code": "HL", "campus": CAMPUS_MAP["HL"], "status": "active"
    },
    "BGHDBM": {
        "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin",
        "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"], "status": "active"
    },
    "BGHLVS": {
        "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin",
        "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"], "status": "active"
    },
        "BGHTTL": {
        "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin",
        "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"], "status": "active"
    }
}

def load_persistent_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_persistent_db():
    db_data = {
        "users": st.session_state.users,
        "students_db": st.session_state.students_db,
        "evaluations_db": st.session_state.evaluations_db,
        "daily_logs_db": st.session_state.daily_logs_db,
        "comparisons_db": st.session_state.comparisons_db
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

db_loaded = load_persistent_db()

if 'users' not in st.session_state:
    st.session_state.users = db_loaded.get("users", DEFAULT_USERS) if db_loaded else DEFAULT_USERS

if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

if 'students_db' not in st.session_state:
    st.session_state.students_db = db_loaded.get("students_db", {}) if db_loaded else {}

if 'evaluations_db' not in st.session_state:
    st.session_state.evaluations_db = db_loaded.get("evaluations_db", []) if db_loaded else []

if 'daily_logs_db' not in st.session_state:
    st.session_state.daily_logs_db = db_loaded.get("daily_logs_db", []) if db_loaded else []

if 'comparisons_db' not in st.session_state:
    st.session_state.comparisons_db = db_loaded.get("comparisons_db", []) if db_loaded else []

# -----------------------------------------------------------------------------
# 4. HÀM HỖ TRỢ LỌC DỮ LIỆU THEO THÁNG & VẼ BIỂU ĐỒ
# -----------------------------------------------------------------------------
def filter_logs_by_month(logs, selected_month):
    if not logs or selected_month == "Tất cả các tháng":
        return logs
    try:
        month_num = int(selected_month.replace("Tháng ", ""))
        filtered = []
        for l in logs:
            date_str = l.get("Date", "")
            if date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                if dt.month == month_num:
                    filtered.append(l)
        return filtered
    except Exception:
        return logs

def filter_evals_by_month(evals, selected_month):
    if not evals or selected_month == "Tất cả các tháng":
        return evals
    filtered = []
    for e in evals:
        term_str = str(e.get("Term", ""))
        if selected_month in term_str:
            filtered.append(e)
        else:
            m_num = selected_month.replace("Tháng ", "")
            if f"Tháng {m_num}" in term_str or f"Kỳ {m_num}" in term_str:
                filtered.append(e)
    return filtered

def render_eq_charts(eval_list, title_prefix=""):
    if not eval_list:
        st.info("Chưa có đủ dữ liệu để vẽ biểu đồ trực quan.")
        return
    
    st.markdown(f"#### 📊 BIỂU ĐỒ TRỰC QUAN PHÂN TÍCH CẢM XÚC EQ {title_prefix.upper()}")
    col_chart1, col_chart2 = st.columns(2)
    
    groups = [e.get("Group_Clean", "DUY TRÌ") for e in eval_list]
    df_g = pd.DataFrame({"Group": groups})
    counts = df_g["Group"].value_counts().reset_index()
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
    avg_scores = []
    for k in tc_keys:
        vals = [e.get(k, 0) for e in eval_list if k in e]
        avg_scores.append(round(sum(vals)/len(vals), 2) if vals else 0)
        
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

def render_comparison_charts(comp_list, title_prefix=""):
    if not comp_list:
        st.info("Chưa có dữ liệu so sánh xu hướng để vẽ biểu đồ.")
        return
        
    st.markdown(f"#### 📈 BIỂU ĐỒ TRỰC QUAN XU HƯỚNG PHÁT TRIỂN EQ {title_prefix.upper()}")
    col_chart1, col_chart2 = st.columns(2)
    df_comp = pd.DataFrame(comp_list)
    
    with col_chart1:
        fig_group = go.Figure()
        fig_group.add_trace(go.Bar(x=df_comp["Student"], y=df_comp["Score_Term1"], name="Đợt 1", marker_color="#FFC107"))
        fig_group.add_trace(go.Bar(x=df_comp["Student"], y=df_comp["Score_Term2"], name="Đợt 2", marker_color="#4CAF50"))
        fig_group.update_layout(
            barmode='group', title="<b>So sánh Điểm EQ giữa 2 Đợt Đánh giá</b>",
            yaxis_range=[0, 4.5], xaxis_title="Học sinh", yaxis_title="Điểm EQ",
            margin=dict(t=40, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_group, use_container_width=True)
        
    trends = df_comp["Trend"].value_counts().reset_index()
    trends.columns = ["Xu hướng", "Số lượng"]
    trend_color_map = {
        "TIẾN BỘ VƯỢT BẬC": "#2E7D32", "TIẾN BỘ": "#4CAF50",
        "DUY TRÌ ÔN ĐỊNH": "#2196F3", "CẦN LƯU Ý (THỤT LÙI)": "#EF5350"
    }
    
    with col_chart2:
        fig_trend = px.bar(
            trends, x="Xu hướng", y="Số lượng", text="Số lượng",
            color="Xu hướng", color_discrete_map=trend_color_map,
            title="<b>Phân bố Xu hướng Phát triển EQ</b>"
        )
        fig_trend.update_traces(textposition='outside')
        fig_trend.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------------------------------------------------------
# 5. HEADER THƯƠNG HIỆU CHÍNH
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
# 6. GIAO DIỆN BÌA NGOÀI / LANDING PAGE (CHƯA ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
if st.session_state.logged_user is None:
    col_left, col_right = st.columns([1.1, 1.9], gap="large")
    
    with col_left:
        st.markdown("""
            <div class="login-card">
                <h3 style="color: #1A1A1A; margin-top: 5px; font-weight: 700;">🔐 ĐĂNG NHẬP HỆ THỐNG</h3>
                <p style="color: #666; font-size: 13px; margin-bottom: 15px;">Dành cho Ban Giám Hiệu & Giáo Viên TFA</p>
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
                <span class="campus-badge">🏢 TFA Hà Đô (Phường Cát Lái, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Dương Bạch Mai (Phường Chánh Hưng, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Him Lam (Phường Tân Hưng, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Trần Thị Lý (Phường Hòa Cường, TP.Đà Nẵng)</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.markdown("#### 🎨 Các Khối Lớp Đào Tạo Chuẩn")
        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1: st.info("👶 **Toddler**\n\n*(Nhóm trẻ từ 12–36 tháng)*")
        with col_k2: st.warning("🌱 **Pre-school & Kindergarten**\n\n*(Khối Lớp 3–5 tuổi)*")
        with col_k3: st.success("🎓 **Pre-primary**\n\n*(Khối Lớp  5–6 tuổi chuẩn bị vào Lớp 1)*")

# -----------------------------------------------------------------------------
# 7. KHÔNG GIAN LÀM VIỆC TRONG APP (SAU KHI ĐĂNG NHẬP)
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
    
    def prepare_eq_report_df(eval_list):
        rows = []
        for idx, item in enumerate(eval_list, 1):
            rows.append({
                "STT": idx, "Tên học sinh": item.get("Student", ""),
                "TC1": item.get("TC1", 0), "TC2": item.get("TC2", 0), "TC3": item.get("TC3", 0),
                "TC4": item.get("TC4", 0), "TC5": item.get("TC5", 0), "TC6": item.get("TC6", 0),
                "Điểm TB (PEQ)": item.get("P_EQ", 0),
                "Nhóm Trạng Thái": item.get("Group_Clean", item.get("Group", "").replace("🟢 ", "").replace("🟠 ", "").replace("🔴 ", "")),
                "Bối cảnh/Minh chứng điển hình": item.get("Context", ""),
                "Kết luận xu hướng": item.get("Conclusion", ""),
                "Kế hoạch tác động": item.get("Plan", ""),
                "Lớp": item.get("Class", ""), "Cơ sở": item.get("Campus", ""),
                "Kỳ đánh giá": item.get("Term", ""), "Giáo viên": item.get("Teacher", "")
            })
        return pd.DataFrame(rows)

    def prepare_daily_log_df(log_list):
        rows = []
        for idx, item in enumerate(log_list, 1):
            rows.append({
                "STT": idx, "Họ và tên trẻ": item.get("Student", ""), "Lớp": item.get("Class", ""),
                "Ngày": item.get("Date", ""), "Hoạt động trong ngày": item.get("Routine", "Tất cả"),
                "Cảm xúc nổi bật": item.get("Emotions", ""), "Bối cảnh & biểu hiện": item.get("Note", ""),
                "Can thiệp & hỗ trợ": item.get("Intervention", ""), "Nhận xét": item.get("Summary", ""),
                "Cơ sở": item.get("Campus", ""), "Giáo viên": item.get("Teacher", "")
            })
        return pd.DataFrame(rows)

    def prepare_comparison_df(comp_list):
        rows = []
        for idx, item in enumerate(comp_list, 1):
            rows.append({
                "STT": idx, "Tên học sinh": item.get("Student", ""),
                "Điểm đợt 1": item.get("Score_Term1", 0.0), "Điểm đợt 2": item.get("Score_Term2", 0.0),
                "Biến thiên": item.get("Delta", 0.0), "Xu hướng EQ": item.get("Trend", ""),
                "Kết luận xu hướng": item.get("Conclusion", ""), "Kế hoạch tác động": item.get("Plan", ""),
                "Lớp": item.get("Class", ""), "Cơ sở": item.get("Campus", ""), "Giáo viên": item.get("Teacher", "")
            })
        return pd.DataFrame(rows)

    # =========================================================================
    # VAI TRÒ 1: ADMIN TỔNG (SUPER ADMIN)
    # =========================================================================
    if role == "super_admin":
        main_menu = st.sidebar.radio(
            "DANH MỤC SUPER ADMIN:",
            ["👑 1. Tạo & Quản lý Tài khoản BGH Cơ Sở", "📊 2. Báo cáo EQ Toàn Hệ Thống", "📈 3. Bảng So Sánh & Xác Nhận Xu Hướng EQ", "📝 4. Nhật ký Cảm xúc Toàn Hệ Thống"]
        )
        
        if main_menu == "👑 1. Tạo & Quản lý Tài khoản BGH Cơ Sở":
            st.subheader("👑 TẠO & QUẢN LÝ TÀI KHOẢN BGH CƠ SỞ")
            tab_acc1, tab_acc2 = st.tabs(["➕ Tạo Tài Khoản BGH Mới", "📋 Danh Sách Tài Khoản Toàn Trường"])
            
            with tab_acc1:
                c1, c2 = st.columns(2)
                with c1: BGH_code = st.selectbox("Chọn Cơ sở quản lý:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}", key="BGH_c")
                with c2: BGH_name = st.text_input("Tên đại diện BGH:", value=f"BGH {CAMPUS_MAP[BGH_code]}").strip()
                BGH_u = st.text_input("Tên đăng nhập BGH:", value=f"BGH{BGH_code}").strip()
                BGH_p = st.text_input("Mật khẩu BGH:", value="123456")
                
                if st.button("➕ Tạo Tài Khoản BGH Cơ Sở"):
                    if bgh_u in st.session_state.users:
                        st.warning(f"⚠️ Tên đăng nhập `{BGH_u}` đã tồn tại!")
                    else:
                        st.session_state.users[BGH_u] = {
                            "password": BGH_p, "name": BGH_name, "role": "campus_admin",
                            "campus_code": BGH_code, "campus": CAMPUS_MAP[BGH_code], "status": "active"
                        }
                        save_persistent_db()
                        st.success(f"🎉 Đã lưu vĩnh viễn! Tên TK BGH: `{BGH_u}` | Mật khẩu: `{BGH_p}`")

            with tab_acc2:
                for u_id, u_data in list(st.session_state.users.items()):
                    if u_id == "admin": continue
                    col_u1, col_u2, col_u3, col_u4, col_u5 = st.columns([1.5, 1.5, 2, 1.2, 1.8])
                    status_text = "🟢 Hoạt động" if u_data.get("status", "active") == "active" else "🔴 Đã khóa"
                    role_text = "BGH Cơ sở" if u_data.get("role") == "campus_admin" else "Giáo viên"
                    
                    with col_u1: st.write(f"**TK:** `{u_id}`")
                    with col_u2: st.write(f"**Tên:** {u_data.get('name')}\n*({role_text})*")
                    with col_u3: st.write(f"**Cơ sở:** {u_data.get('campus_code', 'ALL')}")
                    with col_u4: st.write(f"**Trạng thái:** {status_text}")
                    with col_u5:
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if u_data.get("status", "active") == "active":
                                if st.button("🔒 Khóa", key=f"lock_{u_id}"):
                                    st.session_state.users[u_id]["status"] = "inactive"
                                    save_persistent_db()
                                    st.rerun()
                            else:
                                if st.button("🔓 Mở", key=f"unlock_{u_id}"):
                                    st.session_state.users[u_id]["status"] = "active"
                                    save_persistent_db()
                                    st.rerun()
                        with btn_c2:
                            if st.button("🗑️ Xóa", key=f"del_{u_id}"):
                                del st.session_state.users[u_id]
                                if u_id in st.session_state.students_db: del st.session_state.students_db[u_id]
                                save_persistent_db()
                                st.rerun()
                    st.markdown("---")

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP & PHÂN TÍCH XU HƯỚNG EQ TOÀN HỆ THỐNG")
            col_f1, col_f2 = st.columns(2)
            with col_f1: sel_c = st.selectbox("Lọc Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()))
            with col_f2: sel_m = st.selectbox("🗓️ Lọc theo Tháng / Kỳ:", MONTH_OPTIONS)
            evals = st.session_state.evaluations_db
            if sel_c != "Tất cả cơ sở": evals = [e for e in evals if e.get('Campus') == sel_c]
            evals = filter_evals_by_month(evals, sel_m)
            if evals:
                df_all = prepare_eq_report_df(evals)
                st.dataframe(df_all, use_container_width=True)
                render_eq_charts(evals, f"({sel_c} - {sel_m})")
                st.download_button("Xuất File Excel / CSV Báo Cáo EQ Chuẩn Mẫu", df_all.to_csv(index=False).encode('utf-8-sig'), "Bao_Cao_EQ_TFA.csv", "text/csv")
            else: st.info("Chưa có dữ liệu đánh giá EQ phù hợp bộ lọc.")

        elif main_menu == "📈 3. Bảng So Sánh & Xác Nhận Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XÁC NHẬN XU HƯỚNG PHÁT TRIỂN EQ")
            comps = st.session_state.comparisons_db
            if comps:
                df_comp = prepare_comparison_df(comps)
                st.dataframe(df_comp, use_container_width=True)
                render_comparison_charts(comps, "(Toàn Hệ Thống)")
                st.download_button("Xuất File Excel/CSV Bảng So Sánh", df_comp.to_csv(index=False).encode('utf-8-sig'), "Bang_So_Sanh_EQ_TFA.csv", "text/csv")
            else: st.info("Chưa có dữ liệu so sánh xu hướng.")

        else:
            st.subheader("📝 NHẬT KÝ CẢM XÚC HẰNG NGÀY TOÀN HỆ THỐNG")
            logs = st.session_state.daily_logs_db
            if logs:
                df_l = prepare_daily_log_df(logs)
                st.dataframe(df_l, use_container_width=True)
                st.download_button("Xuất File Excel / CSV Nhật Ký", df_l.to_csv(index=False).encode('utf-8-sig'), "Nhat_Ky_Cam_Xuc_TFA.csv", "text/csv")
            else: st.info("Chưa có nhật ký cảm xúc.")

    # =========================================================================
    # VAI TRÒ 2: BGH TỪNG CƠ SỞ (CAMPUS ADMIN)
    # =========================================================================
    elif role == "campus_admin":
        my_campus = user_info['campus']
        my_code = user_info['campus_code']
        main_menu = st.sidebar.radio(f"DANH MỤC BGH ({my_code}):", [f"🏫 1. Tạo Giáo viên & Quản lý ({my_code})", f"📊 2. Báo cáo EQ Cơ sở ({my_code})", f"📈 3. Bảng So Sánh Xu Hướng EQ ({my_code})", f"📝 4. Nhật ký Cảm xúc Cơ sở ({my_code})"])
        
        if main_menu == f"🏫 1. Tạo Giáo viên & Quản lý ({my_code})":
            st.subheader(f"🏫 BGH QUẢN LÝ VÀ TẠO TÀI KHOẢN GIÁO VIÊN: {my_campus.upper()}")
            col1, col2 = st.columns(2)
            with col1: t_phone = st.text_input("Số điện thoại Giáo viên:").strip()
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
                        save_persistent_db()
                        st.success(f"🎉 Đã lưu vĩnh viễn! Tên Tài khoản Giáo viên: `{gen_u}` | Mật khẩu: `123456`")
                else: st.error("Vui lòng điền đủ SĐT và Họ tên Giáo viên!")

            st.markdown("---")
            for u_id, u_data in list(st.session_state.users.items()):
                if u_data.get("role") == "teacher" and u_data.get("campus_code") == my_code:
                    col_u1, col_u2, col_u3, col_u4 = st.columns([1.5, 1.5, 1.5, 1.5])
                    with col_u1: st.write(f"**TK:** `{u_id}` | Pass: `{u_data.get('password')}`")
                    with col_u2: st.write(f"**GV:** {u_data.get('name')}")
                    with col_u3: st.write(f"**Lớp:** {u_data.get('class_name', 'Chưa tạo')}")
                    with col_u4:
                        if st.button("🗑️ Xóa", key=f"del_c_{u_id}"):
                            del st.session_state.users[u_id]
                            if u_id in st.session_state.students_db: del st.session_state.students_db[u_id]
                            save_persistent_db()
                            st.rerun()

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            campus_evals = [e for e in st.session_state.evaluations_db if e.get('Campus') == my_campus]
            if campus_evals:
                df_c = prepare_eq_report_df(campus_evals)
                st.dataframe(df_c, use_container_width=True)
                render_eq_charts(campus_evals, f"({my_code})")
                st.download_button("Xuất Báo Cáo EQ", df_c.to_csv(index=False).encode('utf-8-sig'), f"Bao_Cao_EQ_{my_code}.csv", "text/csv")
            else: st.info("Chưa có dữ liệu đánh giá EQ thuộc cơ sở.")

        elif main_menu == f"📈 3. Bảng So Sánh Xu Hướng EQ ({my_code})":
            campus_comps = [c for c in st.session_state.comparisons_db if c.get('Campus') == my_campus]
            if campus_comps:
                df_comp = prepare_comparison_df(campus_comps)
                st.dataframe(df_comp, use_container_width=True)
                render_comparison_charts(campus_comps, f"({my_code})")
            else: st.info("Chưa có dữ liệu so sánh xu hướng thuộc cơ sở.")

        else:
            campus_logs = [l for l in st.session_state.daily_logs_db if l.get('Campus') == my_campus]
            if campus_logs:
                df_cl = prepare_daily_log_df(campus_logs)
                st.dataframe(df_cl, use_container_width=True)
            else: st.info("Chưa có nhật ký cảm xúc thuộc cơ sở.")

    # =========================================================================
    # VAI TRÒ 3: GIÁO VIÊN TỪNG LỚP
    # =========================================================================
    else:
        main_menu = st.sidebar.radio("DANH MỤC GIÁO VIÊN:", ["🏫 1. Tạo Lớp & Quản lý Học sinh", "📝 2. Nhật ký Cảm xúc Hằng ngày", "🎯 3. Đánh giá EQ 6 Tiêu chí", "📈 4. Bảng So Sánh & Xác Nhận Xu Hướng EQ", "📊 5. Báo cáo & Xuất File Lớp"])

        if main_menu == "🏫 1. Tạo Lớp & Quản lý Học sinh":
            st.subheader("🏫 TỰ TẠO LỚP HỌC & QUẢN LÝ HỌC SINH")
            col_l1, col_l2 = st.columns(2)
            with col_l1: sel_class_type = st.selectbox("Chọn Khối lớp:", TFA_CLASSES)
            with col_l2: custom_class_name = st.text_input("Tên riêng của Lớp:", value=user_info.get("class_name", sel_class_type))
                
            if st.button("💾 Cập Nhật Tên Lớp"):
                st.session_state.users[user_key]["class_name"] = custom_class_name
                save_persistent_db()
                st.success(f"🎉 Đã lưu tên lớp: **{custom_class_name}**")
                st.rerun()

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                new_student = st.text_input("Họ và tên học sinh mới:").strip()
                if st.button("Thêm Học Sinh"):
                    if new_student:
                        if user_key not in st.session_state.students_db:
                            st.session_state.students_db[user_key] = []
                        st.session_state.students_db[user_key].append(new_student)
                        save_persistent_db()
                        st.success(f"Đã lưu vĩnh viễn bé **{new_student}** vào lớp!")
                        st.rerun()

            with col_b:
                students = st.session_state.students_db.get(user_key, [])
                if students:
                    for idx, s in enumerate(students):
                        c_s1, c_s2, c_s3 = st.columns([2.5, 1, 1])
                        with c_s1: st.write(f"**{idx+1}. {s}**")
                        with c_s2:
                            if st.button("✏️ Sửa", key=f"edit_std_{idx}_{s}"):
                                st.session_state[f"editing_std_{idx}"] = not st.session_state.get(f"editing_std_{idx}", False)
                        with c_s3:
                            if st.button("🗑️ Xóa", key=f"del_std_{idx}_{s}"):
                                st.session_state.students_db[user_key].pop(idx)
                                save_persistent_db()
                                st.rerun()
                        
                        if st.session_state.get(f"editing_std_{idx}", False):
                            with st.form(key=f"form_edit_std_{idx}"):
                                new_name_val = st.text_input("Sửa tên:", value=s)
                                if st.form_submit_button("💾 Lưu thay đổi"):
                                    old_name = st.session_state.students_db[user_key][idx]
                                    st.session_state.students_db[user_key][idx] = new_name_val.strip()
                                    for ev in st.session_state.evaluations_db:
                                        if ev.get("Teacher") == user_info['name'] and ev.get("Student") == old_name: ev["Student"] = new_name_val.strip()
                                    for lg in st.session_state.daily_logs_db:
                                        if lg.get("Teacher") == user_info['name'] and lg.get("Student") == old_name: lg["Student"] = new_name_val.strip()
                                    for cp in st.session_state.comparisons_db:
                                        if cp.get("Teacher") == user_info['name'] and cp.get("Student") == old_name: cp["Student"] = new_name_val.strip()
                                    save_persistent_db()
                                    st.session_state[f"editing_std_{idx}"] = False
                                    st.rerun()
                else: st.info("Lớp chưa có học sinh nào.")

        elif main_menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
            students = st.session_state.students_db.get(user_key, [])
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_s1, col_s2 = st.columns(2)
                with col_s1: std_select = st.selectbox("Chọn học sinh:", students)
                with col_s2: log_date = st.date_input("Ngày theo dõi:")
                routine_sel = st.selectbox("Hoạt động:", TFA_ROUTINES)
                emotions = st.multiselect("Cảm xúc nổi bật:", ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng 😮‍💨"])
                note = st.text_area("1. Bối cảnh & biểu hiện:")
                intervention = st.text_area("2. Can thiệp của giáo viên:")
                summary_note = st.text_input("3. Nhận xét:")
                
                if st.button("💾 Lưu Nhật Ký"):
                    st.session_state.daily_logs_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_select,
                        "Date": str(log_date), "Routine": routine_sel,
                        "Emotions": ", ".join(emotions), "Note": note,
                        "Intervention": intervention, "Summary": summary_note
                    })
                    save_persistent_db()
                    st.success(f"🎉 Đã lưu vĩnh viễn nhật ký cho bé **{std_select}**!")

        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            students = st.session_state.students_db.get(user_key, [])
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_e1, col_e2 = st.columns(2)
                with col_e1: std_eval = st.selectbox("Chọn học sinh:", students)
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
                
                if st.button("💾 Lưu Kết Quả Đánh Giá"):
                    st.session_state.evaluations_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_eval, "Term": term,
                        "TC1": tc1, "TC2": tc2, "TC3": tc3, "TC4": tc4, "TC5": tc5, "TC6": tc6,
                        "P_EQ": peq, "Group_Clean": group_clean,
                        "Context": context_input, "Conclusion": conclusion_input, "Plan": plan_input
                    })
                    save_persistent_db()
                    st.success(f"🎉 Đã lưu vĩnh viễn đánh giá EQ cho bé **{std_eval}**!")

        elif main_menu == "📈 4. Bảng So Sánh & Xác Nhận Xu Hướng EQ":
            students = st.session_state.students_db.get(user_key, [])
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                std_comp = st.selectbox("Chọn học sinh so sánh:", students)
                col_cmp1, col_cmp2 = st.columns(2)
                with col_cmp1: score_t1 = st.number_input("Điểm Đợt 1:", 1.0, 4.0, 2.2, 0.1)
                with col_cmp2: score_t2 = st.number_input("Điểm Đợt 2:", 1.0, 4.0, 3.0, 0.1)
                delta_score = round(score_t2 - score_t1, 2)
                trend_tag = "TIẾN BỘ VƯỢT BẬC" if delta_score >= 0.5 else ("TIẾN BỘ" if delta_score > 0 else ("DUY TRÌ ÔN ĐỊNH" if delta_score == 0 else "CẦN LƯU Ý"))
                
                c_input = st.text_area("Kết luận xu hướng:", value=f"Bé {std_comp} {trend_tag.lower()}...")
                p_input = st.text_area("Kế hoạch tác động:", value=f"Tiếp tục hỗ trợ {std_comp}...")
                
                if st.button("💾 Lưu Bảng So Sánh Xu Hướng"):
                    st.session_state.comparisons_db = [c for c in st.session_state.comparisons_db if not (c['Teacher'] == user_info['name'] and c['Student'] == std_comp)]
                    st.session_state.comparisons_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_comp,
                        "Score_Term1": score_t1, "Score_Term2": score_t2,
                        "Delta": delta_score, "Trend": trend_tag,
                        "Conclusion": c_input, "Plan": p_input
                    })
                    save_persistent_db()
                    st.success(f"🎉 Đã lưu vĩnh viễn bảng so sánh cho bé **{std_comp}**!")

        else:
            my_evals = [e for e in st.session_state.evaluations_db if e['Teacher'] == user_info['name']]
            if my_evals:
                df_eval = prepare_eq_report_df(my_evals)
                st.dataframe(df_eval, use_container_width=True)
                render_eq_charts(my_evals, f"Lớp {user_info['class_name']}")
            else: st.info("Chưa có dữ liệu đánh giá EQ.")
