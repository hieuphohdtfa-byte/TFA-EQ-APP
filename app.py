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
EMOTION_COLS = ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng 😮‍💨", "Tự hào 🌟"]
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
        st.error(f"⚠️ Lỗi đồng bộ Google Sheet: {e}")
        return False

if 'gas_loaded' not in st.session_state:
    with st.spinner("🔄 Đang nạp dữ liệu từ Google Trang tính..."):
        gas_data = load_all_from_gas()
        st.session_state.users_df = pd.DataFrame(gas_data.get("Users", [])) if gas_data.get("Users") else DEFAULT_USERS_DF
        st.session_state.students_df = pd.DataFrame(gas_data.get("Students", [])) if gas_data.get("Students") else pd.DataFrame(columns=["teacher_user", "student_name"])
        st.session_state.evaluations_df = pd.DataFrame(gas_data.get("Evaluations", [])) if gas_data.get("Evaluations") else pd.DataFrame(columns=["Teacher", "Campus", "Class", "Student", "Term", "TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "P_EQ", "Group_Clean", "Context", "Conclusion", "Plan"])
        st.session_state.daily_logs_df = pd.DataFrame(gas_data.get("DailyLogs", [])) if gas_data.get("DailyLogs") else pd.DataFrame(columns=["Teacher", "Campus", "Class", "Student", "Date", "Routine", "Emotions", "Note", "Intervention", "Summary", "Details_JSON"])
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
# 4. HÀM CHUẨN HÓA BẢNG XUẤT FILE CHUẨN TỰA THEO MẪU WORD/EXCEL CỦA TRƯỜNG
# -----------------------------------------------------------------------------
def format_evaluations_export(df):
    """Chuẩn hóa bảng Tổng hợp Đánh giá EQ 6 Tiêu chí đúng cột mẫu"""
    if df.empty:
        return pd.DataFrame()
    
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    export_df["Tên học sinh"] = df["Student"].values
    export_df["TC1"] = pd.to_numeric(df["TC1"], errors='coerce').fillna(0)
    export_df["TC2"] = pd.to_numeric(df["TC2"], errors='coerce').fillna(0)
    export_df["TC3"] = pd.to_numeric(df["TC3"], errors='coerce').fillna(0)
    export_df["TC4"] = pd.to_numeric(df["TC4"], errors='coerce').fillna(0)
    export_df["TC5"] = pd.to_numeric(df["TC5"], errors='coerce').fillna(0)
    export_df["TC6"] = pd.to_numeric(df["TC6"], errors='coerce').fillna(0)
    
    if "P_EQ" in df.columns:
        export_df["Điểm TB (PEQ)"] = pd.to_numeric(df["P_EQ"], errors='coerce').fillna(0)
    else:
        export_df["Điểm TB (PEQ)"] = (export_df["TC1"] + export_df["TC2"] + export_df["TC3"] + export_df["TC4"] + export_df["TC5"] + export_df["TC6"]) / 6.0
        
    export_df["Nhóm Trạng Thái"] = df["Group_Clean"].values if "Group_Clean" in df.columns else "CẦN CẢI THIỆN"
    export_df["Bối cảnh/Minh chứng điển hình (hành vi cụ thể)"] = df["Context"].values if "Context" in df.columns else ""
    export_df["Kết luận xu hướng"] = df["Conclusion"].values if "Conclusion" in df.columns else ""
    export_df["Kế hoạch tác động tiếp theo"] = df["Plan"].values if "Plan" in df.columns else ""
    export_df["Kỳ / Tháng"] = df["Term"].values if "Term" in df.columns else ""
    export_df["Lớp"] = df["Class"].values if "Class" in df.columns else ""
    export_df["Cơ sở"] = df["Campus"].values if "Campus" in df.columns else ""
    export_df["Giáo viên"] = df["Teacher"].values if "Teacher" in df.columns else ""
    
    return export_df

def format_comparisons_export(df):
    """Chuẩn hóa bảng So Sánh Xu Hướng EQ giữa 2 đợt đúng cột mẫu"""
    if df.empty:
        return pd.DataFrame()
    
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    export_df["Tên học sinh"] = df["Student"].values
    export_df["Điểm đợt 1 (Kỳ 1)"] = pd.to_numeric(df["Score_Term1"], errors='coerce').fillna(0.0)
    export_df["Điểm đợt 2 (Kỳ 2)"] = pd.to_numeric(df["Score_Term2"], errors='coerce').fillna(0.0)
    
    if "Delta" in df.columns:
        export_df["Biến thiên"] = pd.to_numeric(df["Delta"], errors='coerce').fillna(0.0)
    else:
        export_df["Biến thiên"] = export_df["Điểm đợt 2 (Kỳ 2)"] - export_df["Điểm đợt 1 (Kỳ 1)"]
        
    export_df["Xu hướng EQ"] = df["Trend"].values if "Trend" in df.columns else "DUY TRÌ ÔN ĐỊNH"
    export_df["Kết luận xu hướng"] = df["Conclusion"].values if "Conclusion" in df.columns else ""
    export_df["Kế hoạch tác động tiếp theo"] = df["Plan"].values if "Plan" in df.columns else ""
    export_df["Lớp"] = df["Class"].values if "Class" in df.columns else ""
    export_df["Cơ sở"] = df["Campus"].values if "Campus" in df.columns else ""
    export_df["Giáo viên"] = df["Teacher"].values if "Teacher" in df.columns else ""
    
    return export_df

def calculate_class_stats(df_comp):
    """Tính bảng Thống kê % Thay đổi giữa Kỳ 1 và Kỳ 2 cho Bảng Xu Hướng"""
    if df_comp.empty:
        return pd.DataFrame()
    
    total_stds = len(df_comp)
    s1 = pd.to_numeric(df_comp["Score_Term1"], errors='coerce').fillna(0)
    s2 = pd.to_numeric(df_comp["Score_Term2"], errors='coerce').fillna(0)
    
    duy_tri_1 = (s1 >= 3.2).sum() / total_stds * 100
    duy_tri_2 = (s2 >= 3.2).sum() / total_stds * 100
    
    cai_thien_1 = ((s1 >= 2.0) & (s1 < 3.2)).sum() / total_stds * 100
    cai_thien_2 = ((s2 >= 2.0) & (s2 < 3.2)).sum() / total_stds * 100
    
    ho_tro_1 = (s1 < 2.0).sum() / total_stds * 100
    ho_tro_2 = (s2 < 2.0).sum() / total_stds * 100
    
    stats_df = pd.DataFrame([
        {
            "Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm DUY TRÌ (PEQ >= 3.2)",
            "Kỳ 1 / Tháng trước": f"{duy_tri_1:.2f}%",
            "Kỳ 2 / Tháng sau": f"{duy_tri_2:.2f}%",
            "Thay đổi (%)": f"{duy_tri_2 - duy_tri_1:+.2f}%"
        },
        {
            "Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm CẦN CẢI THIỆN (2.0 <= PEQ < 3.2)",
            "Kỳ 1 / Tháng trước": f"{cai_thien_1:.2f}%",
            "Kỳ 2 / Tháng sau": f"{cai_thien_2:.2f}%",
            "Thay đổi (%)": f"{cai_thien_2 - cai_thien_1:+.2f}%"
        },
        {
            "Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm HỖ TRỢ ĐẶC BIỆT (PEQ < 2.0)",
            "Kỳ 1 / Tháng trước": f"{ho_tro_1:.2f}%",
            "Kỳ 2 / Tháng sau": f"{ho_tro_2:.2f}%",
            "Thay đổi (%)": f"{ho_tro_2 - ho_tro_1:+.2f}%"
        }
    ])
    return stats_df

# -----------------------------------------------------------------------------
# 5. HÀM HỖ TRỢ VẼ BIỂU ĐỒ
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

def render_comparison_charts(comp_df, title_prefix=""):
    if comp_df.empty:
        st.info("Chưa có dữ liệu so sánh xu hướng để vẽ biểu đồ.")
        return
    st.markdown(f"#### 📈 BIỂU ĐỒ TRỰC QUAN XU HƯỚNG PHÁT TRIỂN EQ {title_prefix.upper()}")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_group = go.Figure()
        fig_group.add_trace(go.Bar(x=comp_df["Student"], y=pd.to_numeric(comp_df["Score_Term1"], errors='coerce'), name="Đợt 1", marker_color="#FFC107"))
        fig_group.add_trace(go.Bar(x=comp_df["Student"], y=pd.to_numeric(comp_df["Score_Term2"], errors='coerce'), name="Đợt 2", marker_color="#4CAF50"))
        fig_group.update_layout(
            barmode='group', title="<b>So sánh Điểm EQ giữa 2 Đợt Đánh giá</b>",
            yaxis_range=[0, 4.5], xaxis_title="Học sinh", yaxis_title="Điểm EQ",
            margin=dict(t=40, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_group, use_container_width=True)
        
    trends = comp_df["Trend"].value_counts().reset_index()
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
# 6. HEADER THƯƠNG HIỆU CHÍNH
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
# 7. GIAO DIỆN BÌA NGOÀI (BỌC FORM ĐỂ BẤM ENTER ĐĂNG NHẬP)
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
        
        with st.form(key="login_form"):
            login_user = st.text_input("👤 Tên đăng nhập:", placeholder="Nhập tên đăng nhập...").strip()
            login_pass = st.text_input("🔑 Mật khẩu:", type="password", placeholder="Nhập mật khẩu...").strip()
            st.write("")
            btn_login = st.form_submit_button("🚀 CỔNG ĐĂNG NHẬP (Nhấn Enter)")
            
            if btn_login:
                if login_user in users_dict:
                    u_info = users_dict[login_user]
                    if str(u_info["password"]) == str(login_pass):
                        if u_info.get("status", "active") == "inactive":
                            st.error("❌ Tài khoản này đã bị NGƯNG HIỆU LỰC hoạt động!")
                        else:
                            st.session_state.logged_user = login_user
                            st.success(f"🎉 Đăng nhập thành công! Chào mừng {u_info['name']}")
                            st.rerun()
                    else:
                        st.error("❌ Mật khẩu không chính xác!")
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
# 8. KHÔNG GIAN LÀM VIỆC TRONG APP (SAU KHI ĐĂNG NHẬP)
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
        main_menu = st.sidebar.radio("DANH MỤC SUPER ADMIN:", [
            "👑 1. Tạo & Quản lý Tài khoản BGH",
            "📊 2. Báo cáo EQ Toàn Hệ Thống",
            "📈 3. Bảng So Sánh & Xu Hướng EQ",
            "📝 4. Nhật ký Cảm xúc Toàn Trường"
        ])
        
        if main_menu == "👑 1. Tạo & Quản lý Tài khoản BGH":
            st.subheader("👑 TẠO & QUẢN LÝ TÀI KHOẢN BGH CƠ SỞ")
            with st.form(key="form_create_bgh"):
                col1, col2 = st.columns(2)
                with col1: BGH_code = st.selectbox("Chọn Cơ sở quản lý:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}")
                with col2: BGH_name = st.text_input("Tên đại diện BGH:", value=f"BGH {CAMPUS_MAP[BGH_code]}").strip()
                BGH_u = st.text_input("Tên đăng nhập BGH:", value=f"BGH{BGH_code}").strip()
                BGH_p = st.text_input("Mật khẩu BGH:", value="123456")
                btn_bgh = st.form_submit_button("➕ Tạo Tài Khoản BGH (Nhấn Enter)")
                
                if btn_bgh:
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
                        st.success(f"🎉 Đã lưu vĩnh viễn trên Google Sheets! TK: `{BGH_u}` | Mật khẩu: `{BGH_p}`")
                        st.rerun()

            st.markdown("---")
            st.dataframe(st.session_state.users_df, use_container_width=True)

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ TOÀN HỆ THỐNG")
            df_eval_raw = st.session_state.evaluations_df
            if not df_eval_raw.empty:
                df_export = format_evaluations_export(df_eval_raw)
                st.dataframe(df_export, use_container_width=True)
                render_eq_charts(df_eval_raw, "(Toàn Trường)")
                st.download_button(
                    "📥 Xuất File CSV/Excel Bảng Tổng Hợp EQ Chuẩn Mẫu",
                    df_export.to_csv(index=False).encode('utf-8-sig'),
                    "Bao_Cao_Tong_Hop_EQ_TFA.csv", "text/csv"
                )
            else: st.info("Chưa có dữ liệu đánh giá EQ.")

        elif main_menu == "📈 3. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XU HƯỚNG PHÁT TRIỂN EQ TOÀN TRƯỜNG")
            df_comp_raw = st.session_state.comparisons_df
            if not df_comp_raw.empty:
                df_comp_export = format_comparisons_export(df_comp_raw)
                st.dataframe(df_comp_export, use_container_width=True)
                
                st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Toàn Trường")
                st.table(calculate_class_stats(df_comp_raw))
                
                render_comparison_charts(df_comp_raw, "(Toàn Trường)")
                st.download_button(
                    "📥 Xuất File CSV/Excel Bảng Xu Hướng EQ Chuẩn Mẫu",
                    df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                    "Bang_Xu_Huong_EQ_TFA.csv", "text/csv"
                )
            else: st.info("Chưa có dữ liệu so sánh xu hướng EQ.")

        else:
            st.subheader("📝 NHẬT KÝ CẢM XÚC TOÀN HỆ THỐNG")
            st.dataframe(st.session_state.daily_logs_df, use_container_width=True)

    # =========================================================================
    # VAI TRÒ 2: BGH TỪNG CƠ SỞ (CAMPUS ADMIN)
    # =========================================================================
    elif role == "campus_admin":
        my_campus = user_info['campus']
        my_code = user_info['campus_code']
        main_menu = st.sidebar.radio(f"DANH MỤC BGH ({my_code}):", [
            f"🏫 1. Tạo Giáo viên ({my_code})",
            f"📊 2. Báo cáo EQ Cơ sở ({my_code})",
            f"📈 3. Bảng So Sánh Xu Hướng ({my_code})"
        ])
        
        if main_menu == f"🏫 1. Tạo Giáo viên ({my_code})":
            st.subheader(f"🏫 BGH QUẢN LÝ VÀ TẠO TÀI KHOẢN GIÁO VIÊN: {my_campus.upper()}")
            with st.form(key="form_create_gv"):
                col1, col2 = st.columns(2)
                with col1: t_phone = st.text_input("Số điện thoại Giáo viên:").strip()
                with col2: t_name = st.text_input("Họ và tên Giáo viên:").strip()
                btn_gv = st.form_submit_button("➕ Tạo Tài Khoản Giáo Viên (Nhấn Enter)")
                
                if btn_gv:
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
                            st.success(f"🎉 Đã lưu vĩnh viễn trên Google Sheets! TK: `{gen_u}` | Mật khẩu: `123456`")
                            st.rerun()

            st.markdown("---")
            gv_df = st.session_state.users_df[(st.session_state.users_df['role'] == 'teacher') & (st.session_state.users_df['campus_code'] == my_code)]
            st.dataframe(gv_df, use_container_width=True)

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            df_c = st.session_state.evaluations_df[st.session_state.evaluations_df['Campus'] == my_campus]
            if not df_c.empty:
                df_export = format_evaluations_export(df_c)
                st.dataframe(df_export, use_container_width=True)
                render_eq_charts(df_c, f"({my_code})")
                st.download_button(
                    "📥 Xuất File CSV/Excel Báo Cáo EQ Cơ Sở",
                    df_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bao_Cao_EQ_{my_code}.csv", "text/csv"
                )
            else: st.info("Chưa có dữ liệu đánh giá EQ tại cơ sở.")

        else:
            df_comp_c = st.session_state.comparisons_df[st.session_state.comparisons_df['Campus'] == my_campus]
            if not df_comp_c.empty:
                df_comp_export = format_comparisons_export(df_comp_c)
                st.dataframe(df_comp_export, use_container_width=True)
                st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Cơ Sở")
                st.table(calculate_class_stats(df_comp_c))
                render_comparison_charts(df_comp_c, f"({my_code})")
            else: st.info("Chưa có dữ liệu so sánh xu hướng EQ tại cơ sở.")

    # =========================================================================
    # VAI TRÒ 3: GIÁO VIÊN TỪNG LỚP
    # =========================================================================
    else:
        main_menu = st.sidebar.radio("DANH MỤC GIÁO VIÊN:", [
            "🏫 1. Quản lý Học sinh",
            "📝 2. Nhật ký Cảm xúc Hằng ngày",
            "🎯 3. Đánh giá EQ 6 Tiêu chí",
            "📈 4. Bảng So Sánh & Xu Hướng EQ",
            "📊 5. Báo cáo & Xuất File Lớp"
        ])

        if main_menu == "🏫 1. Quản lý Học sinh":
            st.subheader("🏫 TỰ TẠO LỚP HỌC & QUẢN LÝ HỌC SINH")
            
            with st.form(key="form_update_class_name"):
                col_l1, col_l2 = st.columns(2)
                with col_l1: sel_class_type = st.selectbox("Chọn Khối lớp:", TFA_CLASSES)
                with col_l2: custom_class_name = st.text_input("Tên riêng của Lớp:", value=user_info.get("class_name", sel_class_type))
                btn_class = st.form_submit_button("💾 Cập Nhật Tên Lớp (Hoặc nhấn Enter)")
                if btn_class:
                    user_idx = st.session_state.users_df[st.session_state.users_df['username'] == user_key].index
                    if not user_idx.empty:
                        st.session_state.users_df.at[user_idx, "class_name"] = custom_class_name
                        save_sheet_to_gas("Users", st.session_state.users_df)
                        st.success(f"🎉 Đã lưu tên lớp: **{custom_class_name}**")
                        st.rerun()

            st.markdown("---")
            
            with st.form(key="form_add_student", clear_on_submit=True):
                st.markdown("##### ➕ Thêm Học Sinh Mới")
                new_student = st.text_input("Họ và tên học sinh mới:").strip()
                btn_std = st.form_submit_button("➕ Thêm Học Sinh (Hoặc nhấn Enter)")
                if btn_std:
                    if new_student:
                        new_std_row = pd.DataFrame([{"teacher_user": user_key, "student_name": new_student}])
                        st.session_state.students_df = pd.concat([st.session_state.students_df, new_std_row], ignore_index=True)
                        save_sheet_to_gas("Students", st.session_state.students_df)
                        st.success(f"🎉 Đã lưu vĩnh viễn bé **{new_student}** vào Google Sheet!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng điền họ tên học sinh!")

            st.markdown("---")
            st.markdown("##### 📋 Danh Sách Học Sinh Trong Lớp (Có Nút Sửa / Xóa)")
            
            my_stds_df = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]
            if not my_stds_df.empty:
                for idx, row in my_stds_df.iterrows():
                    s_name = row['student_name']
                    c_s1, c_s2, c_s3 = st.columns([2.8, 1, 1])
                    with c_s1: st.write(f"👦/👧 **{s_name}**")
                    with c_s2:
                        if st.button("✏️ Sửa", key=f"edit_std_{idx}"):
                            st.session_state[f"editing_std_{idx}"] = not st.session_state.get(f"editing_std_{idx}", False)
                    with c_s3:
                        if st.button("🗑️ Xóa", key=f"del_std_{idx}"):
                            st.session_state.students_df = st.session_state.students_df.drop(idx).reset_index(drop=True)
                            save_sheet_to_gas("Students", st.session_state.students_df)
                            st.success(f"Đã xóa học sinh **{s_name}** khỏi lớp!")
                            st.rerun()
                    
                    if st.session_state.get(f"editing_std_{idx}", False):
                        with st.form(key=f"form_edit_std_{idx}"):
                            new_name_val = st.text_input("Sửa lại họ và tên:", value=s_name)
                            btn_save_edit = st.form_submit_button("💾 Lưu Thay Đổi (Hoặc nhấn Enter)")
                            if btn_save_edit:
                                st.session_state.students_df.at[idx, 'student_name'] = new_name_val.strip()
                                save_sheet_to_gas("Students", st.session_state.students_df)
                                st.session_state[f"editing_std_{idx}"] = False
                                st.success(f"🎉 Đã cập nhật tên thành **{new_name_val.strip()}**!")
                                st.rerun()
                    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("Lớp chưa có học sinh nào. Hãy nhập tên bé ở ô phía trên nhé!")

        # ---------------------------------------------------------------------
        # 📝 2. NHẬT KÝ CẢM XÚC HẰNG NGÀY (THIẾT KẾ CHUẨN MAU WORD)
        # ---------------------------------------------------------------------
        elif main_menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
            st.subheader("📋 HỒ SƠ CẢM XÚC CÁ NHÂN (HẰNG NGÀY)")
            st.caption("Thiết kế chuẩn hóa theo mẫu Hồ sơ cảm xúc hằng ngày của The FIRST Academy")
            
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds:
                st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Quản lý Học sinh' để thêm học sinh trước!")
            else:
                col_s1, col_s2, col_s3 = st.columns([1.5, 1.5, 1])
                with col_s1: std_select = st.selectbox("👦/👧 Chọn học sinh:", my_stds)
                with col_s2: log_date = st.date_input("🗓️ Ngày theo dõi:", value=datetime.today())
                with col_s3: st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**")
                
                st.markdown("---")
                st.markdown("#### 1. Hoạt động trong ngày (Tích chọn cảm xúc riêng cho từng hoạt động)")
                
                init_routines_data = []
                for r in TFA_ROUTINES:
                    init_routines_data.append({
                        "Hoạt động": r,
                        "Vui 😊": False,
                        "Buồn 😢": False,
                        "Giận 😡": False,
                        "Yêu thương 🥰": False,
                        "Hào hứng 🤩": False,
                        "Lo lắng 😮‍💨": False,
                        "Tự hào 🌟": False,
                        "Ghi chú chi tiết": ""
                    })
                df_routine_init = pd.DataFrame(init_routines_data)
                
                edited_routine_df = st.data_editor(
                    df_routine_init,
                    column_config={
                        "Hoạt động": st.column_config.TextColumn("Hoạt động trong ngày", disabled=True, width="medium"),
                        "Vui 😊": st.column_config.CheckboxColumn("Vui 😊", default=False),
                        "Buồn 😢": st.column_config.CheckboxColumn("Buồn 😢", default=False),
                        "Giận 😡": st.column_config.CheckboxColumn("Giận 😡", default=False),
                        "Yêu thương 🥰": st.column_config.CheckboxColumn("Yêu thương 🥰", default=False),
                        "Hào hứng 🤩": st.column_config.CheckboxColumn("Hào hứng 🤩", default=False),
                        "Lo lắng 😮‍💨": st.column_config.CheckboxColumn("Lo lắng 😮‍💨", default=False),
                        "Tự hào 🌟": st.column_config.CheckboxColumn("Tự hào 🌟", default=False),
                        "Ghi chú chi tiết": st.column_config.TextColumn("Ghi chú từng hoạt động", width="large")
                    },
                    hide_index=True,
                    use_container_width=True,
                    key=f"editor_{std_select}_{log_date}"
                )
                
                st.markdown("---")
                st.markdown("#### 2. Quan sát nhanh của giáo viên")
                col_o1, col_o2 = st.columns(2)
                with col_o1:
                    note_context = st.text_area("📌 Bối cảnh và biểu hiện nổi bật:", placeholder="Mô tả cụ thể hành vi, cử chỉ hay bối cảnh xảy ra cảm xúc...")
                with col_o2:
                    note_intervention = st.text_area("🤝 Can thiệp và hỗ trợ của giáo viên:", placeholder="Ghi lại hành động dỗ dành, ôm, hỏi gợi mở hay góc bình tĩnh cô đã dùng...")
                    
                st.markdown("---")
                st.markdown("#### 3. Đánh giá cuối ngày")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    daily_trend = st.selectbox("📈 Xu hướng cảm xúc trong ngày:", [
                        "Duy trì cảm xúc tích cực, vui vẻ cả ngày",
                        "Có xáo trộn nhỏ ở đầu ngày, nhanh chóng cân bằng",
                        "Cần sự can thiệp và hỗ trợ nhiều từ cô",
                        "Cần lưu ý đặc biệt / Có biểu hiện bùng nổ cảm xúc"
                    ])
                with col_d2:
                    daily_summary = st.text_input("💬 Nhận xét ngắn gọn của giáo viên:", placeholder="Nhận xét tổng quát về sự tiến bộ hay tâm trạng của bé...")
                
                st.write("")
                if st.button("💾 LƯU HỒ SƠ CẢM XÚC HẰNG NGÀY (LÊN GOOGLE SHEETS)"):
                    emotions_summary_list = []
                    details_dict = {}
                    
                    for idx, row in edited_routine_df.iterrows():
                        act_name = row["Hoạt động"]
                        active_emos = [e_col for e_col in EMOTION_COLS if row[e_col] == True]
                        act_note = str(row["Ghi chú chi tiết"]).strip()
                        
                        if active_emos or act_note:
                            e_str = ", ".join(active_emos) if active_emos else "Ghi chú"
                            emotions_summary_list.append(f"{act_name}: {e_str}" + (f" ({act_note})" if act_note else ""))
                        
                        details_dict[act_name] = {
                            "emotions": active_emos,
                            "note": act_note
                        }
                    
                    full_emotions_str = " | ".join(emotions_summary_list) if emotions_summary_list else "Bình thường ở tất cả hoạt động"
                    json_str = json.dumps(details_dict, ensure_ascii=False)
                    
                    new_log = pd.DataFrame([{
                        "Teacher": user_info['name'],
                        "Campus": user_info['campus'],
                        "Class": user_info.get('class_name', 'Mầm'),
                        "Student": std_select,
                        "Date": str(log_date),
                        "Routine": "Toàn bộ hoạt động trong ngày",
                        "Emotions": full_emotions_str,
                        "Note": note_context,
                        "Intervention": note_intervention,
                        "Summary": f"[{daily_trend}] {daily_summary}",
                        "Details_JSON": json_str
                    }])
                    
                    st.session_state.daily_logs_df = pd.concat([st.session_state.daily_logs_df, new_log], ignore_index=True)
                    save_sheet_to_gas("DailyLogs", st.session_state.daily_logs_df)
                    st.success(f"🎉 Đã lưu vĩnh viễn Hồ sơ cảm xúc ngày {log_date} cho bé **{std_select}** lên Google Sheets!")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 📋 LỊCH SỬ HỒ SƠ CẢM XÚC ĐÃ LƯU CỦA LỚP")
            my_logs = st.session_state.daily_logs_df[st.session_state.daily_logs_df['Teacher'] == user_info['name']]
            if not my_logs.empty:
                st.dataframe(my_logs[['Date', 'Student', 'Emotions', 'Note', 'Intervention', 'Summary']], use_container_width=True)
            else:
                st.info("Chưa có hồ sơ cảm xúc hằng ngày nào được lưu.")

        # ---------------------------------------------------------------------
        # 🎯 3. ĐÁNH GIÁ EQ 6 TIÊU CHÍ CHUẨN
        # ---------------------------------------------------------------------
        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ CHUẨN")
            st.caption("Căn cứ theo Bảng Tiêu Chí EQ Chuẩn Hóa Toàn Trường (Mức 1 - Mức 4)")
            
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_e1, col_e2 = st.columns(2)
                with col_e1: std_eval = st.selectbox("Chọn học sinh:", my_stds)
                with col_e2: 
                    eval_month = st.selectbox("Chọn Tháng đánh giá:", [f"Tháng {m}" for m in range(1, 13)], index=5)
                    term = f"{eval_month} / Kỳ {1 if int(eval_month.replace('Tháng ', '')) <= 6 else 2}"
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    tc1 = st.slider("TC1: Nhận biết cảm xúc bản thân", 1, 4, 2, help="1: Bộc phát | 2: Nhận biết có điều kiện | 3: Tự nhận biết - hỗ trợ nhẹ | 4: Chủ động & ổn định")
                    tc2 = st.slider("TC2: Gọi tên và diễn đạt cảm xúc", 1, 4, 2, help="1: Phản ứng sinh lý | 2: Gọi tên 1 từ | 3: Nói câu đơn định danh | 4: Diễn đạt + nguyên nhân")
                    tc3 = st.slider("TC3: Điều chỉnh và kiểm soát cảm xúc", 1, 4, 2, help="1: Bùng nổ >5p | 2: Bình tĩnh khi cô ôm | 3: Tự trấn an theo lời nhắc | 4: Tự tìm góc bình tĩnh")
                with c2:
                    tc4 = st.slider("TC4: Đồng cảm và quan hệ xã hội", 1, 4, 2, help="1: Thờ ơ | 2: Quan sát bạn khóc | 3: Cử chỉ an ủi sơ khai | 4: Chủ động rủ bạn chơi/chia sẻ")
                    tc5 = st.slider("TC5: Ảnh hưởng môi trường đến cảm xúc", 1, 4, 3, help="1: Phụ thuộc hoàn toàn | 2: Phụ thuộc sự quen thuộc | 3: Thích nghi có điều kiện | 4: Ít bị ảnh hưởng tiêu cực")
                    tc6 = st.slider("TC6: Phản ứng khi cảm xúc được công nhận", 1, 4, 3, help="1: Lảng tránh/ăn vạ tiếp | 2: Dịu lại nhưng chưa hợp tác | 3: Hợp tác sau khi được dỗ | 4: Tự giải tỏa & chủ động")
                    
                peq = round((tc1 + tc2 + tc3 + tc4 + tc5 + tc6) / 6.0, 2)
                group_clean = "DUY TRÌ" if peq >= 3.2 else ("CẦN CẢI THIỆN" if peq >= 2.0 else "HỖ TRỢ ĐẶC BIỆT")
                
                st.markdown("---")
                col_m1, col_m2 = st.columns([1, 4])
                with col_m1:
                    st.metric("Điểm EQ Tổng hợp (PEQ):", peq, delta=f"Nhóm: {group_clean}")
                with col_m2:
                    st.info(f"📌 **Phân nhóm trạng thái:** `{group_clean}`\n\n*(PEQ ≥ 3.2: Duy trì phong độ | 2.0 ≤ PEQ < 3.2: Cần cải thiện | PEQ < 2.0: Hỗ trợ đặc biệt)*")
                
                context_input = st.text_area("Bối cảnh / Minh chứng điển hình (Hành vi cụ thể):", value=f"{std_eval} thường...")
                conclusion_input = st.text_area("Kết luận xu hướng phát triển:", value=f"Xu hướng của {std_eval}...")
                plan_input = st.text_area("Kế hoạch tác động tiếp theo:", value=f"Hướng dẫn {std_eval}...")
                
                if st.button("💾 Lưu Bảng Đánh Giá EQ (Lên Google Sheets)"):
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
                    st.rerun()

        # ---------------------------------------------------------------------
        # 📈 4. BẢNG SO SÁNH & XU HƯỚNG PHÁT TRIỂN EQ (SO SÁNH 2 ĐỢT/THÁNG)
        # ---------------------------------------------------------------------
        elif main_menu == "📈 4. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XÁC NHẬN XU HƯỚNG PHÁT TRIỂN EQ")
            st.caption("Thiết kế theo chuẩn 'Bảng Xu Hướng Phát Triển EQ Của Trẻ' (So sánh 2 đợt/tháng)")
            
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds:
                st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng thêm học sinh trước!")
            else:
                std_comp = st.selectbox("👦/👧 Chọn học sinh cần so sánh:", my_stds)
                
                col_cmp1, col_cmp2, col_cmp3 = st.columns(3)
                with col_cmp1:
                    score_t1 = st.number_input("Điểm Đợt 1 (Kỳ 1 / Tháng trước):", min_value=1.0, max_value=4.0, value=2.2, step=0.1)
                with col_cmp2:
                    score_t2 = st.number_input("Điểm Đợt 2 (Kỳ 2 / Tháng sau):", min_value=1.0, max_value=4.0, value=3.0, step=0.1)
                with col_cmp3:
                    delta_score = round(score_t2 - score_t1, 2)
                    trend_tag = "TIẾN BỘ VƯỢT BẬC" if delta_score >= 0.5 else ("TIẾN BỘ" if delta_score > 0 else ("DUY TRÌ ÔN ĐỊNH" if delta_score == 0 else "CẦN LƯU Ý (THỤT LÙI)"))
                    st.metric("Biến thiên (Delta):", f"{delta_score:+.2f}", delta=trend_tag)
                
                c_input = st.text_area("Kết luận xu hướng:", value=f"Bé {std_comp} có xu hướng {trend_tag.lower()}...")
                p_input = st.text_area("Kế hoạch tác động tiếp theo:", value=f"Tiếp tục đồng hành hỗ trợ bé {std_comp}...")
                
                if st.button("💾 Lưu Bảng So Sánh Xu Hướng EQ (Lên Google Sheets)"):
                    st.session_state.comparisons_df = st.session_state.comparisons_df[
                        ~((st.session_state.comparisons_df['Teacher'] == user_info['name']) & (st.session_state.comparisons_df['Student'] == std_comp))
                    ]
                    
                    new_comp = pd.DataFrame([{
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_comp,
                        "Score_Term1": score_t1, "Score_Term2": score_t2,
                        "Delta": delta_score, "Trend": trend_tag,
                        "Conclusion": c_input, "Plan": p_input
                    }])
                    
                    st.session_state.comparisons_df = pd.concat([st.session_state.comparisons_df, new_comp], ignore_index=True)
                    save_sheet_to_gas("Comparisons", st.session_state.comparisons_df)
                    st.success(f"🎉 Đã lưu vĩnh viễn dữ liệu so sánh xu hướng cho bé **{std_comp}** lên Google Sheets!")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 📋 DỮ LIỆU SO SÁNH XU HƯỚNG HIỆN CÓ CỦA LỚP")
            my_comps = st.session_state.comparisons_df[st.session_state.comparisons_df['Teacher'] == user_info['name']]
            if not my_comps.empty:
                df_comp_exp = format_comparisons_export(my_comps)
                st.dataframe(df_comp_exp, use_container_width=True)
                
                st.markdown("##### 📊 THỐNG KÊ TỈ LỆ % PHÂN BỔ TOÀN LỚP (KỲ 1 VS KỲ 2)")
                st.table(calculate_class_stats(my_comps))
            else:
                st.info("Chưa có dữ liệu so sánh xu hướng EQ nào.")

        # ---------------------------------------------------------------------
        # 📊 5. BÁO CÁO & XUẤT FILE LỚP (EXCEL / CSV CHUẨN CỘT MẪU)
        # ---------------------------------------------------------------------
        else:
            st.subheader("📊 BÁO CÁO TỔNG HỢP & XUẤT FILE ĐÁNH GIÁ EQ CỦA LỚP")
            
            tab_rep1, tab_rep2 = st.tabs(["📋 1. Bảng Kết Quả Đánh Giá EQ (6 Tiêu Chí)", "📈 2. Bảng So Sánh Xu Hướng EQ (2 Kỳ)"])
            
            with tab_rep1:
                my_evals = st.session_state.evaluations_df[st.session_state.evaluations_df['Teacher'] == user_info['name']]
                if not my_evals.empty:
                    df_eval_export = format_evaluations_export(my_evals)
                    st.dataframe(df_eval_export, use_container_width=True)
                    
                    render_eq_charts(my_evals, f"Lớp {user_info.get('class_name', '')}")
                    
                    st.download_button(
                        "📥 XUẤT FILE EXCEL/CSV BẢNG TỔNG HỢP EQ CHUẨN MẪU",
                        df_eval_export.to_csv(index=False).encode('utf-8-sig'),
                        f"Bang_Tong_Hop_EQ_Lop_{user_info.get('class_name', '')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("Chưa có dữ liệu đánh giá EQ cho lớp này.")

            with tab_rep2:
                my_comps = st.session_state.comparisons_df[st.session_state.comparisons_df['Teacher'] == user_info['name']]
                if not my_comps.empty:
                    df_comp_export = format_comparisons_export(my_comps)
                    st.dataframe(df_comp_export, use_container_width=True)
                    
                    st.markdown("##### 📊 Bảng Thống Kê Thay Đổi Chỉ Số Tỉ Lệ % Toàn Lớp")
                    st.table(calculate_class_stats(my_comps))
                    
                    render_comparison_charts(my_comps, f"Lớp {user_info.get('class_name', '')}")
                    
                    st.download_button(
                        "📥 XUẤT FILE EXCEL/CSV BẢNG XU HƯỚNG EQ CHUẨN MẪU",
                        df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                        f"Bang_Xu_Huong_EQ_Lop_{user_info.get('class_name', '')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("Chưa có dữ liệu so sánh xu hướng EQ cho lớp này.")
