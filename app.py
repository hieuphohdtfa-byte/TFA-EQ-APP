import streamlit as st
import pandas as pd
import requests
import os
import json
import re
import unicodedata
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 🔗 KẾT NỐI VỚI GOOGLE SHEET QUA WEB APP URL
# -----------------------------------------------------------------------------
GAS_URL = "https://script.google.com/macros/s/AKfycbyLmKWVgiMnLk94OL1bjAVROT0jl-JhplqFmm1jpvIJMqZnUfzJUirRQMfyJsjgX34cPQ/exec"

# -----------------------------------------------------------------------------
# 🛠️ HÀM CHUẨN HÓA TIẾNG VIỆT & CHUỖI TÌM KIẾM AN TOÀN TUYỆT ĐỐI
# -----------------------------------------------------------------------------
def remove_accents_vn(s):
    if not s: return ""
    s = str(s).replace("Đ", "D").replace("đ", "d")
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def clean_col_key(k):
    return remove_accents_vn(k).replace(" ", "").replace("_", "").replace("-", "")

def digits_only(s):
    return re.sub(r'\D', '', str(s or ''))

def clean_key(val):
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip().lower()
    s = s.replace(".0", "")
    if s in ["nan", "none"]:
        return ""
    if s.startswith("0") and len(s) > 1:
        s = s[1:]
    return s

def clean_date_str(d_val):
    if not d_val: return ""
    s = str(d_val).strip()
    s = s.split('T')[0].split(' ')[0]
    
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y', '%Y/%m/%d'):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%d/%m/%Y')
        except ValueError:
            pass
            
    parts = s.replace('-', '/').split('/')
    if len(parts) == 3:
        if len(parts[0]) == 4:
            y, m, d = parts[0], parts[1].zfill(2), parts[2].zfill(2)
            return f"{d}/{m}/{y}"
        else:
            d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
            return f"{d}/{m}/{y}"
    return s

SHEET_ALIASES = {
    'Users': ['users', 'user', 'taikhoan', 'giaovien', 'danhsachgiaovien', 'danhsachtaikhoan', 'tk'],
    'Students': ['students', 'student', 'hocsinh', 'danhsachhocsinh', 'tenbe', 'be', 'tre', 'danhsachtre'],
    'DailyLogs': ['dailylogs', 'dailylog', 'nhatky', 'nhatkycamxuc', 'hosocamxuc', 'nhatkyhangngay', 'logs', 'log'],
    'Evaluations': ['evaluations', 'evaluation', 'danhgia', 'danhgiaeq', 'tieuchi', 'phieudanhgia', 'evals', 'eval'],
    'Comparisons': ['comparisons', 'comparison', 'sosanh', 'sosanheq', 'xuhuong', 'bangsosanh', 'comps', 'comp']
}

def get_gas_sheet_rows(gas_data, sheet_name):
    if not isinstance(gas_data, dict):
        return []
        
    for sub_key in ['data', 'result', 'sheets', 'payload']:
        if sub_key in gas_data and isinstance(gas_data[sub_key], dict):
            gas_data = gas_data[sub_key]
            break

    aliases = SHEET_ALIASES.get(sheet_name, [sheet_name.lower()])
    
    for k, v in gas_data.items():
        clean_k = remove_accents_vn(k).replace(' ', '').replace('_', '').replace('-', '')
        for alias in aliases:
            if alias in clean_k or clean_k in alias:
                if isinstance(v, list):
                    return v
                elif isinstance(v, dict):
                    return [v]
    return []

def filter_teacher_records(df, teacher_cols, user_info):
    if df is None or df.empty or not user_info:
        return pd.DataFrame()
        
    target_col = None
    for c in teacher_cols:
        if c in df.columns:
            target_col = c
            break
            
    if not target_col:
        return pd.DataFrame()
        
    u_name = str(user_info.get('raw_username', '') or user_info.get('username', '')).strip()
    u_fullname = str(user_info.get('name', '')).strip()
    u_digits = digits_only(u_name)
    
    clean_u_name = clean_key(u_name)
    clean_u_fullname = clean_key(u_fullname)
    
    def matches_row(val):
        if val is None or pd.isna(val): return False
        v_str = str(val).strip()
        v_clean = clean_key(v_str)
        v_digits = digits_only(v_str)
        
        if v_clean and (v_clean == clean_u_name or v_clean == clean_u_fullname):
            return True
        if u_digits and len(u_digits) >= 8 and v_digits and len(v_digits) >= 8:
            if u_digits in v_digits or v_digits in u_digits:
                return True
        if clean_u_fullname and len(clean_u_fullname) > 3 and v_clean and len(v_clean) > 3:
            if clean_u_fullname in v_clean or v_clean in clean_u_fullname:
                return True
        return False
        
    mask = df[target_col].apply(matches_row)
    return df[mask]

def filter_df_by_campus(df, campus_val):
    if df is None or df.empty or not campus_val:
        return pd.DataFrame()
    c_cols = ['campus', 'coso', 'campus_code', 'Campus', 'CoSo']
    target_col = None
    for c in c_cols:
        if c in df.columns:
            target_col = c
            break
    if not target_col:
        return pd.DataFrame()
    
    clean_target = remove_accents_vn(campus_val)
    def campus_matches(val):
        if not val or pd.isna(val): return False
        v_clean = remove_accents_vn(val)
        return clean_target in v_clean or v_clean in clean_target
        
    return df[df[target_col].apply(campus_matches)]

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
            color: #8C6200;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 13px;
            display: inline-block;
            margin: 4px;
        }
        .note-badge {
            background-color: #E3F2FD;
            color: #0D47A1;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            display: inline-block;
            margin-top: 4px;
        }

        /* 📱 TỐI ƯU HÓA RIÊNG MÀN HÌNH ĐIỆN THOẠI (< 768px) */
        @media (max-width: 768px) {
            .stApp { padding: 8px !important; }
            .main-header { padding: 14px 16px !important; text-align: center; }
            .main-header h2 { font-size: 18px !important; }
            .main-header p { font-size: 12px !important; }
            
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 8px !important;
            }
            
            .stButton>button {
                padding: 14px 16px !important;
                font-size: 16px !important;
            }
            
            div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. BỘ TIÊU CHÍ EQ NGUYÊN BẢN CHO CẢ 3 KHỐI LỚP
