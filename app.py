import streamlit as st
import pandas as pd
import requests
import os
import json
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 🔗 KẾT NỐI VỚI GOOGLE SHEET QUA WEB APP URL (KHO DỮ LIỆU THỰC NGUYÊN BẢN)
# -----------------------------------------------------------------------------
GAS_URL = "https://script.google.com/macros/s/AKfycbwYyCVKVPrIw80fR13LysE3yZz2OrZRhPlfeymEJ6j-g_GkEfWtnauvNzfKJnEQYWNeqA/exec"

# -----------------------------------------------------------------------------
# 🛠️ HÀM HỖ TRỢ CHUẨN HÓA MÃ CHUỖI & TÌM KIẾM AN TOÀN TUYỆT ĐỐI
# -----------------------------------------------------------------------------
def remove_accents(input_str):
    if not input_str: return ''
    s = str(input_str)
    s = re.sub(r'[àáảãạăằắẳẵặâầấẩẫậ]', 'a', s)
    s = re.sub(r'[ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ]', 'A', s)
    s = re.sub(r'[đ]', 'd', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[èéẻẽẹêềếểễệ]', 'e', s)
    s = re.sub(r'[ÈÉẺẼẸÊỀẾỂỄỆ]', 'E', s)
    s = re.sub(r'[ìíỉĩị]', 'i', s)
    s = re.sub(r'[ÌÍỈĨỊ]', 'I', s)
    s = re.sub(r'[òóỏõọôồốổỗộơờớởỡợ]', 'o', s)
    s = re.sub(r'[ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ]', 'O', s)
    s = re.sub(r'[ùúủũụưừứửữự]', 'u', s)
    s = re.sub(r'[ÙÚỦŨỤƯỪỨỬỮỰ]', 'U', s)
    s = re.sub(r'[ỳýỷỹỵ]', 'y', s)
    s = re.sub(r'[ỲÝỶỸỴ]', 'Y', s)
    return s

def clean_dict_key(k):
    if not k: return ''
    s = remove_accents(str(k)).lower()
    return re.sub(r'[^a-z0-9]', '', s)

def clean_key(val):
    if val is None or pd.isna(val): return ''
    s = remove_accents(str(val)).strip().lower().replace('.0', '')
    if s in ['nan', 'none']: return ''
    s = re.sub(r'[^a-z0-9]', '', s)
    if s.startswith('0') and len(s) > 1: s = s[1:]
    return s

def filter_records_multilevel(df, campus="Tất cả", class_name="Tất cả", teacher="Tất cả", student="Tất cả"):
    if df is None or df.empty:
        return pd.DataFrame()
    res = df.copy()
    
    # 1. Campus
    if campus and "Tất cả" not in str(campus):
        c_target = clean_dict_key(campus)
        c_col = 'campus' if 'campus' in res.columns else res.columns[0]
        def match_c(v):
            if not v or pd.isna(v): return False
            v_c = clean_dict_key(v)
            return v_c == c_target or v_c in c_target or c_target in v_c
        res = res[res[c_col].apply(match_c)]

    # 2. Class
    if class_name and "Tất cả" not in str(class_name):
        cl_target = clean_dict_key(class_name)
        cl_col = 'class' if 'class' in res.columns else res.columns[0]
        def match_cl(v):
            if not v or pd.isna(v): return False
            v_cl = clean_dict_key(v)
            return v_cl == cl_target or v_cl in cl_target or cl_target in v_cl
        res = res[res[cl_col].apply(match_cl)]

    # 3. Teacher
    if teacher and "Tất cả" not in str(teacher):
        t_target = clean_dict_key(teacher)
        t_col = 'teacher' if 'teacher' in res.columns else res.columns[0]
        def match_t(v):
            if not v or pd.isna(v): return False
            v_t = clean_dict_key(v)
            return v_t == t_target or v_t in t_target or t_target in v_t
        res = res[res[t_col].apply(match_t)]

    # 4. Student
    if student and "Tất cả" not in str(student):
        s_target = clean_dict_key(student)
        s_col = 'student' if 'student' in res.columns else res.columns[0]
        def match_s(v):
            if not v or pd.isna(v): return False
            v_s = clean_dict_key(v)
            return v_s == s_target or v_s in s_target or s_target in v_s
        res = res[res[s_col].apply(match_s)]

    return res

def filter_df_by_clean_col(df, col_name, target_val):
    if df is None or df.empty or col_name not in df.columns:
        return pd.DataFrame()
    target_clean = clean_key(target_val)
    mask = df[col_name].apply(clean_key) == target_clean
    return df[mask]

def get_gas_sheet_rows(gas_data, sheet_name):
    if not isinstance(gas_data, dict): return []
    for sub_key in ["data", "result", "sheets", "payload"]:
        if sub_key in gas_data and isinstance(gas_data[sub_key], dict):
            gas_data = gas_data[sub_key]
            break
    clean_target = str(sheet_name).strip().lower().replace(" ", "").replace("_", "")
    for k, v in gas_data.items():
        clean_k = str(k).strip().lower().replace(" ", "").replace("_", "")
        if clean_k == clean_target or clean_k == clean_target + "s" or clean_target == clean_k + "s":
            if isinstance(v, list): return v
            elif isinstance(v, dict): return [v]
    return []

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG & GIAO DIỆN TỐI ƯU CẢ TRÊN MÁY TÍNH VÀ ĐIỆN THOẠI (RESPONSIVE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The FIRST Academy - Hệ Thống Quản Lý Cảm Xúc EQ",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stApp { background-color: #FFFDF5; }
        .main-header {
            background: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
            padding: 18px 22px;
            border-radius: 12px;
            color: #1A1A1A;
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.25);
            margin-bottom: 20px;
        }
        .main-header h2 { color: #1A1A1A !important; font-weight: 800; margin: 0; font-size: 24px; }
        .main-header p { color: #2D2D2D; margin: 4px 0 0 0; font-size: 14px; font-weight: 500; }
        .login-card {
            background-color: #FFFFFF;
            padding: 20px 15px;
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
            padding: 12px 20px;
            width: 100%;
            transition: all 0.3s ease;
            font-size: 15px;
        }
        .stButton>button:hover {
            background-color: #FFB300;
            color: #000000;
            box-shadow: 0 4px 12px rgba(255, 179, 0, 0.4);
        }
        section[data-testid="stSidebar"] {
            background-color: #FFF9E6;
            border-right: 1px solid #FFE082;
        }
        .info-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 16px;
            border: 1px solid #FFE58F;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            margin-bottom: 15px;
        }
        .campus-badge {
            background-color: #FFF3C4;
            color: #B78103;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        @media (max-width: 768px) {
            .main-header { padding: 12px 15px; }
            .main-header h2 { font-size: 18px; }
            .stButton>button { padding: 10px 14px; font-size: 14px; }
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. HẰNG SỐ CẤU HÌNH & DANH SÁCH MẶC ĐỊNH
# -----------------------------------------------------------------------------
CAMPUS_MAP = {
    "HD": "Cơ sở TFA Hà Đô (Phường Cát Lái, TP.HCM)",
    "HL": "Cơ sở TFA Him Lam (Phường Tân Hưng, TP.HCM)",
    "DBM": "Cơ sở TFA Dương Bạch Mai (Phường Chánh Hưng, TP.HCM)",
    "LVS": "Cơ sở TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)",
    "TTL": "Cơ sở TFA Trần Thị Lý (Phường Hòa Cường, Đà Nẵng)"
}

TFA_CLASSES = [
    "Pre-school (3-4 tuổi)",
    "Kindergarten (4-5 tuổi)",
    "Pre-primary (5-6 tuổi)"
]

SCHOOL_YEAR_OPTIONS = ["2024 - 2025", "2025 - 2026", "2026 - 2027", "2027 - 2028"]

DEFAULT_USERS_DF = pd.DataFrame([
    {"username": "admin", "password": "admin123", "name": "Ban Giám Hiệu Tổng (Toàn Hệ Thống)", "role": "super_admin", "campus_code": "ALL", "campus": "Tất cả cơ sở", "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHD", "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin", "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHTTL", "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin", "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHDBM", "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin", "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHL", "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin", "campus_code": "HL", "campus": CAMPUS_MAP["HL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHLVS", "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin", "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"], "class_name": "Tất cả", "status": "active"}
])

LOGO_FILE = "logo.png" if os.path.exists("logo.png") else ("Logo TFA Ver2.1 .png" if os.path.exists("Logo TFA Ver2.1 .png") else "/workspace/knowledge/Logo_TFA_Ver2.1_.png")

# -----------------------------------------------------------------------------
# 3. CHUẨN HÓA DỮ LIỆU ĐỌC TỪ GOOGLE SHEET
# -----------------------------------------------------------------------------
def normalize_users_df(raw_rows, default_users_df):
    if not raw_rows: return default_users_df
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        cr = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        row_clean = {}
        for k in ['username', 'user', 'tk', 'tendangnhap', 'taikhoan']:
            if k in cr and cr[k]: row_clean['username'] = cr[k]; break
        for k in ['password', 'pass', 'matkhau']:
            if k in cr and cr[k]: row_clean['password'] = cr[k]; break
        for k in ['name', 'hoten', 'tengiaovien', 'ten']:
            if k in cr and cr[k]: row_clean['name'] = cr[k]; break
        for k in ['role', 'vaitro']:
            if k in cr and cr[k]: row_clean['role'] = cr[k]; break
        for k in ['campuscode', 'macoso', 'code']:
            if k in cr and cr[k]: row_clean['campus_code'] = cr[k]; break
        for k in ['campus', 'coso']:
            if k in cr and cr[k]: row_clean['campus'] = cr[k]; break
        for k in ['classname', 'class', 'lop']:
            if k in cr and cr[k]: row_clean['class_name'] = cr[k]; break
        for k in ['status', 'trangthai']:
            if k in cr and cr[k]: row_clean['status'] = cr[k]; break
        norm_rows.append(row_clean)
    df = pd.DataFrame(norm_rows)
    for c in ["username", "password", "name", "role", "campus_code", "campus", "class_name", "status"]:
        if c not in df.columns: df[c] = ""
    all_df = pd.concat([default_users_df, df], ignore_index=True)
    all_df["_u_clean"] = all_df["username"].apply(clean_key)
    return all_df.drop_duplicates(subset=["_u_clean"], keep="last").drop(columns=["_u_clean"]).reset_index(drop=True)

def normalize_students_df(raw_rows):
    if not raw_rows: return pd.DataFrame(columns=["teacher_user", "student_name", "student_note"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        cr = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        row_clean = {}
        for k in ['teacheruser', 'teacher', 'giaovien', 'tkgiaovien']:
            if k in cr and cr[k]: row_clean['teacher_user'] = clean_key(cr[k]); break
        for k in ['studentname', 'student', 'tenhocsinh', 'hocsinh', 'tenbe']:
            if k in cr and cr[k]: row_clean['student_name'] = cr[k]; break
        for k in ['studentnote', 'note', 'ghichu']:
            if k in cr and cr[k]: row_clean['student_note'] = cr[k]; break
        norm_rows.append(row_clean)
    df = pd.DataFrame(norm_rows)
    for c in ["teacher_user", "student_name", "student_note"]:
        if c not in df.columns: df[c] = ""
    return df

def normalize_evaluations_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher", "campus", "class", "student", "school_year", "term", "eval_date", "tc1", "tc2", "tc3", "tc4", "tc5", "tc6", "p_eq", "group_clean", "context", "conclusion", "plan"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        cr = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        std = {}
        for k in ['teacher', 'giaovien', 'tengiaovien']:
            if k in cr and cr[k]: std['teacher'] = cr[k]; break
        if 'teacher' not in std: std['teacher'] = ''
        
        for k in ['campus', 'coso', 'tencoso']:
            if k in cr and cr[k]: std['campus'] = cr[k]; break
        if 'campus' not in std: std['campus'] = ''
        
        for k in ['class', 'lop', 'khoilop', 'classname']:
            if k in cr and cr[k]: std['class'] = cr[k]; break
        if 'class' not in std: std['class'] = ''
        
        for k in ['student', 'hocsinh', 'tenhocsinh', 'tenbe', 'be']:
            if k in cr and cr[k]: std['student'] = cr[k]; break
        if 'student' not in std: std['student'] = ''
        
        for k in ['schoolyear', 'namhoc']:
            if k in cr and cr[k]: std['school_year'] = cr[k]; break
        if 'school_year' not in std: std['school_year'] = ''
        
        for k in ['term', 'kythang', 'ky', 'thang']:
            if k in cr and cr[k]: std['term'] = cr[k]; break
        if 'term' not in std: std['term'] = ''
        
        for k in ['evaldate', 'ngaydanhgia', 'ngay']:
            if k in cr and cr[k]: std['eval_date'] = cr[k]; break
        if 'eval_date' not in std: std['eval_date'] = ''
        
        for i in range(1, 7): std[f'tc{i}'] = cr.get(f'tc{i}', '0')
        
        for k in ['peq', 'peqscore', 'diemtbpeq', 'diemtb']:
            if k in cr and cr[k]: std['p_eq'] = cr[k]; break
        if 'p_eq' not in std: std['p_eq'] = '0'
        
        for k in ['groupclean', 'nhomtrangthai', 'nhom']:
            if k in cr and cr[k]: std['group_clean'] = cr[k]; break
        if 'group_clean' not in std: std['group_clean'] = ''
        
        for k in ['context', 'boicanhminhchungdienhinhhanhvicuthe', 'boicanh', 'minhchung']:
            if k in cr and cr[k]: std['context'] = cr[k]; break
        if 'context' not in std: std['context'] = ''
        
        for k in ['conclusion', 'ketluanxuhuong', 'ketluan']:
            if k in cr and cr[k]: std['conclusion'] = cr[k]; break
        if 'conclusion' not in std: std['conclusion'] = ''
        
        for k in ['plan', 'kehoachtacdongtieptheo', 'kehoach']:
            if k in cr and cr[k]: std['plan'] = cr[k]; break
        if 'plan' not in std: std['plan'] = ''
        
        norm_rows.append(std)
    return pd.DataFrame(norm_rows)

def normalize_dailylogs_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher", "campus", "class", "student", "date", "routine", "emotions", "note", "intervention", "summary", "details_json"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        cr = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        std = {
            "teacher": cr.get("teacher", cr.get("giaovien", "")),
            "campus": cr.get("campus", cr.get("coso", "")),
            "class": cr.get("class", cr.get("lop", "")),
            "student": cr.get("student", cr.get("hocsinh", cr.get("tenbe", ""))),
            "date": cr.get("date", cr.get("ngay", "")),
            "routine": cr.get("routine", cr.get("hoatdong", "")),
            "emotions": cr.get("emotions", cr.get("camxuc", "")),
            "note": cr.get("note", cr.get("ghichu", "")),
            "intervention": cr.get("intervention", cr.get("canthiep", "")),
            "summary": cr.get("summary", cr.get("tomtat", "")),
            "details_json": cr.get("detailsjson", cr.get("chitietjson", ""))
        }
        norm_rows.append(std)
    return pd.DataFrame(norm_rows)

def normalize_comparisons_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher", "campus", "class", "student", "school_year", "comp_type", "period_1", "period_2", "score_term1", "score_term2", "delta", "trend", "conclusion", "plan", "comp_date"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        cr = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        std = {
            "teacher": cr.get("teacher", cr.get("giaovien", "")),
            "campus": cr.get("campus", cr.get("coso", "")),
            "class": cr.get("class", cr.get("lop", "")),
            "student": cr.get("student", cr.get("hocsinh", cr.get("tenbe", ""))),
            "school_year": cr.get("schoolyear", cr.get("namhoc", "")),
            "comp_type": cr.get("comptype", cr.get("loaisosanh", "")),
            "period_1": cr.get("period1", cr.get("dot1", "")),
            "period_2": cr.get("period2", cr.get("dot2", "")),
            "score_term1": cr.get("scoreterm1", cr.get("diemdot1", "0")),
            "score_term2": cr.get("scoreterm2", cr.get("diemdot2", "0")),
            "delta": cr.get("delta", cr.get("bienthien", "0")),
            "trend": cr.get("trend", cr.get("xuhuong", "")),
            "conclusion": cr.get("conclusion", cr.get("ketluanxuhuong", "")),
            "plan": cr.get("plan", cr.get("kehoachtacdongtieptheo", "")),
            "comp_date": cr.get("compdate", cr.get("ngaysosanh", ""))
        }
        norm_rows.append(std)
    return pd.DataFrame(norm_rows)

# -----------------------------------------------------------------------------
# 4. KẾT NỐI GOOGLE SHEET (NẠP & GHI VĨNH VIỄN)
# -----------------------------------------------------------------------------
def load_all_from_gas():
    try:
        res = requests.get(f"{GAS_URL}?action=read_all", allow_redirects=True, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict): return data
    except Exception: pass
    return {}

def save_sheet_to_gas(sheet_name, df):
    try:
        clean_df = df.fillna("").astype(str)
        clean_df = clean_df.replace(["nan", "None", "NaN"], "")
        rows_list = clean_df.to_dict(orient="records")
        payload = {"action": "save_sheet", "sheet_name": sheet_name, "rows": rows_list}
        headers = {"Content-Type": "application/json"}
        res = requests.post(GAS_URL, data=json.dumps(payload), headers=headers, allow_redirects=True, timeout=20)
        if res.status_code == 200:
            try:
                res_data = res.json()
                if isinstance(res_data, dict) and res_data.get("status") == "error":
                    st.error(f"⚠️ Google Sheet báo lỗi: {res_data.get('message', 'Không thể ghi dữ liệu')}")
                    return False
            except Exception: pass
            return True
        fallback_res = requests.post(GAS_URL, data={"payload": json.dumps(payload)}, allow_redirects=True, timeout=20)
        return fallback_res.status_code == 200
    except Exception as e:
        st.error(f"⚠️ Không thể kết nối với Google Sheet: {e}")
        return False

def init_app_data(force_reload=False):
    if force_reload or 'gas_loaded' not in st.session_state:
        with st.spinner("🔄 Đang đồng bộ kho dữ liệu thực từ Google Sheet..."):
            gas_data = load_all_from_gas()
            st.session_state.users_df = normalize_users_df(get_gas_sheet_rows(gas_data, "Users"), DEFAULT_USERS_DF)
            st.session_state.students_df = normalize_students_df(get_gas_sheet_rows(gas_data, "Students"))
            st.session_state.evaluations_df = normalize_evaluations_df(get_gas_sheet_rows(gas_data, "Evaluations"))
            st.session_state.daily_logs_df = normalize_dailylogs_df(get_gas_sheet_rows(gas_data, "DailyLogs"))
            st.session_state.comparisons_df = normalize_comparisons_df(get_gas_sheet_rows(gas_data, "Comparisons"))
            st.session_state.gas_loaded = True

# Khởi tạo dữ liệu
if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = None

init_app_data()

# -----------------------------------------------------------------------------
# 5. ĐỊNH DẠNG BẢNG BÁO CÁO XUẤT FILE FILE EXCEL/CSV
# -----------------------------------------------------------------------------
def format_evaluations_export(df):
    cols = [
        "STT", "Ngày đánh giá", "Tên học sinh", "Lớp", "Cơ sở", "Giáo viên",
        "Năm học", "Kỳ / Tháng",
        "TC1", "TC2", "TC3", "TC4", "TC5", "TC6",
        "Điểm TB (PEQ)", "Nhóm Trạng Thái",
        "Bối cảnh/Minh chứng điển hình (hành vi cụ thể)",
        "Kết luận xu hướng", "Kế hoạch tác động tiếp theo"
    ]
    if df is None or df.empty: return pd.DataFrame(columns=cols)
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    
    def get_series(c_name):
        if c_name in df.columns: return pd.Series(df[c_name].values, index=export_df.index)
        return pd.Series([""] * len(df), index=export_df.index)

    export_df["Ngày đánh giá"] = get_series("eval_date")
    export_df["Tên học sinh"] = get_series("student")
    export_df["Lớp"] = get_series("class")
    export_df["Cơ sở"] = get_series("campus")
    export_df["Giáo viên"] = get_series("teacher")
    export_df["Năm học"] = get_series("school_year")
    export_df["Kỳ / Tháng"] = get_series("term")
    
    for tc in ["tc1", "tc2", "tc3", "tc4", "tc5", "tc6"]:
        export_df[tc.upper()] = pd.to_numeric(get_series(tc), errors='coerce').fillna(0)
        
    export_df["Điểm TB (PEQ)"] = pd.to_numeric(get_series("p_eq"), errors='coerce').fillna(0)
    export_df["Nhóm Trạng Thái"] = get_series("group_clean")
    export_df["Bối cảnh/Minh chứng điển hình (hành vi cụ thể)"] = get_series("context")
    export_df["Kết luận xu hướng"] = get_series("conclusion")
    export_df["Kế hoạch tác động tiếp theo"] = get_series("plan")
    
    return export_df

def format_comparisons_export(df):
    cols = [
        "STT", "Ngày so sánh", "Tên học sinh", "Lớp", "Cơ sở", "Giáo viên",
        "Năm học", "Loại so sánh", "Đợt 1", "Điểm đợt 1", "Đợt 2", "Điểm đợt 2",
        "Biến thiên", "Xu hướng EQ", "Kết luận xu hướng", "Kế hoạch tác động tiếp theo"
    ]
    if df is None or df.empty: return pd.DataFrame(columns=cols)
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    
    def get_series(c_name):
        if c_name in df.columns: return pd.Series(df[c_name].values, index=export_df.index)
        return pd.Series([""] * len(df), index=export_df.index)

    export_df["Ngày so sánh"] = get_series("comp_date")
    export_df["Tên học sinh"] = get_series("student")
    export_df["Lớp"] = get_series("class")
    export_df["Cơ sở"] = get_series("campus")
    export_df["Giáo viên"] = get_series("teacher")
    export_df["Năm học"] = get_series("school_year")
    export_df["Loại so sánh"] = get_series("comp_type")
    export_df["Đợt 1"] = get_series("period_1")
    export_df["Điểm đợt 1"] = pd.to_numeric(get_series("score_term1"), errors='coerce').fillna(0)
    export_df["Đợt 2"] = get_series("period_2")
    export_df["Điểm đợt 2"] = pd.to_numeric(get_series("score_term2"), errors='coerce').fillna(0)
    export_df["Biến thiên"] = pd.to_numeric(get_series("delta"), errors='coerce').fillna(0)
    export_df["Xu hướng EQ"] = get_series("trend")
    export_df["Kết luận xu hướng"] = get_series("conclusion")
    export_df["Kế hoạch tác động tiếp theo"] = get_series("plan")
    
    return export_df

def calculate_class_stats(df_comp):
    if df_comp is None or df_comp.empty:
        return pd.DataFrame([{"Chỉ số": "Không có dữ liệu", "Giá trị": "0"}])
    total = len(df_comp)
    inc = len(df_comp[df_comp["trend"].str.contains("TĂNG|Tiến bộ", case=False, na=False)])
    dec = len(df_comp[df_comp["trend"].str.contains("GIẢM|Cần chú ý", case=False, na=False)])
    stable = total - inc - dec
    return pd.DataFrame([
        {"Chỉ số": "Tổng số bé đánh giá so sánh", "Giá trị": f"{total} bé"},
        {"Chỉ số": "Số bé có xu hướng TĂNG ĐIỂM (Tiến bộ)", "Giá trị": f"{inc} bé ({inc/total*100:.1f}%)" if total else "0"},
        {"Chỉ số": "Số bé BÌNH ỔN / ĐẦU KỲ", "Giá trị": f"{stable} bé ({stable/total*100:.1f}%)" if total else "0"},
        {"Chỉ số": "Số bé GIẢM ĐIỂM (Cần can thiệp)", "Giá trị": f"{dec} bé ({dec/total*100:.1f}%)" if total else "0"}
    ])

def render_eq_charts(eval_df, title_prefix=""):
    if eval_df is None or eval_df.empty: return
    st.markdown(f"##### 📊 Biểu Đồ Thống Kê EQ {title_prefix}")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if "group_clean" in eval_df.columns:
            grp_counts = eval_df["group_clean"].value_counts().reset_index()
            grp_counts.columns = ["Nhóm Trạng Thái", "Số lượng"]
            fig1 = px.pie(grp_counts, values="Số lượng", names="Nhóm Trạng Thái", title="Phân Phối Nhóm Trạng Thái EQ", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
    with col_g2:
        tc_cols = ["tc1", "tc2", "tc3", "tc4", "tc5", "tc6"]
        tc_names = ["TC1: Tự nhận thức", "TC2: Bộc lộ cảm xúc", "TC3: Thấu cảm", "TC4: Làm chủ hành vi", "TC5: Thích ứng", "TC6: Hợp tác"]
        avg_scores = []
        for c in tc_cols:
            if c in eval_df.columns: avg_scores.append(pd.to_numeric(eval_df[c], errors='coerce').mean())
            else: avg_scores.append(0)
        df_tc_chart = pd.DataFrame({"Tiêu chí": tc_names, "Điểm TB": avg_scores})
        fig2 = px.bar(df_tc_chart, x="Tiêu chí", y="Điểm TB", range_y=[0, 4], title="Điểm Trung Bình 6 Tiêu Chí EQ", color="Điểm TB", color_continuous_scale="Viridis")
        st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. ĐĂNG NHẬP & XÁC THỰC TÀI KHOẢN
# -----------------------------------------------------------------------------
def get_users_dict():
    u_dict = {}
    if "users_df" in st.session_state and not st.session_state.users_df.empty:
        for idx, row in st.session_state.users_df.iterrows():
            u_name = str(row.get("username", "")).strip()
            clean_u = clean_key(u_name)
            if clean_u and clean_u != "nan":
                u_dict[clean_u] = {
                    "raw_username": u_name,
                    "password": str(row.get("password", "")).strip(),
                    "name": str(row.get("name", "")).strip(),
                    "role": str(row.get("role", "teacher")).strip().lower(),
                    "campus_code": str(row.get("campus_code", "HD")).strip().upper(),
                    "campus": str(row.get("campus", "Cơ sở TFA Hà Đô")).strip(),
                    "class_name": str(row.get("class_name", "Kindergarten (4-5 tuổi)")).strip(),
                    "status": str(row.get("status", "active")).strip().lower()
                }
    return u_dict

def authenticate_user(login_u, login_p, users_dict):
    clean_u = clean_key(login_u)
    if clean_u in users_dict:
        user_info = users_dict[clean_u]
        if user_info["password"] == login_p.strip():
            if user_info["status"] == "inactive":
                return False, "⚠️ Tài khoản này hiện đã bị khóa bởi Ban Giám Hiệu!"
            return True, clean_u
        return False, "⚠️ Mật khẩu không chính xác!"
    return False, "⚠️ Tên đăng nhập không tồn tại!"

users_dict = get_users_dict()

# -----------------------------------------------------------------------------
# 7. GIAO DIỆN CHÍNH & ĐĂNG NHẬP
# -----------------------------------------------------------------------------
if st.session_state.get('logged_user') is None:
    col_left, col_right = st.columns([1.1, 1.9], gap="large")
    with col_left:
        st.markdown("""
            <div class="login-card">
                <h3 style="color: #1A1A1A; margin-top: 5px; font-weight: 700;">🔐 ĐĂNG NHẬP HỆ THỐNG</h3>
                <p style="color: #666; font-size: 13px; margin-bottom: 15px;">Dành cho Ban Giám Hiệu & Giáo Viên TFA</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form(key="login_form"):
            u_input = st.text_input("👤 Tên đăng nhập (SĐT / Mã BGH):", placeholder="VD: 0901234567HD hoặc BGHHD")
            p_input = st.text_input("🔑 Mật khẩu:", type="password")
            submit_btn = st.form_submit_button("🚀 ĐĂNG NHẬP (Nhấn Enter)")
            
            if submit_btn:
                if u_input and p_input:
                    success, res_val = authenticate_user(u_input, p_input, users_dict)
                    if success:
                        st.session_state['logged_user'] = res_val
                        st.success("🎉 Đăng nhập thành công! Đang vào hệ thống...")
                        st.rerun()
                    else:
                        st.error(res_val)
                else:
                    st.warning("⚠️ Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!")

    with col_right:
        st.markdown("""
            <div class="info-card">
                <h3 style="color: #D97706; margin-top: 0; font-weight: 800;">☀️ HỆ THỐNG QUẢN LÝ & THEO DÕI HỒ SƠ CẢM XÚC EQ</h3>
                <h5 style="color: #B45309;">Hệ Thống Mầm Non Song Ngữ The FIRST Academy (TFA)</h5>
                <p style="font-size: 14px; line-height: 1.6; color: #4B5563;">
                    Phần mềm hỗ trợ Giáo viên & BGH theo dõi nhật ký cảm xúc hằng ngày, đánh giá 6 tiêu chí EQ chuẩn mầm non, tự động tổng hợp xu hướng phát triển và xuất file báo cáo vĩnh viễn kết nối Google Sheet.
                </p>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 8. MÀN HÌNH SAU KHI ĐĂNG NHẬP
# -----------------------------------------------------------------------------
else:
    user_key = st.session_state.get('logged_user')
    user_info = users_dict.get(user_key, {
        "name": "Giáo Viên TFA", "role": "teacher", "campus": "Cơ sở TFA Hà Đô",
        "campus_code": "HD", "class_name": "Kindergarten (4-5 tuổi)"
    })
    
    role = user_info['role']
    
    # THANH SIDEBAR TẢI BÊN TRÁI
    st.sidebar.markdown(f"### 👋 Xin chào, **{user_info['name']}**!")
    
    if role == "super_admin":
        st.sidebar.error("👑 **Vai trò:** Admin Tổng (Toàn Hệ Thống)")
    elif role == "campus_admin":
        st.sidebar.warning(f"🏫 **Vai trò:** BGH - {user_info['campus']}")
    else:
        st.sidebar.info(f"🏢 **Cơ sở:** {user_info['campus']}\n\n👩‍🏫 **Lớp:** {user_info.get('class_name', 'Chưa tạo lớp')}")
    
    if st.sidebar.button("🔄 Đồng Bộ Lại Dữ Liệu"):
        init_app_data(force_reload=True)
        st.rerun()

    if st.sidebar.button("🚪 Đăng Xuất"):
        st.session_state['logged_user'] = None
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
            with st.form(key="form_create_bgh", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1: BGH_code = st.selectbox("Chọn Cơ sở quản lý:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}")
                with col2: BGH_name = st.text_input("Tên đại diện BGH:", value=f"BGH {CAMPUS_MAP[BGH_code]}").strip()
                BGH_u = st.text_input("Tên đăng nhập BGH:", value=f"BGH{BGH_code}").strip()
                BGH_p = st.text_input("Mật khẩu BGH:", value="123456")
                btn_bgh = st.form_submit_button("➕ Tạo Tài Khoản BGH (Nhấn Enter)")
                
                if btn_bgh:
                    clean_bgh_u = clean_key(BGH_u)
                    if clean_bgh_u in users_dict:
                        st.warning(f"⚠️ Tên đăng nhập `{BGH_u}` đã tồn tại!")
                    else:
                        new_row = pd.DataFrame([{
                            "username": BGH_u, "password": BGH_p, "name": BGH_name,
                            "role": "campus_admin", "campus_code": BGH_code,
                            "campus": CAMPUS_MAP[BGH_code], "class_name": "Tất cả", "status": "active"
                        }])
                        st.session_state.users_df = pd.concat([st.session_state.users_df, new_row], ignore_index=True)
                        if save_sheet_to_gas("Users", st.session_state.users_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn trên Google Sheets! TK: `{BGH_u}`")
                            st.rerun()

            st.markdown("---")
            st.dataframe(st.session_state.users_df, use_container_width=True)

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ TOÀN HỆ THỐNG")
            st.info("💡 **Admin:** Bạn có thể tự do lọc rút dữ liệu EQ từ kho Google Sheet theo từng Cơ sở, Khối lớp, Giáo viên hoặc Học sinh bên dưới:")
            
            df_eval_raw = st.session_state.evaluations_df
            
            # BỘ LỌC ĐA CẤP ĐỘNG 4 CẤP
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                camp_opts = ["Tất cả cơ sở"] + list(CAMPUS_MAP.values())
                sel_camp = st.selectbox("1. Chọn Cơ sở:", camp_opts, key="sa_sel_camp")
            
            with col_f2:
                class_opts = ["Tất cả các lớp"] + TFA_CLASSES
                sel_class = st.selectbox("2. Chọn Khối Lớp:", class_opts, key="sa_sel_class")
                
            # Lọc sơ bộ để rút Giáo viên
            df_cc = filter_records_multilevel(df_eval_raw, campus=sel_camp, class_name=sel_class)
            t_rec = df_cc["teacher"].dropna().unique().tolist() if not df_cc.empty else []
            t_usr = []
            if "users_df" in st.session_state and not st.session_state.users_df.empty:
                u_df_filt = filter_records_multilevel(st.session_state.users_df, campus=sel_camp, class_name=sel_class)
                if "name" in u_df_filt.columns: t_usr = u_df_filt["name"].dropna().unique().tolist()
            
            all_teachers = sorted(list(set([t for t in t_rec + t_usr if t and str(t).strip() != ""])))
            t_opts = ["Tất cả giáo viên (đã tạo)"] + all_teachers
            
            with col_f3:
                sel_teacher = st.selectbox("3. Chọn Giáo viên (đã tạo):", t_opts, key="sa_sel_teacher")
                
            # Lọc sơ bộ để rút Học sinh
            df_cct = filter_records_multilevel(df_cc, teacher=sel_teacher)
            s_rec = df_cct["student"].dropna().unique().tolist() if not df_cct.empty else []
            all_students = sorted(list(set([s for s in s_rec if s and str(s).strip() != ""])))
            s_opts = ["Tất cả học sinh trong lớp"] + all_students
            
            with col_f4:
                sel_student = st.selectbox("4. Chọn Học sinh:", s_opts, key="sa_sel_student")
                
            # DỮ LIỆU ĐÃ LỌC HOÀN CHỈNH
            df_eval_filtered = filter_records_multilevel(df_eval_raw, campus=sel_camp, class_name=sel_class, teacher=sel_teacher, student=sel_student)
            df_export = format_evaluations_export(df_eval_filtered)
            
            st.markdown(f"##### 📋 Kết Quả Rút Dữ Liệu ({len(df_export)} dòng phù hợp)")
            st.dataframe(df_export, use_container_width=True)
            
            if not df_eval_filtered.empty:
                render_eq_charts(df_eval_filtered, "(Toàn Trường / Đã Lọc)")
            else:
                st.info("ℹ️ Không tìm thấy dữ liệu đánh giá EQ phù hợp với bộ lọc. Bạn vẫn có thể xuất file báo cáo mẫu bên dưới.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Tổng Hợp EQ (Theo Bộ Lọc Đã Chọn)",
                df_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bao_Cao_EQ_Admin_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

        elif main_menu == "📈 3. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XU HƯỚNG PHÁT TRIỂN EQ TOÀN TRƯỜNG")
            df_comp_raw = st.session_state.comparisons_df
            
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                camp_opts = ["Tất cả cơ sở"] + list(CAMPUS_MAP.values())
                sel_camp = st.selectbox("1. Chọn Cơ sở:", camp_opts, key="sa_cmp_camp")
            with col_f2:
                class_opts = ["Tất cả các lớp"] + TFA_CLASSES
                sel_class = st.selectbox("2. Chọn Khối Lớp:", class_opts, key="sa_cmp_class")
                
            df_cc = filter_records_multilevel(df_comp_raw, campus=sel_camp, class_name=sel_class)
            t_rec = df_cc["teacher"].dropna().unique().tolist() if not df_cc.empty else []
            t_opts = ["Tất cả giáo viên (đã tạo)"] + sorted(list(set([t for t in t_rec if t])))
            
            with col_f3:
                sel_teacher = st.selectbox("3. Chọn Giáo viên (đã tạo):", t_opts, key="sa_cmp_teacher")
                
            df_cct = filter_records_multilevel(df_cc, teacher=sel_teacher)
            s_rec = df_cct["student"].dropna().unique().tolist() if not df_cct.empty else []
            s_opts = ["Tất cả học sinh"] + sorted(list(set([s for s in s_rec if s])))
            
            with col_f4:
                sel_student = st.selectbox("4. Chọn Học sinh:", s_opts, key="sa_cmp_student")

            df_comp_filtered = filter_records_multilevel(df_comp_raw, campus=sel_camp, class_name=sel_class, teacher=sel_teacher, student=sel_student)
            df_comp_export = format_comparisons_export(df_comp_filtered)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên EQ")
            st.table(calculate_class_stats(df_comp_filtered))
            
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Xu Hướng EQ (Theo Bộ Lọc)",
                df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bang_Xu_Huong_EQ_Admin_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

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
            f"🏫 1. Tạo & Quản lý Giáo viên ({my_code})",
            f"📊 2. Báo cáo EQ Cơ sở ({my_code})",
            f"📈 3. Bảng So Sánh Xu Hướng ({my_code})"
        ])
        
        if main_menu == f"🏫 1. Tạo & Quản lý Giáo viên ({my_code})":
            st.subheader(f"🏫 BGH QUẢN LÝ VÀ TẠO TÀI KHOẢN GIÁO VIÊN: {my_campus.upper()}")
            
            with st.form(key="form_create_gv", clear_on_submit=True):
                st.markdown("##### ➕ Tạo Tài Khoản Giáo Viên Mới (Gõ xong nhấn Enter)")
                col1, col2, col3 = st.columns([1.5, 2, 1.5])
                with col1: t_class = st.selectbox("Khối Lớp phụ trách:", TFA_CLASSES)
                with col2: t_name = st.text_input("Họ và tên Giáo viên:").strip()
                with col3: t_phone = st.text_input("Số điện thoại (dùng làm SĐT/TK):").strip()
                
                btn_gv = st.form_submit_button("➕ Tạo Tài Khoản Giáo Viên (Hoặc nhấn Enter)")
                
                if btn_gv:
                    if t_phone and t_name:
                        gen_u = f"{t_phone}{my_code}"
                        clean_gen_u = clean_key(gen_u)
                        if clean_gen_u in users_dict:
                            st.warning(f"⚠️ Tài khoản `{gen_u}` đã tồn tại!")
                        else:
                            new_row = pd.DataFrame([{
                                "username": gen_u, "password": "123456", "name": t_name,
                                "role": "teacher", "campus_code": my_code,
                                "campus": my_campus, "class_name": t_class, "status": "active"
                            }])
                            st.session_state.users_df = pd.concat([st.session_state.users_df, new_row], ignore_index=True)
                            if save_sheet_to_gas("Users", st.session_state.users_df):
                                st.success(f"🎉 Đã lưu vĩnh viễn giáo viên {t_name} trên Google Sheets! TK: `{gen_u}`")
                                st.rerun()

            st.markdown("---")
            st.markdown(f"##### 📋 Danh Sách Giáo Viên Cơ Sở {my_code}")
            
            col_campus = "campus_code" if "campus_code" in st.session_state.users_df.columns else "Campus_Code"
            col_role = "role" if "role" in st.session_state.users_df.columns else "Role"
            
            gv_df = st.session_state.users_df[
                (st.session_state.users_df[col_role].apply(clean_key) == 'teacher') & 
                (st.session_state.users_df[col_campus].apply(clean_key) == clean_key(my_code))
            ]
            gv_idx_list = gv_df.index.tolist()
            
            if gv_idx_list:
                for idx in gv_idx_list:
                    row = st.session_state.users_df.loc[idx]
                    u_username = row.get('username', row.get('Username', ''))
                    u_name = row.get('name', row.get('Name', ''))
                    u_class = row.get('class_name', row.get('Class_Name', 'Chưa xếp lớp'))
                    u_status = row.get('status', row.get('Status', 'active'))
                    status_badge = "🟢 Đang hoạt động" if clean_key(u_status) == "active" else "🔴 Đã khóa"
                    
                    c_g1, c_g2, c_g3, c_g4 = st.columns([2.5, 1, 1, 1])
                    with c_g1:
                        st.write(f"👩‍🏫 **{u_name}** | Lớp: `{u_class}` | TK: `{u_username}` | {status_badge}")
                    with c_g2:
                        if st.button("✏️ Sửa", key=f"edit_gv_btn_{idx}"):
                            st.session_state[f"editing_gv_{idx}"] = not st.session_state.get(f"editing_gv_{idx}", False)
                    with c_g3:
                        toggle_txt = "🔒 Khóa" if clean_key(u_status) == "active" else "🔓 Mở khóa"
                        if st.button(toggle_txt, key=f"toggle_gv_{idx}"):
                            new_st = "inactive" if clean_key(u_status) == "active" else "active"
                            st.session_state.users_df.loc[idx, 'status'] = new_st
                            if save_sheet_to_gas("Users", st.session_state.users_df):
                                st.success(f"Đã chuyển trạng thái TK **{u_name}** sang `{new_st}`!")
                                st.rerun()
                    with c_g4:
                        if st.button("🗑️ Xóa", key=f"del_gv_{idx}"):
                            st.session_state.users_df = st.session_state.users_df.drop(idx).reset_index(drop=True)
                            if save_sheet_to_gas("Users", st.session_state.users_df):
                                st.success(f"Đã xóa tài khoản giáo viên **{u_name}**!")
                                st.rerun()

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            st.subheader(f"📊 BÁO CÁO TỔNG HỢP EQ CƠ SỞ: {my_campus.upper()}")
            st.info("💡 **BGH:** Bạn có thể tự do lọc rút dữ liệu EQ trực tiếp từ kho Google Sheet theo Khối lớp, Giáo viên (đã tạo) hoặc Học sinh:")
            
            df_eval_raw = st.session_state.evaluations_df
            
            # BỘ LỌC ĐA CẤP 3 CẤP CHO BGH
            col_bgh1, col_bgh2, col_bgh3 = st.columns(3)
            with col_bgh1:
                class_opts = ["Tất cả các lớp trong cơ sở"] + TFA_CLASSES
                bgh_sel_class = st.selectbox("1. Chọn Khối Lớp:", class_opts, key="bgh_sel_class")
                
            # Lọc sơ bộ theo Campus + Class
            df_c_cc = filter_records_multilevel(df_eval_raw, campus=my_campus, class_name=bgh_sel_class)
            t_rec = df_c_cc["teacher"].dropna().unique().tolist() if not df_c_cc.empty else []
            t_usr = []
            if "users_df" in st.session_state and not st.session_state.users_df.empty:
                u_df = filter_records_multilevel(st.session_state.users_df, campus=my_campus, class_name=bgh_sel_class)
                if "name" in u_df.columns: t_usr = u_df["name"].dropna().unique().tolist()
            
            bgh_teachers = sorted(list(set([t for t in t_rec + t_usr if t and str(t).strip() != ""])))
            bgh_t_opts = ["Tất cả giáo viên (đã tạo)"] + bgh_teachers
            
            with col_bgh2:
                bgh_sel_teacher = st.selectbox("2. Chọn Giáo viên (đã tạo):", bgh_t_opts, key="bgh_sel_teacher")
                
            # Lọc tiếp theo Teacher
            df_c_cct = filter_records_multilevel(df_c_cc, teacher=bgh_sel_teacher)
            s_rec = df_c_cct["student"].dropna().unique().tolist() if not df_c_cct.empty else []
            bgh_students = sorted(list(set([s for s in s_rec if s and str(s).strip() != ""])))
            bgh_s_opts = ["Tất cả học sinh trong lớp"] + bgh_students
            
            with col_bgh3:
                bgh_sel_student = st.selectbox("3. Chọn Học sinh:", bgh_s_opts, key="bgh_sel_student")

            # DỮ LIỆU ĐÃ LỌC BGH
            df_eval_bgh_filt = filter_records_multilevel(df_eval_raw, campus=my_campus, class_name=bgh_sel_class, teacher=bgh_sel_teacher, student=bgh_sel_student)
            df_export = format_evaluations_export(df_eval_bgh_filt)
            
            st.markdown(f"##### 📋 Kết Quả Rút Dữ Liệu Cơ Sở ({len(df_export)} dòng)")
            st.dataframe(df_export, use_container_width=True)
            
            if not df_eval_bgh_filt.empty:
                render_eq_charts(df_eval_bgh_filt, f"({my_code})")
            else:
                st.info("ℹ️ Không tìm thấy dữ liệu đánh giá EQ phù hợp. Bạn vẫn có thể tải Khung Báo Cáo Mẫu bên dưới.")
                
            st.download_button(
                f"📥 Xuất File CSV/Excel Báo Cáo EQ Cơ Sở {my_code}",
                df_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bao_Cao_EQ_{my_code}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

        else:
            st.subheader(f"📈 BẢNG SO SÁNH XU HƯỚNG EQ CƠ SỞ: {my_campus.upper()}")
            df_comp_raw = st.session_state.comparisons_df
            
            col_bgh1, col_bgh2, col_bgh3 = st.columns(3)
            with col_bgh1:
                class_opts = ["Tất cả các lớp trong cơ sở"] + TFA_CLASSES
                bgh_sel_class = st.selectbox("1. Chọn Khối Lớp:", class_opts, key="bgh_cmp_class")
                
            df_c_cc = filter_records_multilevel(df_comp_raw, campus=my_campus, class_name=bgh_sel_class)
            t_rec = df_c_cc["teacher"].dropna().unique().tolist() if not df_c_cc.empty else []
            bgh_t_opts = ["Tất cả giáo viên (đã tạo)"] + sorted(list(set([t for t in t_rec if t])))
            
            with col_bgh2:
                bgh_sel_teacher = st.selectbox("2. Chọn Giáo viên (đã tạo):", bgh_t_opts, key="bgh_cmp_teacher")
                
            df_c_cct = filter_records_multilevel(df_c_cc, teacher=bgh_sel_teacher)
            s_rec = df_c_cct["student"].dropna().unique().tolist() if not df_c_cct.empty else []
            bgh_s_opts = ["Tất cả học sinh trong lớp"] + sorted(list(set([s for s in s_rec if s])))
            
            with col_bgh3:
                bgh_sel_student = st.selectbox("3. Chọn Học sinh:", bgh_s_opts, key="bgh_cmp_student")

            df_comp_bgh_filt = filter_records_multilevel(df_comp_raw, campus=my_campus, class_name=bgh_sel_class, teacher=bgh_sel_teacher, student=bgh_sel_student)
            df_comp_export = format_comparisons_export(df_comp_bgh_filt)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Thống Kê Biến Thiên EQ Cơ Sở")
            st.table(calculate_class_stats(df_comp_bgh_filt))
            
            st.download_button(
                f"📥 Xuất File CSV/Excel Bảng Xu Hướng EQ Cơ Sở {my_code}",
                df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bang_Xu_Huong_EQ_{my_code}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

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
            st.subheader(f"🏫 THÊM & QUẢN LÝ DANH SÁCH HỌC SINH - LỚP: {user_info.get('class_name', '')}")
            with st.form(key="form_add_student", clear_on_submit=True):
                col_std1, col_std2 = st.columns(2)
                with col_std1: new_student_val = st.text_input("👦👧 Họ và tên Bé (Học sinh):", placeholder="VD: Nguyễn Văn A")
                with col_std2: new_student_note = st.text_input("📌 Ghi chú đặc biệt / Lưu ý về trẻ:", placeholder="VD: Cần hỗ trợ 1-1, dị ứng...")
                btn_std = st.form_submit_button("➕ Thêm Học Sinh")
                if btn_std:
                    clean_name = new_student_val.strip()
                    clean_note = new_student_note.strip()
                    if clean_name:
                        t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
                        s_col = "student_name" if "student_name" in st.session_state.students_df.columns else "Student_Name"
                        existing_mask = (
                            (st.session_state.students_df[t_col].apply(clean_key) == clean_key(user_key)) &
                            (st.session_state.students_df[s_col].apply(clean_key) == clean_key(clean_name))
                        )
                        if existing_mask.any():
                            st.session_state.students_df.loc[existing_mask, "student_note"] = clean_note
                        else:
                            new_std_row = pd.DataFrame([{
                                "teacher_user": clean_key(user_key), "student_name": clean_name, "student_note": clean_note
                            }])
                            st.session_state.students_df = pd.concat([st.session_state.students_df, new_std_row], ignore_index=True)
                        if save_sheet_to_gas("Students", st.session_state.students_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn bé **{clean_name}** vào danh sách lớp!")
                            st.rerun()

            st.markdown("---")
            st.markdown("##### 📋 Danh Sách Học Sinh Trong Lớp")
            t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
            my_stds_df = filter_df_by_clean_col(st.session_state.students_df, t_col, user_key)
            if not my_stds_df.empty:
                st.dataframe(my_stds_df[["student_name", "student_note"]], use_container_width=True)
            else:
                st.info("Lớp chưa có học sinh nào. Vui lòng thêm học sinh ở biểu mẫu trên.")

        elif main_menu == "📊 5. Báo cáo & Xuất File Lớp":
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ VÀ XU HƯỚNG CỦA LỚP")
            t_col = "teacher" if "teacher" in st.session_state.evaluations_df.columns else "Teacher"
            df_my_eval = filter_df_by_clean_col(st.session_state.evaluations_df, t_col, user_info['name'])
            df_my_eval_export = format_evaluations_export(df_my_eval)
            
            st.markdown("##### 1. Bảng Đánh Giá EQ 6 Tiêu Chí Của Lớp")
            st.dataframe(df_my_eval_export, use_container_width=True)
            
            st.markdown("---")
            st.markdown("##### 2. Bảng Xu Hướng & So Sánh EQ Của Lớp")
            tc_col = "teacher" if "teacher" in st.session_state.comparisons_df.columns else "Teacher"
            df_my_comp = filter_df_by_clean_col(st.session_state.comparisons_df, tc_col, user_info['name'])
            df_my_comp_export = format_comparisons_export(df_my_comp)
            
            st.dataframe(df_my_comp_export, use_container_width=True)
            
            col_dwn1, col_dwn2 = st.columns(2)
            with col_dwn1:
                st.download_button(
                    "📥 Xuất CSV/Excel Bảng Tổng Hợp EQ Lớp",
                    df_my_eval_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bao_Cao_EQ_Lop_{user_info['name']}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
                )
            with col_dwn2:
                st.download_button(
                    "📥 Xuất CSV/Excel Bảng Xu Hướng EQ Lớp",
                    df_my_comp_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bang_Xu_Huong_EQ_Lop_{user_info['name']}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
                )