# -----------------------------------------------------------------------------
CAMPUS_MAP = {
    "HD": "Cơ sở TFA Hà Đô (Phường Cát Lái, TP.HCM)",
    "HL": "Cơ sở TFA Him Lam (Phường Tân Hưng, TP.HCM)",
    "DBM": "Cơ sở TFA Dương Bạch Mai (Phường Chánh Hưng, TP.HCM)",
    "LVS": "Cơ sở TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)",
    "TTL": "Cơ sở TFA Trần Thị Lý (Phường Hòa Cường, TP.Đà Nẵng)"
}

TFA_CLASSES = ["Pre-school (3-4 tuổi)", "Kindergarten (4-5 tuổi)", "Pre-primary (5-6 tuổi)"]
SCHOOL_YEAR_OPTIONS = ["2024 - 2025", "2025 - 2026", "2026 - 2027", "2027 - 2028"]

TFA_ROUTINES = [
    "Đón trẻ - Thể dục sáng", "Ăn sáng", "Hoạt động có chủ đích",
    "Ăn trưa", "Ăn xế", "Hoạt động chiều", "Trả trẻ", "Tình huống phát sinh"
]
EMOTION_COLS = ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng 😮‍💨", "Tự hào 🌟"]

LOGO_FILE = "logo.png" if os.path.exists("logo.png") else ("Logo TFA Ver2.1 .png" if os.path.exists("Logo TFA Ver2.1 .png") else "logo.png")

CRITERIA_DATA = {
    "Pre-school (3-4 tuổi)": {
        "TC1": {1: "Mức 1: Khóc/giận/vui nhưng không biết vì sao.", 2: "Mức 2: Nhận diện khi cô hỏi trực tiếp.", 3: "Mức 3: Tự dùng từ đơn để nói cảm xúc.", 4: "Mức 4: Tự nhận ra sớm trước khi bộc phát."},
        "TC2": {1: "Mức 1: Biểu đạt cảm xúc qua phản ứng sinh lý.", 2: "Mức 2: Nói 1 từ đơn gọi tên cảm xúc.", 3: "Mức 3: Nói câu đơn giản định danh cảm xúc.", 4: "Mức 4: Diễn đạt kèm nguyên nhân sơ khai."},
        "TC3": {1: "Mức 1: Bùng nổ kéo dài > 5 phút.", 2: "Mức 2: Bình tĩnh khi cô ôm trấn an.", 3: "Mức 3: Nghe hướng dẫn cô để tự dịu lại.", 4: "Mức 4: Tự tìm góc bình tĩnh không cần cô."},
        "TC4": {1: "Mức 1: Thờ ơ khi thấy bạn khóc/đau.", 2: "Mức 2: Dừng lại quan sát bạn.", 3: "Mức 3: Biết an ủi, vuốt lưng cho bạn.", 4: "Mức 4: Chủ động chia sẻ, rủ bạn chơi chung."},
        "TC5": {1: "Mức 1: Dễ bùng nổ khi môi trường đổi.", 2: "Mức 2: Rụt rè khi có yếu tố lạ.", 3: "Mức 3: Thích nghi có điều kiện.", 4: "Mức 4: Giữ tâm trạng ổn định dù môi trường đổi."},
        "TC6": {1: "Mức 1: Không hợp tác khi cô dỗ.", 2: "Mức 2: Dịu lại nhưng chưa hợp tác ngay.", 3: "Mức 3: Hợp tác sau khi được công nhận.", 4: "Mức 4: Tự giải tỏa, chủ động tìm cô."}
    },
    "Kindergarten (4-5 tuổi)": {
        "TC1": {1: "Mức 1: Nói cảm xúc nhưng chưa rõ lý do.", 2: "Mức 2: Trả lời nguyên nhân khi cô gợi ý.", 3: "Mức 3: Dùng câu ghép giải thích cảm xúc.", 4: "Mức 4: Tự điều chỉnh hành vi từ sớm."},
        "TC2": {1: "Mức 1: Kiểm soát hành vi bản năng.", 2: "Mức 2: Tự gọi tên cảm xúc câu ngắn.", 3: "Mức 3: Nói rõ mối quan hệ nhân-quả.", 4: "Mức 4: Biểu đạt cảm xúc kèm mong muốn."},
        "TC3": {1: "Mức 1: Bộc phát hành vi ăn vạ lâu.", 2: "Mức 2: Phối hợp hít thở/uống nước cùng cô.", 3: "Mức 3: Tự nói từ khích lệ bản thân.", 4: "Mức 4: Chủ động tách khỏi nguồn xung đột."},
        "TC4": {1: "Mức 1: Nhận biết cảm xúc bạn qua nét mặt.", 2: "Mức 2: An ủi, vỗ vai hoặc giúp đỡ bạn.", 3: "Mức 3: Chủ động chia sẻ không cần nhắc.", 4: "Mức 4: Mời bạn chơi, hòa giải mâu thuẫn."},
        "TC5": {1: "Mức 1: Lo lắng khi ngoại cảnh thay đổi.", 2: "Mức 2: Nói cho cô biết sự khó chịu.", 3: "Mức 3: Chọn góc yên tĩnh phù hợp.", 4: "Mức 4: Chủ động giữ trật tự cùng lớp."},
        "TC6": {1: "Mức 1: Giảm phản ứng khi cô gọi tên cảm xúc.", 2: "Mức 2: Kể lại sự việc khi cô xoa dịu.", 3: "Mức 3: Chủ động xin lỗi / làm hòa với bạn.", 4: "Mức 4: Đưa lời hứa không lặp lại."}
    },
    "Pre-primary (5-6 tuổi)": {
        "TC1": {1: "Mức 1: Nói cảm xúc chung chung.", 2: "Mức 2: Dùng từ cảm xúc bậc cao (tự hào, hồi hộp).", 3: "Mức 3: Giải thích chi tiết nguyên nhân.", 4: "Mức 4: Dự báo cường độ cảm xúc điềm tĩnh."},
        "TC2": {1: "Mức 1: Cảm xúc mạnh chỉ dùng hành động.", 2: "Mức 2: Trả lời khi cô cho lựa chọn từ.", 3: "Mức 3: Nói từ vựng sắc thái rõ ràng.", 4: "Mức 4: Kết nối Ngôn ngữ - Logic - Cảm xúc trọn vẹn."},
        "TC3": {1: "Mức 1: Mất kiểm soát > 10 phút.", 2: "Mức 2: Hồi phục 5-7 phút nhờ cô hướng dẫn.", 3: "Mức 3: Tự điều chỉnh 80%, hồi phục 3-5 phút.", 4: "Mức 4: Tự phục hồi cực nhanh < 2 phút."},
        "TC4": {1: "Mức 1: Tự phục vụ bản thân là chính.", 2: "Mức 2: Biết quan tâm khi cô định hướng.", 3: "Mức 3: Biết thương lượng: 'Tớ chơi trước, cậu chơi sau'.", 4: "Mức 4: Dẫn dắt nhóm, tôn trọng sự khác biệt."},
        "TC5": {1: "Mức 1: Dễ thu mình trước thay đổi lớn.", 2: "Mức 2: Nhận biết môi trường ồn nhưng chờ cô.", 3: "Mức 3: Tự di chuyển ra chỗ yên tĩnh.", 4: "Mức 4: Duy trì thái độ tích cực mọi hoàn cảnh."},
        "TC6": {1: "Mức 1: Cần > 15 phút để dịu lại.", 2: "Mức 2: Chấp nhận đồng cảm nhưng thụ động.", 3: "Mức 3: Phản hồi tích cực, gật đầu chia sẻ.", 4: "Mức 4: Cảm ơn người lắng nghe, tìm hướng giải quyết."}
    }
}

# -----------------------------------------------------------------------------
# 🤖 THUẬT TOÁN MA TRẬN TỰ ĐỘNG TỔNG HỢP EQ
# -----------------------------------------------------------------------------
def auto_map_daily_to_criteria(student_name, teacher_name, daily_df):
    if daily_df is None or daily_df.empty: return None
    
    std_logs = filter_teacher_records(daily_df, ['teacher', 'giaovien', 'Teacher'], {'name': teacher_name, 'raw_username': teacher_name})
    if std_logs.empty:
        s_col = 'student' if 'student' in daily_df.columns else ('hocsinh' if 'hocsinh' in daily_df.columns else 'Student')
        std_logs = daily_df[daily_df[s_col].apply(clean_key) == clean_key(student_name)] if s_col in daily_df.columns else pd.DataFrame()
        
    if std_logs.empty: return None
        
    neg_count, pos_count, total_logs = 0, 0, len(std_logs)
    context_evidences = []
    
    emo_col = "emotions" if "emotions" in std_logs.columns else ("camxuc" if "camxuc" in std_logs.columns else "Emotions")
    note_col = "note" if "note" in std_logs.columns else ("ghichu" if "ghichu" in std_logs.columns else "Note")
    interv_col = "intervention" if "intervention" in std_logs.columns else ("canthiep" if "canthiep" in std_logs.columns else "Intervention")
    date_col = "date" if "date" in std_logs.columns else ("ngay" if "ngay" in std_logs.columns else "Date")
    
    for _, row in std_logs.iterrows():
        emotions_text = str(row.get(emo_col, ''))
        note = str(row.get(note_col, '')).strip()
        interv = str(row.get(interv_col, '')).strip()
        dt_str = clean_date_str(row.get(date_col, ''))
        
        if any(e in emotions_text for e in ["Buồn", "Giận", "Lo lắng"]): neg_count += 1
        if any(e in emotions_text for e in ["Vui", "Hào hứng", "Yêu thương", "Tự hào"]): pos_count += 1
        
        if note or interv:
            context_evidences.append(f"• {dt_str}: {emotions_text} | Bối cảnh: {note} | Cô hỗ trợ: {interv}")

    auto_tc3 = 1 if neg_count > total_logs * 0.4 else (2 if neg_count > 0 else 3)
    auto_tc1 = 1 if neg_count > total_logs * 0.5 else (2 if neg_count > 2 else (4 if pos_count > total_logs * 0.7 else 3))
    auto_peq = round((auto_tc1*2 + auto_tc3*4) / 6.0, 2)
    auto_group = "DUY TRÌ" if auto_peq >= 3.2 else ("CẦN CẢI THIỆN" if auto_peq >= 2.0 else "HỖ TRỢ ĐẶC BIỆT")
    
    evidence_str = "\n".join(context_evidences[:5]) if context_evidences else "Bé sinh hoạt ổn định trong tháng."
    return {
        "TC1": auto_tc1, "TC2": auto_tc1, "TC3": auto_tc3, "TC4": 3, "TC5": 3, "TC6": auto_tc3,
        "P_EQ": auto_peq, "Group_Clean": auto_group,
        "Context": f"Tổng hợp {total_logs} ngày theo dõi:\n{evidence_str}",
        "Conclusion": f"Bé {student_name} đạt điểm PEQ={auto_peq}, thuộc nhóm {auto_group}.",
        "Plan": f"Kế hoạch tác động: Tiếp tục đồng hành và hỗ trợ bé duy trì/cải thiện cảm xúc."
    }

# -----------------------------------------------------------------------------
# 3. ĐỒNG BỘ GOOGLE SHEET & CHUẨN HÓA DỮ LIỆU
# -----------------------------------------------------------------------------
DEFAULT_USERS_DF = pd.DataFrame([
    {"username": "admin", "password": "admin123", "name": "Ban Giám Hiệu Tổng (Toàn Hệ Thống)", "role": "super_admin", "campus_code": "ALL", "campus": "Tất cả cơ sở", "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHD", "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin", "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHTTL", "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin", "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHDBM", "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin", "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHL", "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin", "campus_code": "HL", "campus": CAMPUS_MAP["HL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHLVS", "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin", "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"], "class_name": "Tất cả", "status": "active"}
])

def normalize_users_df(raw_rows, default_df):
    if not raw_rows: return default_df
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        row_clean = {}
        for k, v in r.items():
            k_clean = clean_col_key(k)
            val_clean = str(v).strip() if v is not None else ''
            
            if k_clean in ['username', 'user', 'tk', 'tendangnhap', 'taikhoan', 'taikhoangv', 'sdt', 'sodienthoai', 'magv', 'magiaovien', 'phone']:
                row_clean['username'] = val_clean
            elif k_clean in ['password', 'pass', 'matkhau', 'mk', 'passwordhash']:
                row_clean['password'] = val_clean
            elif k_clean in ['name', 'hoten', 'hovaten', 'tengiaovien', 'tengv', 'ten', 'fullname']:
                row_clean['name'] = val_clean
            elif k_clean in ['role', 'vaitro', 'phanquyen', 'chucvu']:
                row_clean['role'] = val_clean
            elif k_clean in ['campuscode', 'macoso', 'code']:
                row_clean['campus_code'] = val_clean
            elif k_clean in ['campus', 'coso', 'tencoso', 'truong', 'chinhanh']:
                row_clean['campus'] = val_clean
            elif k_clean in ['classname', 'class', 'lop', 'tenlop', 'khoilop', 'khoi']:
                row_clean['class_name'] = val_clean
            elif k_clean in ['status', 'trangthai', 'tinhtrang']:
                row_clean['status'] = val_clean
            else:
                row_clean[k_clean] = val_clean
        norm_rows.append(row_clean)
        
    df = pd.DataFrame(norm_rows)
    for c in ['username', 'password', 'name', 'role', 'campus_code', 'campus', 'class_name', 'status']:
        if c not in df.columns: df[c] = ''
    all_df = pd.concat([default_df, df], ignore_index=True)
    all_df["_u"] = all_df["username"].apply(clean_key)
    return all_df[all_df["_u"] != ""].drop_duplicates(subset=["_u"], keep="last").drop(columns=["_u"])

def normalize_students_df(raw_rows):
    if not raw_rows: return pd.DataFrame(columns=['teacher_user', 'student_name', 'student_note'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        row_clean = {}
        for k, v in r.items():
            k_clean = clean_col_key(k)
            val_clean = str(v).strip() if v is not None else ''
            
            if k_clean in ['teacheruser', 'teacher', 'teacherusername', 'tuser', 'user', 'giaovien', 'tkgiaovien', 'magiaovien', 'magv', 'sdt', 'sdtgiaovien', 'sdtgv', 'tendangnhap']:
                row_clean['teacher_user'] = val_clean
            elif k_clean in ['studentname', 'student', 'sname', 'tenhocsinh', 'hocsinh', 'tenbe', 'be', 'hotenhocsinh', 'hotenbe', 'ten']:
                row_clean['student_name'] = val_clean
            elif k_clean in ['studentnote', 'note', 'ghichu', 'luuy', 'dacdiem', 'ghichudacbiet']:
                row_clean['student_note'] = val_clean
            else:
                row_clean[k_clean] = val_clean
        norm_rows.append(row_clean)
        
    df = pd.DataFrame(norm_rows)
    for c in ['teacher_user', 'student_name', 'student_note']:
        if c not in df.columns: df[c] = ''
    return df

def normalize_dailylogs_df(raw_rows):
    if not raw_rows: return pd.DataFrame(columns=['teacher', 'campus', 'class', 'student', 'date', 'routine', 'emotions', 'note', 'intervention', 'summary', 'details_json'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        row_clean = {}
        for k, v in r.items():
            k_clean = clean_col_key(k)
            val_clean = str(v).strip() if v is not None else ''
            
            if k_clean in ['teacher', 'giaovien', 'tengiaovien', 'magiaovien', 'magv', 'teacheruser', 'user', 'sdt']:
                row_clean['teacher'] = val_clean
            elif k_clean in ['campus', 'coso', 'tencoso', 'truong', 'chinhanh']:
                row_clean['campus'] = val_clean
            elif k_clean in ['class', 'lop', 'tenlop', 'khoilop', 'classname']:
                row_clean['class'] = val_clean
            elif k_clean in ['student', 'hocsinh', 'tenhocsinh', 'tenbe', 'be', 'hoten']:
                row_clean['student'] = val_clean
            elif k_clean in ['date', 'ngay', 'ngaynhap', 'ngaytao', 'time']:
                row_clean['date'] = clean_date_str(val_clean)
            elif k_clean in ['routine', 'hoatdong', 'thoigian', 'sinhhoat']:
                row_clean['routine'] = val_clean
            elif k_clean in ['emotions', 'camxuc', 'trangthai', 'bieuhien']:
                row_clean['emotions'] = val_clean
            elif k_clean in ['note', 'ghichu', 'boicanh', 'mota', 'dienbien']:
                row_clean['note'] = val_clean
            elif k_clean in ['intervention', 'canthiep', 'cocanthiep', 'hotro', 'xuly']:
                row_clean['intervention'] = val_clean
            elif k_clean in ['summary', 'nhanxet', 'danhgia', 'nhanxetchung', 'xuhuong']:
                row_clean['summary'] = val_clean
            elif k_clean in ['detailsjson', 'details', 'chitietjson', 'chitiet', 'json']:
                row_clean['details_json'] = val_clean
            else:
                row_clean[k_clean] = val_clean
        norm_rows.append(row_clean)
        
    df = pd.DataFrame(norm_rows)
    for c in ['teacher', 'campus', 'class', 'student', 'date', 'routine', 'emotions', 'note', 'intervention', 'summary', 'details_json']:
        if c not in df.columns: df[c] = ''
    return df

def normalize_evaluations_df(raw_rows):
    if not raw_rows: return pd.DataFrame(columns=['teacher', 'campus', 'class', 'student', 'school_year', 'term', 'eval_date', 'tc1', 'tc2', 'tc3', 'tc4', 'tc5', 'tc6', 'p_eq', 'group_clean', 'context', 'conclusion', 'plan'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        row_clean = {}
        for k, v in r.items():
            k_clean = clean_col_key(k)
            val_clean = str(v).strip() if v is not None else ''
            
            if k_clean in ['teacher', 'giaovien', 'tengiaovien', 'magiaovien', 'magv', 'sdt']:
                row_clean['teacher'] = val_clean
            elif k_clean in ['campus', 'coso', 'tencoso', 'truong', 'chinhanh']:
                row_clean['campus'] = val_clean
            elif k_clean in ['class', 'lop', 'tenlop', 'khoilop', 'classname']:
                row_clean['class'] = val_clean
            elif k_clean in ['student', 'hocsinh', 'tenhocsinh', 'tenbe', 'be', 'hoten']:
                row_clean['student'] = val_clean
            elif k_clean in ['schoolyear', 'namhoc', 'nam']:
                row_clean['school_year'] = val_clean
            elif k_clean in ['term', 'ky', 'hocky', 'thang', 'dot']:
                row_clean['term'] = val_clean
            elif k_clean in ['evaldate', 'ngay', 'ngaydanhgia', 'date']:
                row_clean['eval_date'] = clean_date_str(val_clean)
            elif k_clean in ['tc1', 'tieuchi1']: row_clean['tc1'] = val_clean
            elif k_clean in ['tc2', 'tieuchi2']: row_clean['tc2'] = val_clean
            elif k_clean in ['tc3', 'tieuchi3']: row_clean['tc3'] = val_clean
            elif k_clean in ['tc4', 'tieuchi4']: row_clean['tc4'] = val_clean
            elif k_clean in ['tc5', 'tieuchi5']: row_clean['tc5'] = val_clean
            elif k_clean in ['tc6', 'tieuchi6']: row_clean['tc6'] = val_clean
            elif k_clean in ['peq', 'peqscore', 'diemtb', 'diempeq', 'trungbinh']:
                row_clean['p_eq'] = val_clean
            elif k_clean in ['groupclean', 'nhom', 'nhomtrangthai', 'xeploai', 'nhompeq']:
                row_clean['group_clean'] = val_clean
            elif k_clean in ['context', 'boicanh', 'minhchung', 'mota']:
                row_clean['context'] = val_clean
            elif k_clean in ['conclusion', 'ketluan', 'ketluanxuhuong']:
                row_clean['conclusion'] = val_clean
            elif k_clean in ['plan', 'kehoach', 'kehoachtagdong', 'huongxuly']:
                row_clean['plan'] = val_clean
            else:
                row_clean[k_clean] = val_clean
        norm_rows.append(row_clean)
        
    df = pd.DataFrame(norm_rows)
    for c in ['teacher', 'campus', 'class', 'student', 'school_year', 'term', 'eval_date', 'tc1', 'tc2', 'tc3', 'tc4', 'tc5', 'tc6', 'p_eq', 'group_clean', 'context', 'conclusion', 'plan']:
        if c not in df.columns: df[c] = ''
    return df

def normalize_comparisons_df(raw_rows):
    if not raw_rows: return pd.DataFrame(columns=['teacher', 'campus', 'class', 'student', 'school_year', 'comp_type', 'period_1', 'period_2', 'score_term1', 'score_term2', 'delta', 'trend', 'conclusion', 'plan', 'comp_date'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        row_clean = {}
        for k, v in r.items():
            k_clean = clean_col_key(k)
            val_clean = str(v).strip() if v is not None else ''
            
            if k_clean in ['teacher', 'giaovien', 'tengiaovien', 'magiaovien', 'magv', 'sdt']:
                row_clean['teacher'] = val_clean
            elif k_clean in ['campus', 'coso', 'tencoso', 'truong', 'chinhanh']:
                row_clean['campus'] = val_clean
            elif k_clean in ['class', 'lop', 'tenlop', 'khoilop', 'classname']:
                row_clean['class'] = val_clean
            elif k_clean in ['student', 'hocsinh', 'tenhocsinh', 'tenbe', 'be', 'hoten']:
                row_clean['student'] = val_clean
            elif k_clean in ['schoolyear', 'namhoc', 'nam']:
                row_clean['school_year'] = val_clean
            elif k_clean in ['comptype', 'loaisosanh', 'hinhthuc']:
                row_clean['comp_type'] = val_clean
            elif k_clean in ['period1', 'dot1', 'ky1', 'thang1']:
                row_clean['period_1'] = val_clean
            elif k_clean in ['period2', 'dot2', 'ky2', 'thang2']:
                row_clean['period_2'] = val_clean
            elif k_clean in ['scoreterm1', 'diemdot1', 'diemky1']:
                row_clean['score_term1'] = val_clean
            elif k_clean in ['scoreterm2', 'diemdot2', 'diemky2']:
                row_clean['score_term2'] = val_clean
            elif k_clean in ['delta', 'bienthien', 'chenhlech']:
                row_clean['delta'] = val_clean
            elif k_clean in ['trend', 'xuhuong', 'nhanxetxuhuong']:
                row_clean['trend'] = val_clean
            elif k_clean in ['conclusion', 'ketluan']:
                row_clean['conclusion'] = val_clean
            elif k_clean in ['plan', 'kehoach']:
                row_clean['plan'] = val_clean
            elif k_clean in ['compdate', 'ngay', 'ngaysosanh', 'date']:
                row_clean['comp_date'] = clean_date_str(val_clean)
            else:
                row_clean[k_clean] = val_clean
        norm_rows.append(row_clean)
        
    df = pd.DataFrame(norm_rows)
    for c in ['teacher', 'campus', 'class', 'student', 'school_year', 'comp_type', 'period_1', 'period_2', 'score_term1', 'score_term2', 'delta', 'trend', 'conclusion', 'plan', 'comp_date']:
        if c not in df.columns: df[c] = ''
    return df

def load_all_from_gas():
    try:
        res = requests.get(f"{GAS_URL}?action=read_all", allow_redirects=True, timeout=15)
        if res.status_code == 200 and isinstance(res.json(), dict):
            return res.json()
    except Exception: pass
    return {}

def save_sheet_to_gas(sheet_name, df):
    try:
        clean_df = df.fillna("").astype(str).replace(["nan", "None", "NaN"], "")
        payload = {"action": "save_sheet", "sheet_name": sheet_name, "rows": clean_df.to_dict(orient="records")}
        res = requests.post(GAS_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=20)
        return res.status_code == 200
    except Exception: return False

def init_app_data(force_reload=False):
    if force_reload or 'gas_loaded' not in st.session_state:
        with st.spinner("🔄 Đang nạp & đồng bộ dữ liệu từ Google Sheet..."):
            gas_data = load_all_from_gas()
            st.session_state.users_df = normalize_users_df(get_gas_sheet_rows(gas_data, "Users"), DEFAULT_USERS_DF)
            st.session_state.students_df = normalize_students_df(get_gas_sheet_rows(gas_data, "Students"))
            st.session_state.evaluations_df = normalize_evaluations_df(get_gas_sheet_rows(gas_data, "Evaluations"))
            st.session_state.daily_logs_df = normalize_dailylogs_df(get_gas_sheet_rows(gas_data, "DailyLogs"))
            st.session_state.comparisons_df = normalize_comparisons_df(get_gas_sheet_rows(gas_data, "Comparisons"))
            st.session_state.gas_loaded = True

init_app_data()

if 'logged_user' not in st.session_state: st.session_state.logged_user = None

def get_users_dict():
    u_dict = {}
    if "users_df" in st.session_state and not st.session_state.users_df.empty:
        for idx, row in st.session_state.users_df.iterrows():
            u_name = str(row.get("username", "")).strip()
            clean_u = clean_key(u_name)
            if clean_u:
                u_dict[clean_u] = {
                    "raw_username": u_name,
                    "password": str(row.get("password", "")).strip().replace(".0", ""),
                    "name": str(row.get("name", u_name)).strip(),
                    "role": str(row.get("role", "teacher")).strip().lower(),
                    "campus_code": str(row.get("campus_code", "")).strip(),
                    "campus": str(row.get("campus", "")).strip(),
                    "class_name": str(row.get("class_name", "Lớp Mầm")).strip(),
                    "status": str(row.get("status", "active")).strip().lower()
                }
    return u_dict

def authenticate_user(login_u, login_p, users_dict):
    clean_u = clean_key(login_u)
    digits_u = digits_only(login_u)
    clean_p = str(login_p).strip().replace(".0", "")
    
    if not clean_u:
        return False, None, None, "EMPTY_USER"
        
    for u_key, u_info in users_dict.items():
        db_u = u_info["raw_username"]
        db_p = str(u_info["password"]).strip().replace(".0", "")
        db_name = u_info["name"]
        
        match = False
        if clean_key(u_key) == clean_u or clean_key(db_u) == clean_u:
            match = True
        elif digits_u and len(digits_u) >= 8 and digits_u in digits_only(db_u):
            match = True
        elif clean_key(db_name) == clean_u or clean_u in clean_key(db_name):
            match = True
            
        if match:
            if db_p == clean_p:
                return True, u_key, u_info, "OK"
            else:
                return False, None, None, "WRONG_PASSWORD"
                
    return False, None, None, "NOT_FOUND"

# -----------------------------------------------------------------------------
# 4. GIAO DIỆN ĐĂNG NHẬP & BẢO MẬT
# -----------------------------------------------------------------------------
users_dict = get_users_dict()

if st.session_state.logged_user is None:
    col_l, col_r = st.columns([1.2, 1.8], gap="large")
    with col_l:
        st.markdown("<div class='login-card'><h3>🔐 ĐĂNG NHẬP HỆ THỐNG TFA EQ</h3><p style='color:#666;font-size:13px;'>Dành cho Ban Giám Hiệu & Giáo Viên</p></div>", unsafe_allow_html=True)
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=220)
        
        with st.form("login_form"):
            u_in = st.text_input("👤 Số điện thoại / Tên đăng nhập:").strip()
            p_in = st.text_input("🔑 Mật khẩu:", type="password").strip()
            st.write("")
            btn_login = st.form_submit_button("🚀 CỔNG ĐĂNG NHẬP")
            
            if btn_login:
                success, u_key, u_info, err_code = authenticate_user(u_in, p_in, users_dict)
                if success:
                    st.session_state.logged_user = u_key
                    st.success(f"🎉 Đăng nhập thành công! Chào mừng {u_info['name']}")
                    st.rerun()
                elif err_code == "WRONG_PASSWORD":
                    st.error("❌ Mật khẩu không chính xác!")
                else:
                    st.error(f"❌ Tài khoản `{u_in}` không tồn tại trên hệ thống!")

        st.markdown("---")
        if st.button("🔄 NẠP TẢI LẠI DỮ LIỆU TỪ GOOGLE SHEET (1-CLICK)"):
            init_app_data(force_reload=True)
            st.success("🎉 Đã làm mới và nạp lại toàn bộ dữ liệu từ Google Trang tính!")
            st.rerun()

    with col_r:
        st.markdown("""
            <div class="info-card">
                <h3 style="color: #000; margin-top:0;">🏫 HỆ THỐNG TRƯỜNG MẦM NON SONG NGỮ THE FIRST ACADEMY</h3>
                <p style="color: #444; line-height: 1.6; font-size: 14.5px;">
                    <b>The FIRST Academy (TFA)</b> theo dõi & đánh giá sự phát triển <b>Trí tuệ Cảm xúc (EQ)</b> của trẻ mầm non.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 🟢 Trạng thái dữ liệu kết nối từ Google Sheet:")
        c_u = len(st.session_state.users_df) if "users_df" in st.session_state else 0
        c_s = len(st.session_state.students_df) if "students_df" in st.session_state else 0
        c_d = len(st.session_state.daily_logs_df) if "daily_logs_df" in st.session_state else 0
        c_e = len(st.session_state.evaluations_df) if "evaluations_df" in st.session_state else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tài khoản", f"{c_u}")
        m2.metric("Học sinh", f"{c_s}")
        m3.metric("Nhật ký", f"{c_d}")
        m4.metric("Phiếu EQ", f"{c_e}")
        
        st.markdown("---")
        st.markdown("##### 📍 Mạng lưới 5 Cơ sở Toàn hệ thống")
        st.markdown("""
            <div>
                <span class="campus-badge">🏢 TFA Hà Đô (Phường Cát Lái, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Dương Bạch Mai (Phường Chánh Hưng, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Him Lam (Phường Tân Hưng, TP.HCM)</span>
                <span class="campus-badge">🏢 TFA Trần Thị Lý (Phường Hòa Cường, TP.Đà Nẵng)</span>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. KHÔNG GIAN LÀM VIỆC TRONG APP (SAU KHI ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
else:
    u_info = users_dict.get(st.session_state.logged_user, {"name": "Giáo viên", "role": "teacher", "campus": "TFA", "class_name": "Lớp"})
    user_key = st.session_state.logged_user
    role = u_info.get("role", "teacher")
    
    if os.path.exists(LOGO_FILE): st.sidebar.image(LOGO_FILE, width=220)
    st.sidebar.markdown(f"### 👤 **{u_info['name']}**\n🏢 **Cơ sở:** {u_info['campus']}")
    
    if st.sidebar.button("🔄 Nạp Tải Dữ Liệu Sheet"):
        init_app_data(force_reload=True)
        st.rerun()
        
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state.logged_user = None
        st.rerun()

    st.sidebar.markdown("---")
    
    # -------------------------------------------------------------------------
    # VAI TRÒ GIÁO VIÊN
    # -------------------------------------------------------------------------
    if role == "teacher":
        menu = st.sidebar.radio("DANH MỤC GIÁO VIÊN:", [
            "🏫 1. Quản lý Học sinh",
            "📝 2. Nhật ký Cảm xúc Hằng ngày",
            "🎯 3. Đánh giá EQ 6 Tiêu chí",
            "📈 4. So Sánh & Xu Hướng EQ"
        ])
        
        if menu == "🏫 1. Quản lý Học sinh":
            st.subheader("🏫 QUẢN LÝ DANH SÁCH HỌC SINH LỚP")
            with st.form("add_std_form", clear_on_submit=True):
                s_name = st.text_input("Họ và tên học sinh mới:").strip()
                s_note = st.text_input("Ghi chú đặc biệt (dị ứng, lưu ý...):").strip()
                if st.form_submit_button("➕ Thêm Học Sinh"):
                    if s_name:
                        new_std = pd.DataFrame([{"teacher_user": u_info.get("raw_username", user_key), "student_name": s_name, "student_note": s_note}])
                        st.session_state.students_df = pd.concat([st.session_state.students_df, new_std], ignore_index=True)
                        save_sheet_to_gas("Students", st.session_state.students_df)
                        st.success(f"🎉 Đã thêm thành công bé **{s_name}**!")
                        st.rerun()

            st.markdown("---")
            my_stds_df = filter_teacher_records(st.session_state.students_df, ['teacher_user', 'teacher', 'Teacher_User'], u_info)
            if not my_stds_df.empty:
                st.dataframe(my_stds_df[["student_name", "student_note"]], use_container_width=True)
            else:
                st.info("Lớp bạn chưa có học sinh nào. Hãy thêm ở form trên!")

        elif menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
            st.subheader("📝 HỒ SƠ CẢM XÚC CÁ NHÂN HẰNG NGÀY")
            my_stds_df = filter_teacher_records(st.session_state.students_df, ['teacher_user', 'teacher', 'Teacher_User'], u_info)
            my_stds = my_stds_df["student_name"].tolist() if not my_stds_df.empty and "student_name" in my_stds_df.columns else []
            
            if not my_stds:
                st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng thêm học sinh ở Mục 1!")
            else:
                c1, c2 = st.columns(2)
                with c1: sel_std = st.selectbox("👦/👧 Chọn học sinh:", my_stds)
                with c2: sel_date = st.date_input("🗓️ Chọn ngày nhập / xem lại:", value=datetime.today())
                dt_str = clean_date_str(sel_date)
                
                d_df = filter_teacher_records(st.session_state.daily_logs_df, ['teacher', 'giaovien', 'Teacher'], u_info)
                old_log = None
                if not d_df.empty:
                    s_col = 'student' if 'student' in d_df.columns else 'hocsinh'
                    d_col = 'date' if 'date' in d_df.columns else 'ngay'
                    mask = (d_df[s_col].apply(clean_key) == clean_key(sel_std)) & (d_df[d_col].apply(clean_date_str) == dt_str)
                    if mask.any(): old_log = d_df[mask].iloc[-1]
                
                if old_log is not None:
                    st.success(f"ℹ️ Đã tìm thấy nhật ký ngày **{dt_str}** của bé **{sel_std}**. Bạn có thể chỉnh sửa rồi bấm Lưu!")
                else:
                    st.info(f"🗓️ Ngày **{dt_str}** chưa có nhật ký. Nhập nội dung bên dưới để tạo mới!")
                
                with st.form("daily_form"):
                    note_ctx = st.text_area("📌 Bối cảnh / Biểu hiện nổi bật trong ngày:", value=str(old_log.get("note", "")) if old_log is not None else "")
                    note_interv = st.text_area("🤝 Can thiệp & hỗ trợ của cô:", value=str(old_log.get("intervention", "")) if old_log is not None else "")
                    daily_sum = st.text_area("💬 Nhận xét chung của giáo viên:", value=str(old_log.get("summary", "")) if old_log is not None else "")
                    
                    if st.form_submit_button("💾 LƯU HỒ SƠ CẢM XÚC HẰNG NGÀY"):
                        new_log = pd.DataFrame([{
                            "teacher": u_info.get("name", user_key), "campus": u_info.get("campus", "TFA"), "class": u_info.get("class_name", "Mầm"),
                            "student": sel_std, "date": dt_str, "routine": "Cả ngày",
                            "emotions": "Ghi nhận cảm xúc", "note": note_ctx, "intervention": note_interv,
                            "summary": daily_sum, "details_json": "{}"
                        }])
                        st.session_state.daily_logs_df = pd.concat([st.session_state.daily_logs_df, new_log], ignore_index=True)
                        save_sheet_to_gas("DailyLogs", st.session_state.daily_logs_df)
                        st.success(f"🎉 Đã lưu thành công nhật ký ngày {dt_str} cho bé **{sel_std}**!")
                        st.rerun()

        elif menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ")
            my_stds_df = filter_teacher_records(st.session_state.students_df, ['teacher_user', 'teacher', 'Teacher_User'], u_info)
            my_stds = my_stds_df["student_name"].tolist() if not my_stds_df.empty and "student_name" in my_stds_df.columns else []
            
            if my_stds:
                sel_std = st.selectbox("Chọn học sinh:", my_stds)
                if st.button("⚡ TỰ ĐỘNG TỔNG HỢP EQ THÁNG (1-CLICK)"):
                    res = auto_map_daily_to_criteria(sel_std, u_info["name"], st.session_state.daily_logs_df)
                    if res:
                        st.success(f"🎉 Đã tổng hợp thành công cho bé **{sel_std}**! Điểm PEQ đề xuất: {res['P_EQ']} ({res['Group_Clean']})")
                        st.info(f"📝 Bối cảnh: {res['Context']}")
            else: st.warning("Chưa có học sinh trong lớp.")

        else:
            st.subheader("📈 BẢNG SO SÁNH & XU HƯỚNG EQ")
            my_comps = filter_teacher_records(st.session_state.comparisons_df, ['teacher', 'giaovien', 'Teacher'], u_info)
            st.dataframe(my_comps, use_container_width=True)
            
    # -------------------------------------------------------------------------
    # VAI TRÒ ADMIN TỔNG HOẶC BGH CƠ SỞ
    # -------------------------------------------------------------------------
    else:
        st.subheader(f"📊 QUẢN LÝ DÀNH CHO {role.upper()}")
        st.dataframe(st.session_state.evaluations_df, use_container_width=True)
