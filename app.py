import streamlit as st
import pandas as pd
import requests
import os
import json
import unicodedata
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 🔗 KẾT NỐI VỚI GOOGLE SHEET QUA WEB APP URL
# -----------------------------------------------------------------------------
GAS_URL = "https://script.google.com/macros/s/AKfycbwYyCVKVPrIw80fR13LysE3yZz2OrZRhPlfeymEJ6j-g_GkEfWtnauvNzfKJnEQYWNeqA/exec"

# -----------------------------------------------------------------------------
# 🛠️ HÀM HỖ TRỢ CHUẨN HÓA MÃ CHUỖI & TÌM KIẾM AN TOÀN TUYỆT ĐỐI
# -----------------------------------------------------------------------------
def remove_accents_vn(s):
    if not s:
        return ""
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd').replace('Đ', 'D').lower().strip()

def clean_dict_key(k):
    if not k:
        return ""
    k_no_accent = remove_accents_vn(k)
    return ''.join(c for c in k_no_accent if c.isalnum())

def clean_key(val):
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip().lower().replace(".0", "")
    if s in ["nan", "none"]:
        return ""
    s = remove_accents_vn(s)
    if s.startswith("0") and len(s) > 1:
        s = s[1:]
        
    for pfx in ["cobaogiao", "cogiao", "cophutrach", "giao", "co"]:
        if s.startswith(pfx) and len(s) > len(pfx):
            s = s[len(pfx):]
            break
            
    return s.strip()

def clean_date_str(val):
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip()
    if not s or s.lower() in ["nan", "none"]:
        return ""
    if "-" in s:
        parts = s.split("T")[0].split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}"
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
    return s

def get_val(row_dict, keys_list, default=""):
    if not row_dict or not isinstance(row_dict, dict):
        return default
    for k in keys_list:
        clean_k = clean_dict_key(k)
        if clean_k in row_dict and str(row_dict[clean_k]).strip() != "":
            return str(row_dict[clean_k]).strip()
        for rk, rv in row_dict.items():
            if clean_k in rk and str(rv).strip() != "":
                return str(rv).strip()
    return default

def is_student_match(s1, s2):
    if not s1 or not s2:
        return False
    c1 = clean_key(s1)
    c2 = clean_key(s2)
    if not c1 or not c2:
        return False
    if c1 == c2:
        return True
    
    c1_p = c1
    c2_p = c2
    for pfx in ["be", "hocsinh", "tre"]:
        if c1_p.startswith(pfx) and len(c1_p) > len(pfx):
            c1_p = c1_p[len(pfx):]
        if c2_p.startswith(pfx) and len(c2_p) > len(pfx):
            c2_p = c2_p[len(pfx):]
            
    if c1_p == c2_p or (len(c1_p) >= 3 and c1_p in c2_p) or (len(c2_p) >= 3 and c2_p in c1_p):
        return True
    return False

def is_teacher_match(val, user_info):
    if not val or not user_info:
        return False
    c_val = clean_key(val)
    if not c_val:
        return False
    
    u_name = clean_key(user_info.get('name', ''))
    u_user = clean_key(user_info.get('username', ''))
    u_raw = clean_key(user_info.get('raw_username', ''))
    
    if c_val in [u_name, u_user, u_raw]:
        return True
        
    u_digits = u_user
    for cc in ["hd", "hl", "dbm", "lvs", "ttl", "all"]:
        if u_digits.endswith(cc):
            u_digits = u_digits[:-len(cc)]
    val_digits = c_val
    for cc in ["hd", "hl", "dbm", "lvs", "ttl", "all"]:
        if val_digits.endswith(cc):
            val_digits = val_digits[:-len(cc)]
            
    if u_digits and len(u_digits) >= 6 and (val_digits == u_digits or c_val == u_digits or val_digits == u_user):
        return True
        
    raw_val_words = set(remove_accents_vn(val).split())
    raw_name_words = set(remove_accents_vn(user_info.get('name', '')).split())
    if raw_val_words and raw_name_words:
        if raw_val_words.issubset(raw_name_words) or raw_name_words.issubset(raw_val_words):
            return True
            
    return False

def filter_teacher_records(df, col_name, user_info):
    if df is None or df.empty or col_name not in df.columns or not user_info:
        return df.iloc[0:0] if df is not None else pd.DataFrame()
        
    role = user_info.get("role", "teacher")
    if role in ["super_admin", "campus_admin"]:
        return df
        
    mask = df[col_name].apply(lambda v: is_teacher_match(v, user_info))
    return df[mask]

def get_gas_sheet_rows(gas_data, sheet_name):
    if not isinstance(gas_data, dict):
        return []
        
    for sub_key in ["data", "result", "sheets", "payload"]:
        if sub_key in gas_data and isinstance(gas_data[sub_key], dict):
            gas_data = gas_data[sub_key]
            break

    target_clean = clean_dict_key(sheet_name)
    aliases = {
        "users": ["users", "user", "taikhoan", "nguoidung", "giaovien", "dsgv", "danhsachgiaovien", "teachers", "teacher"],
        "students": ["students", "student", "hocsinh", "be", "danhsachhocsinh", "dshs", "dshocsinh"],
        "evaluations": ["evaluations", "evaluation", "danhgia", "phieudanhgia", "eqevaluations", "danhgiaeq", "phieudanhgiaeq"],
        "dailylogs": ["dailylogs", "dailylog", "nhatky", "hoso", "hosocamxuc", "nhatkyhangngay", "nhatkycamxuc"],
        "comparisons": ["comparisons", "comparison", "sosanh", "xuhuong", "bangsosanh", "sosanhxuhuong", "bangsosanhxuhuong"]
    }
    match_targets = aliases.get(target_clean, [target_clean])
    
    for k, v in gas_data.items():
        clean_k = clean_dict_key(k)
        if any(clean_k == t or clean_k == t + "s" or t == clean_k + "s" for t in match_targets):
            if isinstance(v, list):
                return v
            elif isinstance(v, dict):
                return [v]
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
    .stApp { background-color: #FFFDF5; font-family: 'Segoe UI', Roboto, sans-serif; }
    div[data-testid="stSidebar"] { background-color: #FFF9E6 !important; border-right: 2px solid #FFE082; }
    div.stButton > button:first-child {
        background-color: #FFC107; color: #333333; font-weight: bold;
        border-radius: 8px; border: none; padding: 0.5rem 1rem; width: 100%; transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover { background-color: #FFB300; color: #000000; }
    h1, h2, h3 { color: #D84315; }
    .note-badge { background-color: #E1F5FE; color: #0277BD; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

LOGO_FILE = "Logo_TFA_Ver2.1_.png"
if os.path.exists(LOGO_FILE):
    st.image(LOGO_FILE, width=280)
else:
    st.title("☀️ THE FIRST ACADEMY")

st.markdown("### 🏫 HỆ THỐNG QUẢN LÝ VÀ PHÁT TRIỂN TRÍ TUỆ CẢM XÚC (EQ)")

# -----------------------------------------------------------------------------
# 2. HẰNG SỐ VÀ CẤU HÌNH BỘ TIÊU CHÍ EQ
# -----------------------------------------------------------------------------
TFA_CLASSES = [
    "Pre-school (3-4 tuổi)",
    "Kindergarten (4-5 tuổi)",
    "Pre-primary (5-6 tuổi)"
]

CAMPUS_MAP = {
    "HD": "Hà Đô",
    "TTL": "Trần Thị Lý",
    "DBM": "Dương Bạch Mai",
    "HL": "Him Lam",
    "LVS": "Lê Văn Sỹ"
}

SCHOOL_YEAR_OPTIONS = ["2024 - 2025", "2025 - 2026", "2026 - 2027"]

EMOTION_COLS = [
    "Vui 🌱", "Hào hứng 🌟", "Yêu thương ❤️", "Tự hào ✨",
    "Buồn 🌧️", "Giận ⚡", "Lo lắng ☁️"
]

TFA_ROUTINES = [
    "Đón trẻ / Buổi sáng 🌅",
    "Hoạt động có chủ đích / Học tập 📘",
    "Ăn trưa / Giờ ngủ 🥗",
    "Hoạt động chiều / Chơi tự do 🎨",
    "Trả trẻ / Cuối ngày 🚪",
    "Tình huống phát sinh / Khác ⚠️"
]

CRITERIA_DATA = {
    "Pre-school (3-4 tuổi)": {
        "TC1": {1: "Mức 1: Chưa nhận biết được các cảm xúc cơ bản.", 2: "Mức 2: Bắt đầu nhận biết được vui, buồn khi cô gợi mở.", 3: "Mức 3: Nhận biết tốt cảm xúc bản thân trong ngày.", 4: "Mức 4: Tự giác chia sẻ cảm xúc với cô và bạn."},
        "TC2": {1: "Mức 1: Chưa gọi tên được cảm xúc.", 2: "Mức 2: Gọi tên được cảm xúc đơn giản.", 3: "Mức 3: Diễn đạt rõ ràng cảm xúc qua lời nói.", 4: "Mức 4: Diễn đạt mạch lạc và giải thích lý do."},
        "TC3": {1: "Mức 1: Dễ bùng nổ, khóc lâu.", 2: "Mức 2: Cần cô dỗ dành xoa dịu.", 3: "Mức 3: Tự dịu lại sau khi cô gợi ý.", 4: "Mức 4: Tự chủ cảm xúc tốt."},
        "TC4": {1: "Mức 1: Thụ động trong giao tiếp.", 2: "Mức 2: Biết an ủi bạn khi cô nhắc.", 3: "Mức 3: Chủ động quan tâm bạn bè.", 4: "Mức 4: Thể hiện sự đồng cảm sâu sắc."},
        "TC5": {1: "Mức 1: Nhạy cảm mạnh với môi trường.", 2: "Mức 2: Thích nghi dần.", 3: "Mức 3: Tự tin trong môi trường lớp.", 4: "Mức 4: Truyền năng lượng tích cực."},
        "TC6": {1: "Mức 1: Chưa phản ứng tích cực.", 2: "Mức 2: Vui khi được công nhận.", 3: "Mức 3: Hợp tác tốt khi cô công nhận.", 4: "Mức 4: Phát huy năng lực tự tin vượt trội."}
    },
    "Kindergarten (4-5 tuổi)": {
        "TC1": {1: "Mức 1: Chưa nhận biết rõ cảm xúc.", 2: "Mức 2: Nhận biết cảm xúc cơ bản.", 3: "Mức 3: Nhận biết đa dạng cảm xúc.", 4: "Mức 4: Thấu hiểu sâu sắc cảm xúc."},
        "TC2": {1: "Mức 1: Khó gọi tên cảm xúc.", 2: "Mức 2: Gọi tên cảm xúc tương đối.", 3: "Mức 3: Diễn đạt nguyên nhân cảm xúc.", 4: "Mức 4: Diễn đạt tinh tế cảm xúc."},
        "TC3": {1: "Mức 1: Còn hay ăn vạ.", 2: "Mức 2: Cần sự can thiệp của cô.", 3: "Mức 3: Sử dụng Góc Bình Tĩnh hiệu quả.", 4: "Mức 4: Tự làm chủ cảm xúc hoàn hảo."},
        "TC4": {1: "Mức 1: Chưa chơi hòa đồng.", 2: "Mức 2: Biết chia sẻ đồ chơi.", 3: "Mức 3: Biết lắng nghe và hợp tác.", 4: "Mức 4: Làm thủ lĩnh nhóm tích cực."},
        "TC5": {1: "Mức 1: Dễ bị xáo trộn.", 2: "Mức 2: Thích nghi sau xáo trộn.", 3: "Mức 3: Vững vàng trước thay đổi.", 4: "Mức 4: Giúp bạn khác thích nghi."},
        "TC6": {1: "Mức 1: Ít thay đổi.", 2: "Mức 2: Tích cực hơn.", 3: "Mức 3: Tiến bộ rõ rệt.", 4: "Mức 4: Tự hào và lan tỏa."}
    },
    "Pre-primary (5-6 tuổi)": {
        "TC1": {1: "Mức 1: Nhận biết hạn chế.", 2: "Mức 2: Nhận biết tốt.", 3: "Mức 3: Nhận biết và phân tích cảm xúc.", 4: "Mức 4: Quản trị cảm xúc bản thân."},
        "TC2": {1: "Mức 1: Diễn đạt chưa rõ.", 2: "Mức 2: Nói rõ cảm xúc.", 3: "Mức 3: Trình bày nguyên nhân và mong muốn.", 4: "Mức 4: Thuyết phục và giải quyết mâu thuẫn."},
        "TC3": {1: "Mức 1: Thiếu kiềm chế.", 2: "Mức 2: Cần gợi ý xoa dịu.", 3: "Mức 3: Tự giải tỏa căng thẳng.", 4: "Mức 4: Bản lĩnh và tự làm chủ hoàn toàn."},
        "TC4": {1: "Mức 1: Thỉnh thoảng tranh chấp.", 2: "Mức 2: Tôn trọng bạn.", 3: "Mức 3: Giải quyết mâu thuẫn ôn hòa.", 4: "Mức 4: Gắn kết tập thể xuất sắc."},
        "TC5": {1: "Mức 1: Bị ảnh hưởng bởi xung quanh.", 2: "Mức 2: Bình tĩnh thích ứng.", 3: "Mức 3: Chủ động xử lý tình huống.", 4: "Mức 4: Bản lĩnh tiên phong."},
        "TC6": {1: "Mức 1: Tiếp nhận đơn thuần.", 2: "Mức 2: Tự tin hơn.", 3: "Mức 3: Đạt mục tiêu cảm xúc.", 4: "Mức 4: Truyền cảm hứng cho các bạn."}
    }
}

# -----------------------------------------------------------------------------
# 3. ĐỒNG BỘ GOOGLE SHEET & CHUẨN HÓA DỮ LIỆU ĐA DẠNG
# -----------------------------------------------------------------------------
DEFAULT_USERS_DF = pd.DataFrame([
    {"username": "admin", "password": "admin123", "name": "Ban Giám Hiệu Tổng (Toàn Hệ Thống)", "role": "super_admin", "campus_code": "ALL", "campus": "Tất cả cơ sở", "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHD", "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin", "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHTTL", "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin", "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHDBM", "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin", "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHHL", "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin", "campus_code": "HL", "campus": CAMPUS_MAP["HL"], "class_name": "Tất cả", "status": "active"},
    {"username": "BGHLVS", "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin", "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"], "class_name": "Tất cả", "status": "active"}
])

def normalize_users_df(raw_rows, default_users_df):
    if not raw_rows:
        return default_users_df
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        rd = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        username = get_val(rd, ['username', 'user', 'tk', 'tendangnhap', 'taikhoan', 'sdt', 'sodienthoai', 'phone', 'dienthoai', 'magv', 'magiaovien', 'taikhoangv', 'tentk', 'stk', 'account', 'login', 'id', 'userid', 'tkgiaovien', 'mataikhoan', 'sdttendangnhap'])
        password = get_val(rd, ['password', 'pass', 'matkhau', 'mk', 'matkhau2', 'pwd', 'secret'], '123456')
        if password.endswith('.0'): password = password[:-2]
        name = get_val(rd, ['name', 'hoten', 'tengiaovien', 'ten', 'hovaten', 'tengv', 'fullname', 'displayname', 'giaovien', 'nv'], username)
        role = get_val(rd, ['role', 'vaitro', 'chucvu', 'quyen'], 'teacher').lower()
        campus_code = get_val(rd, ['campuscode', 'macoso', 'code', 'cosocode'])
        campus = get_val(rd, ['campus', 'coso', 'truong', 'tencoso'])
        class_name = get_val(rd, ['classname', 'class', 'lop', 'tenlop', 'khoi', 'khoilopphutrach', 'khoilop'])
        status = get_val(rd, ['status', 'trangthai', 'tinhtrang'], 'active').lower()
        
        if username:
            norm_rows.append({
                'username': username, 'password': password, 'name': name,
                'role': role, 'campus_code': campus_code, 'campus': campus,
                'class_name': class_name, 'status': status
            })
    df = pd.DataFrame(norm_rows)
    for c in ['username', 'password', 'name', 'role', 'campus_code', 'campus', 'class_name', 'status']:
        if c not in df.columns: df[c] = ''
    all_df = pd.concat([default_users_df, df], ignore_index=True)
    all_df['_u_clean'] = all_df['username'].apply(clean_key)
    all_df = all_df[all_df['_u_clean'] != ''].drop_duplicates(subset=['_u_clean'], keep='last').drop(columns=['_u_clean'])
    return all_df

def normalize_students_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=['teacher_user', 'student_name', 'student_note'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        rd = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        t_user = get_val(rd, ['teacheruser', 'teacher', 'teacherusername', 'tuser', 'user', 'giaovien', 'tkgiaovien', 'magv', 'sdt', 'sodienthoai', 'phone', 'taikhoan', 'sdttendangnhap'])
        s_name = get_val(rd, ['studentname', 'student', 'sname', 'tenhocsinh', 'hocsinh', 'tenbe', 'be', 'ten'])
        s_note = get_val(rd, ['studentnote', 'note', 'ghichu', 'luuy', 'ghichudacbietluuyvetre'])
        if s_name:
            norm_rows.append({'teacher_user': t_user, 'student_name': s_name, 'student_note': s_note})
    df = pd.DataFrame(norm_rows)
    for c in ['teacher_user', 'student_name', 'student_note']:
        if c not in df.columns: df[c] = ''
    return df

def normalize_evaluations_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=['teacher', 'campus', 'class', 'student', 'school_year', 'term', 'eval_date', 'tc1', 'tc2', 'tc3', 'tc4', 'tc5', 'tc6', 'p_eq', 'group_clean', 'context', 'conclusion', 'plan'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        rd = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        norm_rows.append({
            'teacher': get_val(rd, ['teacher', 'giaovien', 'tkgiaovien', 'magv', 'taikhoan', 'sdt']),
            'campus': get_val(rd, ['campus', 'coso']),
            'class': get_val(rd, ['class', 'lop']),
            'student': get_val(rd, ['student', 'hocsinh', 'tenbe', 'tenhocsinh']),
            'school_year': get_val(rd, ['schoolyear', 'namhoc']),
            'term': get_val(rd, ['term', 'ky', 'kythang', 'thang']),
            'eval_date': clean_date_str(get_val(rd, ['evaldate', 'ngay', 'ngaydanhgia'])),
            'tc1': get_val(rd, ['tc1'], '0'),
            'tc2': get_val(rd, ['tc2'], '0'),
            'tc3': get_val(rd, ['tc3'], '0'),
            'tc4': get_val(rd, ['tc4'], '0'),
            'tc5': get_val(rd, ['tc5'], '0'),
            'tc6': get_val(rd, ['tc6'], '0'),
            'p_eq': get_val(rd, ['peq', 'peqscore', 'diemtbpeq', 'diemtb'], '0'),
            'group_clean': get_val(rd, ['groupclean', 'nhom', 'nhomtrangthai']),
            'context': get_val(rd, ['context', 'boicanh', 'boicanhminhchungdienhinhhanhvicuthe']),
            'conclusion': get_val(rd, ['conclusion', 'ketluan', 'ketluanxuhuong']),
            'plan': get_val(rd, ['plan', 'kehoach', 'kehoachtacdongtieptheo'])
        })
    return pd.DataFrame(norm_rows)

def normalize_dailylogs_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=['teacher', 'campus', 'class', 'student', 'date', 'routine', 'emotions', 'note', 'intervention', 'summary', 'details_json'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        rd = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        norm_rows.append({
            'teacher': get_val(rd, ['teacher', 'giaovien', 'tkgiaovien', 'magv', 'taikhoan', 'sdt', 'cophutrach', 'nguoinhap']),
            'campus': get_val(rd, ['campus', 'coso', 'truong', 'tencoso']),
            'class': get_val(rd, ['class', 'lop', 'tenlop', 'khoilop']),
            'student': get_val(rd, ['student', 'hocsinh', 'tenbe', 'tenhocsinh', 'ten']),
            'date': clean_date_str(get_val(rd, ['date', 'ngay', 'ngaynhap', 'ngaytao'])),
            'routine': get_val(rd, ['routine', 'hoatdong'], 'Cả ngày'),
            'emotions': get_val(rd, ['emotions', 'camxuc']),
            'note': get_val(rd, ['note', 'ghichu', 'boicanh', 'boicanhvabieuhiennoibat']),
            'intervention': get_val(rd, ['intervention', 'canthiep', 'canthiepvahotro', 'canthiepvahotrocuagiao']),
            'summary': get_val(rd, ['summary', 'nhanxet', 'xuhuong', 'nhanxetbosungcuagiao']),
            'details_json': get_val(rd, ['detailsjson', 'details', 'chitiet'])
        })
    return pd.DataFrame(norm_rows)

def normalize_comparisons_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=['teacher', 'campus', 'class', 'student', 'school_year', 'comp_type', 'period_1', 'period_2', 'score_term1', 'score_term2', 'delta', 'trend', 'conclusion', 'plan', 'comp_date'])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        rd = {clean_dict_key(k): str(v).strip() if v is not None else '' for k, v in r.items()}
        norm_rows.append({
            'teacher': get_val(rd, ['teacher', 'giaovien', 'tkgiaovien', 'magv', 'taikhoan', 'sdt']),
            'campus': get_val(rd, ['campus', 'coso']),
            'class': get_val(rd, ['class', 'lop']),
            'student': get_val(rd, ['student', 'hocsinh', 'tenbe', 'tenhocsinh']),
            'school_year': get_val(rd, ['schoolyear', 'namhoc']),
            'comp_type': get_val(rd, ['comptype', 'loaisosanh', 'hinhthucsosanh']),
            'period_1': get_val(rd, ['period1', 'dot1']),
            'period_2': get_val(rd, ['period2', 'dot2']),
            'score_term1': get_val(rd, ['scoreterm1', 'diemdot1'], '0'),
            'score_term2': get_val(rd, ['scoreterm2', 'diemdot2'], '0'),
            'delta': get_val(rd, ['delta', 'bienthien'], '0'),
            'trend': get_val(rd, ['trend', 'xuhuong', 'xuhuongeq']),
            'conclusion': get_val(rd, ['conclusion', 'ketluan', 'ketluanxuhuong']),
            'plan': get_val(rd, ['plan', 'kehoach', 'kehoachtacdongtieptheo']),
            'comp_date': clean_date_str(get_val(rd, ['compdate', 'ngaysosanh', 'ngay']))
        })
    return pd.DataFrame(norm_rows)

def load_all_from_gas():
    try:
        res = requests.get(f"{GAS_URL}?action=read_all", allow_redirects=True, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and len(data) > 0:
                return data
    except Exception:
        pass

    try:
        res = requests.post(GAS_URL, data=json.dumps({"action": "read_all"}), headers={"Content-Type": "application/json"}, allow_redirects=True, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and len(data) > 0:
                return data
    except Exception:
        pass

    try:
        res = requests.post(GAS_URL, data={"payload": json.dumps({"action": "read_all"})}, allow_redirects=True, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and len(data) > 0:
                return data
    except Exception:
        pass

    return {}

def save_sheet_to_gas(sheet_name, df):
    try:
        clean_df = df.fillna("").astype(str)
        clean_df = clean_df.replace(["nan", "None", "NaN"], "")
        rows_list = clean_df.to_dict(orient="records")
        
        payload = {
            "action": "save_sheet",
            "sheet_name": sheet_name,
            "rows": rows_list
        }
        
        headers = {"Content-Type": "application/json"}
        res = requests.post(GAS_URL, data=json.dumps(payload), headers=headers, allow_redirects=True, timeout=20)
        
        if res.status_code == 200:
            try:
                res_data = res.json()
                if isinstance(res_data, dict) and res_data.get("status") == "error":
                    st.error(f"⚠️ Google Sheet báo lỗi: {res_data.get('message', 'Không thể ghi dữ liệu')}")
                    return False
            except Exception:
                pass
            return True
            
        fallback_res = requests.post(GAS_URL, data={"payload": json.dumps(payload)}, allow_redirects=True, timeout=20)
        if fallback_res.status_code == 200:
            return True
            
        st.error(f"⚠️ Google Sheet trả về mã lỗi HTTP: {res.status_code}")
        return False
        
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Google Sheet: {e}")
        return False

def init_app_data(force_reload=False):
    if force_reload or 'gas_loaded' not in st.session_state:
        with st.spinner("🔄 Đang đồng bộ & nạp dữ liệu từ Google Trang tính..."):
            gas_data = load_all_from_gas()
            if gas_data and isinstance(gas_data, dict):
                u_rows = get_gas_sheet_rows(gas_data, "Users")
                st.session_state.users_df = normalize_users_df(u_rows, DEFAULT_USERS_DF)

                s_rows = get_gas_sheet_rows(gas_data, "Students")
                st.session_state.students_df = normalize_students_df(s_rows)

                e_rows = get_gas_sheet_rows(gas_data, "Evaluations")
                st.session_state.evaluations_df = normalize_evaluations_df(e_rows)

                d_rows = get_gas_sheet_rows(gas_data, "DailyLogs")
                st.session_state.daily_logs_df = normalize_dailylogs_df(d_rows)

                c_rows = get_gas_sheet_rows(gas_data, "Comparisons")
                st.session_state.comparisons_df = normalize_comparisons_df(c_rows)

                st.session_state.gas_loaded = True
            else:
                if 'users_df' not in st.session_state: st.session_state.users_df = DEFAULT_USERS_DF
                if 'students_df' not in st.session_state: st.session_state.students_df = pd.DataFrame()
                if 'evaluations_df' not in st.session_state: st.session_state.evaluations_df = pd.DataFrame()
                if 'daily_logs_df' not in st.session_state: st.session_state.daily_logs_df = pd.DataFrame()
                if 'comparisons_df' not in st.session_state: st.session_state.comparisons_df = pd.DataFrame()

init_app_data()

def get_all_users_dict():
    u_dict = {}
    if "users_df" in st.session_state and not st.session_state.users_df.empty:
        for idx, row in st.session_state.users_df.iterrows():
            u_name = str(row.get("username", "")).strip()
            clean_u = clean_key(u_name)
            if clean_u and clean_u != "nan":
                u_dict[clean_u] = {
                    "raw_username": u_name,
                    "username": u_name,
                    "password": str(row.get("password", "")).strip(),
                    "name": str(row.get("name", u_name)).strip(),
                    "role": str(row.get("role", "teacher")).strip().lower(),
                    "campus_code": str(row.get("campus_code", "")).strip(),
                    "campus": str(row.get("campus", "")).strip(),
                    "class_name": str(row.get("class_name", "Chưa tạo lớp")).strip(),
                    "status": str(row.get("status", "active")).strip().lower()
                }
    return u_dict

def authenticate_user(login_u, login_p, users_dict):
    clean_u = clean_key(login_u)
    clean_p = str(login_p).strip()
    
    if not clean_u:
        return False, None, None, "EMPTY_USER"
        
    for u_key, u_info in users_dict.items():
        if clean_key(u_key) == clean_u or clean_key(u_info.get("username")) == clean_u:
            if u_info["password"] == clean_p:
                return True, u_key, u_info, "OK"
            else:
                return False, None, None, "WRONG_PASSWORD"
    return False, None, None, "NOT_FOUND"

# -----------------------------------------------------------------------------
# 4. HÀM CHUẨN HÓA BẢNG XUẤT FILE EXCEL/CSV & XỬ LÝ BÁO CÁO
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
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    
    def get_series(c_name):
        if c_name in df.columns:
            return pd.Series(df[c_name].values, index=export_df.index)
        return pd.Series([""] * len(df), index=export_df.index)

    export_df["Ngày đánh giá"] = get_series("eval_date") if "eval_date" in df.columns else datetime.today().strftime("%d/%m/%Y")
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
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    
    def get_series(c_name):
        if c_name in df.columns:
            return pd.Series(df[c_name].values, index=export_df.index)
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

def render_eq_charts(df, title_suffix=""):
    if df is None or df.empty:
        st.info("ℹ️ Chưa có dữ liệu để vẽ biểu đồ.")
        return
        
    c1, c2 = st.columns(2)
    with c1:
        if "group_clean" in df.columns:
            grp_counts = df["group_clean"].value_counts().reset_index()
            grp_counts.columns = ["Nhóm Trạng Thái", "Số lượng"]
            fig_pie = px.pie(grp_counts, names="Nhóm Trạng Thái", values="Số lượng", title=f"Tỷ Lệ Nhóm Trạng Thái EQ {title_suffix}", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with c2:
        tc_cols = [c for c in ["tc1", "tc2", "tc3", "tc4", "tc5", "tc6"] if c in df.columns]
        if tc_cols:
            tc_means = df[tc_cols].apply(pd.to_numeric, errors='coerce').mean().reset_index()
            tc_means.columns = ["Tiêu Chí", "Điểm Trung Bình"]
            tc_means["Tiêu Chí"] = tc_means["Tiêu Chí"].str.upper()
            fig_bar = px.bar(tc_means, x="Tiêu Chí", y="Điểm Trung Bình", title=f"Điểm Trung Bình 6 Tiêu Chí EQ {title_suffix}", color="Điểm Trung Bình", color_continuous_scale="YlOrRd", range_y=[0, 4])
            st.plotly_chart(fig_bar, use_container_width=True)

def calculate_class_stats(df):
    if df is None or df.empty or "delta" not in df.columns:
        return pd.DataFrame([{"Chỉ số": "Không có dữ liệu", "Giá trị": "0"}])
        
    deltas = pd.to_numeric(df["delta"], errors='coerce').dropna()
    if deltas.empty:
        return pd.DataFrame([{"Chỉ số": "Không có dữ liệu", "Giá trị": "0"}])
        
    return pd.DataFrame([
        {"Chỉ số": "Tổng số bé đánh giá / so sánh", "Giá trị": str(len(deltas))},
        {"Chỉ số": "Số bé Tiến bộ (Delta > 0)", "Giá trị": str((deltas > 0).sum())},
        {"Chỉ số": "Số bé Duy trì (Delta = 0)", "Giá trị": str((deltas == 0).sum())},
        {"Chỉ số": "Số bé Cần lưu ý (Delta < 0)", "Giá trị": str((deltas < 0).sum())},
        {"Chỉ số": "Mức biến thiên trung bình toàn lớp", "Giá trị": f"{deltas.mean():+.2f}"}
    ])

def auto_map_daily_to_criteria(student_name, teacher_name, daily_df):
    if daily_df is None or daily_df.empty:
        return None
        
    t_col = "teacher" if "teacher" in daily_df.columns else "Teacher"
    s_col = "student" if "student" in daily_df.columns else "Student"
    
    std_logs = daily_df[
        daily_df.apply(lambda r: is_student_match(r.get(s_col), student_name) and (not teacher_name or is_teacher_match(r.get(t_col), {'name': teacher_name, 'username': teacher_name})), axis=1)
    ]
    if std_logs.empty:
        return None
        
    neg_emotions_count = 0
    pos_emotions_count = 0
    total_logs = len(std_logs)
    
    context_evidences = []
    tc5_signals = []
    tc4_signals = []
    tc3_signals = []
    
    emo_col = "emotions" if "emotions" in std_logs.columns else "Emotions"
    note_col = "note" if "note" in std_logs.columns else "Note"
    interv_col = "intervention" if "intervention" in std_logs.columns else "Intervention"
    date_col = "date" if "date" in std_logs.columns else "Date"
    
    for _, row in std_logs.iterrows():
        emotions_text = str(row.get(emo_col, ''))
        note = str(row.get(note_col, '')).strip()
        interv = str(row.get(interv_col, '')).strip()
        dt_str = clean_date_str(row.get(date_col, ''))
        
        has_neg = any(neg_e in emotions_text for neg_e in ["Buồn", "Giận", "Lo lắng"])
        has_pos = any(pos_e in emotions_text for pos_e in ["Vui", "Hào hứng", "Yêu thương", "Tự hào"])
        
        if has_neg: neg_emotions_count += 1
        if has_pos: pos_emotions_count += 1
        
        if "Đón trẻ" in emotions_text or "Trả trẻ" in emotions_text or "Tình huống phát sinh" in emotions_text:
            if "Giận" in emotions_text or "Buồn" in emotions_text or "Lo lắng" in emotions_text:
                tc5_signals.append(1 if "khóc" in note.lower() or "ăn vạ" in note.lower() else 2)
            else:
                tc5_signals.append(4 if "tự giác" in note.lower() or "chủ động" in note.lower() else 3)
                
        if "Hoạt động chiều" in emotions_text or "Hoạt động có chủ đích" in emotions_text:
            if "Yêu thương" in emotions_text or "Tự hào" in emotions_text or "an ủi" in note.lower() or "chia sẻ" in note.lower():
                tc4_signals.append(4 if "chủ động" in note.lower() or "hòa giải" in note.lower() else 3)
            elif "Giận" in emotions_text:
                tc4_signals.append(1 if "đánh" in note.lower() or "tranh đồ" in note.lower() else 2)
                
        if interv:
            if "tự dịu" in interv.lower() or "góc bình tĩnh" in interv.lower() or "ngay" in interv.lower():
                tc3_signals.append(4)
            elif "ôm" in interv.lower() or "dỗ" in interv.lower() or "nhắc" in interv.lower():
                tc3_signals.append(3 if "ngoan" in interv.lower() or "nghe lời" in interv.lower() else 2)
            elif "khóc lâu" in interv.lower() or "không nghe" in interv.lower():
                tc3_signals.append(1)
                
        if note or interv or has_neg:
            ev_item = f"• {dt_str}: {emotions_text}"
            if note: ev_item += f" | Bối cảnh: {note}"
            if interv: ev_item += f" | Cô hỗ trợ: {interv}"
            context_evidences.append(ev_item)

    if tc3_signals:
        auto_tc3 = round(sum(tc3_signals) / len(tc3_signals))
    else:
        auto_tc3 = 1 if neg_emotions_count > total_logs * 0.4 else (2 if neg_emotions_count > 0 else 3)
        
    auto_tc1 = 1 if neg_emotions_count > total_logs * 0.5 else (2 if neg_emotions_count > 2 else (4 if pos_emotions_count > total_logs * 0.7 else 3))
    auto_tc2 = auto_tc1
    auto_tc4 = round(sum(tc4_signals) / len(tc4_signals)) if tc4_signals else 3
    auto_tc5 = round(sum(tc5_signals) / len(tc5_signals)) if tc5_signals else (2 if neg_emotions_count > 3 else 3)
    auto_tc6 = auto_tc3
    
    auto_tc1 = max(1, min(4, auto_tc1))
    auto_tc2 = max(1, min(4, auto_tc2))
    auto_tc3 = max(1, min(4, auto_tc3))
    auto_tc4 = max(1, min(4, auto_tc4))
    auto_tc5 = max(1, min(4, auto_tc5))
    auto_tc6 = max(1, min(4, auto_tc6))
    
    auto_peq = round((auto_tc1 + auto_tc2 + auto_tc3 + auto_tc4 + auto_tc5 + auto_tc6) / 6.0, 2)
    auto_group = "DUY TRÌ" if auto_peq >= 3.2 else ("CẦN CẢI THIỆN" if auto_peq >= 2.0 else "HỖ TRỢ ĐẶC BIỆT")
    
    evidence_str = "\n".join(context_evidences[:5]) if context_evidences else "Bé sinh hoạt và học tập ổn định theo thời khóa biểu trong tháng."
    auto_context = f"Dựa trên {total_logs} ngày theo dõi hằng ngày trong tháng:\n{evidence_str}"
    
    if auto_group == "DUY TRÌ":
        auto_conclusion = f"Bé {student_name} có trí tuệ cảm xúc phát triển rất tích cực (PEQ={auto_peq}), thuộc nhóm DUY TRÌ PHONG ĐỘ."
        auto_plan = f"Kế hoạch: Tiếp tục phát huy năng lực tự chủ, giao vai trò thủ lĩnh nhóm và khuyến khích bé hỗ trợ các bạn khác."
    elif auto_group == "CẦN CẢI THIỆN":
        auto_conclusion = f"Bé {student_name} đang trong quá trình phát triển cảm xúc (PEQ={auto_peq}), thuộc nhóm CẦN CẢI THIỆN."
        auto_plan = f"Kế hoạch: Hướng dẫn bé thực hành gọi tên cảm xúc, gợi ý sử dụng Góc bình tĩnh khi bé gặp khó khăn."
    else:
        auto_conclusion = f"Bé {student_name} gặp nhiều khó khăn trong quản trị cảm xúc (PEQ={auto_peq}), thuộc nhóm HỖ TRỢ ĐẶC BIỆT."
        auto_plan = f"Kế hoạch: Thiết lập can thiệp 1-1, sử dụng kỹ thuật dỗ dành ôm xoa dịu, phối hợp chặt chẽ với phụ huynh."

    return {
        "TC1": auto_tc1, "TC2": auto_tc2, "TC3": auto_tc3,
        "TC4": auto_tc4, "TC5": auto_tc5, "TC6": auto_tc6,
        "P_EQ": auto_peq, "Group_Clean": auto_group,
        "Context": auto_context, "Conclusion": auto_conclusion, "Plan": auto_plan
    }

def is_class_match(c_val, target_class):
    if not c_val or not target_class or target_class == "Tất cả các lớp":
        return True
    c1 = clean_key(c_val)
    c2 = clean_key(target_class)
    if c1 == c2 or c1 in c2 or c2 in c1:
        return True
    return False

def filter_records_multilevel(df, campus_code=None, campus_name=None, class_type=None, school_year=None, term_val=None, teacher_name=None, student_name=None):
    if df is None or df.empty:
        return pd.DataFrame()
        
    res_df = df.copy()
    
    if campus_code and campus_code != "ALL" and "campus_code" in res_df.columns:
        res_df = res_df[res_df["campus_code"].apply(clean_key) == clean_key(campus_code)]
    elif campus_name and campus_name != "Tất cả cơ sở" and "campus" in res_df.columns:
        res_df = res_df[res_df["campus"].apply(clean_key) == clean_key(campus_name)]
        
    if class_type and class_type != "Tất cả các lớp" and "class" in res_df.columns:
        res_df = res_df[res_df["class"].apply(lambda v: is_class_match(v, class_type))]
        
    if school_year and school_year != "Tất cả năm học" and "school_year" in res_df.columns:
        res_df = res_df[res_df["school_year"].astype(str).str.strip() == str(school_year).strip()]
        
    if term_val and term_val != "Tất cả mốc thời gian" and term_val != "Tất cả kỳ/tháng" and "term" in res_df.columns:
        res_df = res_df[res_df["term"].astype(str).str.strip().apply(clean_key).str.contains(clean_key(term_val))]
        
    if teacher_name and teacher_name != "Tất cả giáo viên" and "teacher" in res_df.columns:
        res_df = res_df[res_df["teacher"].apply(lambda v: is_teacher_match(v, {"name": teacher_name, "username": teacher_name}))]
        
    if student_name and student_name != "Tất cả học sinh" and "student" in res_df.columns:
        res_df = res_df[res_df["student"].apply(lambda v: is_student_match(v, student_name))]
        
    return res_df

def synthesize_daily_logs_report(daily_df, campus_name=None, class_type=None, school_year=None, term_val=None, teacher_name=None, student_name=None):
    if daily_df is None or daily_df.empty:
        return pd.DataFrame()
        
    filt_df = filter_records_multilevel(daily_df, campus_name=campus_name, class_type=class_type, school_year=school_year, term_val=term_val, teacher_name=teacher_name, student_name=student_name)
    if filt_df.empty:
        return pd.DataFrame()
        
    s_col = "student" if "student" in filt_df.columns else "Student"
    t_col = "teacher" if "teacher" in filt_df.columns else "Teacher"
    c_col = "campus" if "campus" in filt_df.columns else "Campus"
    cl_col = "class" if "class" in filt_df.columns else "Class"
    
    synth_rows = []
    grouped = filt_df.groupby([s_col, t_col], as_index=False)
    
    for (std_val, t_val), group_df in grouped:
        if not std_val: continue
        mapped = auto_map_daily_to_criteria(std_val, t_val, group_df)
        if mapped:
            c_val = group_df[c_col].iloc[0] if c_col in group_df.columns else ""
            class_val = group_df[cl_col].iloc[0] if cl_col in group_df.columns else ""
            synth_rows.append({
                "teacher": t_val, "campus": c_val, "class": class_val, "student": std_val,
                "school_year": school_year if school_year and school_year != "Tất cả năm học" else "2025 - 2026",
                "term": term_val if term_val and "Tất cả" not in term_val else "Đánh giá Tổng hợp từ Nhật Ký",
                "eval_date": datetime.today().strftime("%d/%m/%Y"),
                "tc1": mapped["TC1"], "tc2": mapped["TC2"], "tc3": mapped["TC3"],
                "tc4": mapped["TC4"], "tc5": mapped["TC5"], "tc6": mapped["TC6"],
                "p_eq": mapped["P_EQ"], "group_clean": mapped["Group_Clean"],
                "context": mapped["Context"], "conclusion": mapped["Conclusion"], "plan": mapped["Plan"]
            })
            
    if not synth_rows:
        return pd.DataFrame()
        
    synth_df = pd.DataFrame(synth_rows)
    return format_evaluations_export(synth_df)

# -----------------------------------------------------------------------------
# 5. KHÔNG GIAN DÀNH CHO NGƯỜI DÙNG DỰA TRÊN VAI TRÒ (AUTHENTICATION)
# -----------------------------------------------------------------------------
if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

users_dict = get_all_users_dict()

if hasattr(st, "query_params") and "user" in st.query_params and not st.session_state.logged_user:
    param_u = st.query_params["user"]
    clean_p_u = clean_key(param_u)
    if clean_p_u in users_dict:
        st.session_state.logged_user = clean_p_u

if not st.session_state.logged_user:
    st.markdown("---")
    st.subheader("🔑 ĐĂNG NHẬP HỆ THỐNG")
    
    with st.form(key="login_form"):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            input_user = st.text_input("👤 Tên đăng nhập / Số điện thoại:").strip()
        with col_u2:
            input_pass = st.text_input("🔒 Mật khẩu:", type="password").strip()
            
        btn_login = st.form_submit_button("🚀 Đăng Nhập Hệ Thống")
        
        if btn_login:
            ok, u_key, u_info, msg = authenticate_user(input_user, input_pass, users_dict)
            if ok:
                st.session_state.logged_user = u_key
                st.success(f"🎉 Đăng nhập thành công! Xin chào **{u_info['name']}**.")
                st.rerun()
            else:
                if msg == "WRONG_PASSWORD":
                    st.error("❌ Mật khẩu không chính xác. Vui lòng thử lại!")
                else:
                    st.error("❌ Tên đăng nhập không tồn tại trên hệ thống!")
                    
    st.info("💡 **Gợi ý tài khoản trải nghiệm:** Admin Tổng (`admin` / `admin123`) | BGH Hà Đô (`BGHHD` / `123456`)")

else:
    user_info = users_dict.get(st.session_state.logged_user, {
        "name": "Người dùng", "role": "teacher", "campus": "TFA", "class_name": "Lớp"
    })
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
        if hasattr(st, "query_params") and "user" in st.query_params:
            del st.query_params["user"]
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
                        st.session_state.users_df["_clean"] = st.session_state.users_df["username"].apply(clean_key)
                        st.session_state.users_df = st.session_state.users_df.drop_duplicates(subset=["_clean"], keep="last").drop(columns=["_clean"])
                        
                        if save_sheet_to_gas("Users", st.session_state.users_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn trên Google Sheets! TK: `{BGH_u}` | Mật khẩu: `{BGH_p}`")
                            st.rerun()

            st.markdown("---")
            st.dataframe(st.session_state.users_df, use_container_width=True)

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ TOÀN HỆ THỐNG")
            
            st.markdown("##### 🔍 Bộ Lọc Dữ Liệu Báo Cáo Chuyên Sâu 6 Cấp (Toàn Trường)")
            c1, c2, c3 = st.columns(3)
            with c1: sa_sel_campus = st.selectbox("1. Chọn Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()), key="sa_eval_campus")
            with c2: sa_sel_class = st.selectbox("2. Chọn Khối Lớp:", ["Tất cả các lớp"] + TFA_CLASSES, key="sa_eval_class")
            with c3: sa_sel_year = st.selectbox("3. Chọn Năm Học:", ["Tất cả năm học"] + SCHOOL_YEAR_OPTIONS, key="sa_eval_year")
            
            c4, c5, c6 = st.columns(3)
            with c4: sa_sel_term = st.selectbox("4. Mốc Thời Gian (Tháng/Quý):", ["Tất cả mốc thời gian"] + [f"Tháng {m}" for m in range(1, 13)] + ["Quý 1", "Quý 2", "Quý 3", "Quý 4"], key="sa_eval_term")
            
            u_df = st.session_state.users_df
            teacher_list = ["Tất cả giáo viên"]
            if not u_df.empty:
                t_mask = u_df["role"].apply(clean_key) == "teacher"
                if sa_sel_campus != "Tất cả cơ sở":
                    t_mask = t_mask & (u_df["campus"].apply(clean_key) == clean_key(sa_sel_campus))
                if sa_sel_class != "Tất cả các lớp":
                    t_mask = t_mask & u_df["class_name"].apply(lambda v: is_class_match(v, sa_sel_class))
                teacher_list += sorted(list(set(u_df[t_mask]["name"].dropna().tolist())))
            with c5: sa_sel_teacher = st.selectbox("5. Chọn Giáo Viên:", teacher_list, key="sa_eval_teacher")
            
            s_df = st.session_state.students_df
            student_list = ["Tất cả học sinh"]
            if not s_df.empty:
                if sa_sel_teacher != "Tất cả giáo viên":
                    s_df = s_df[s_df["teacher_user"].apply(lambda v: is_teacher_match(v, {"name": sa_sel_teacher, "username": sa_sel_teacher}))]
                student_list += sorted(list(set(s_df["student_name"].dropna().tolist())))
            with c6: sa_sel_student = st.selectbox("6. Chọn Học Sinh:", student_list, key="sa_eval_student")
            
            st.markdown("---")
            df_eval_raw = st.session_state.evaluations_df
            df_eval_filtered = filter_records_multilevel(
                df_eval_raw, campus_name=sa_sel_campus, class_type=sa_sel_class,
                school_year=sa_sel_year, term_val=sa_sel_term,
                teacher_name=sa_sel_teacher, student_name=sa_sel_student
            )
            
            if not df_eval_filtered.empty:
                st.markdown("#### 1. Báo Cáo Đánh Giá EQ 6 Tiêu Chí (Đã Lưu)")
                df_export = format_evaluations_export(df_eval_filtered)
                st.dataframe(df_export, use_container_width=True)
                render_eq_charts(df_eval_filtered, "(Toàn Trường)")
                st.download_button(
                    "📥 Xuất File CSV/Excel Bảng Đánh Giá EQ (Theo Bộ Lọc)",
                    df_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bao_Cao_Tong_Hop_EQ_TFA_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv",
                    key="sa_eval_download_btn"
                )
            else:
                st.markdown("#### ⚡ BÁO CÁO EQ TỰ ĐỘNG TỔNG HỢP TỪ NHẬT KÝ HẰNG NGÀY (DAILY LOGS)")
                df_daily_raw = st.session_state.daily_logs_df
                df_synth = synthesize_daily_logs_report(
                    df_daily_raw, campus_name=sa_sel_campus, class_type=sa_sel_class,
                    school_year=sa_sel_year, term_val=sa_sel_term,
                    teacher_name=sa_sel_teacher, student_name=sa_sel_student
                )
                if not df_synth.empty:
                    st.dataframe(df_synth, use_container_width=True)
                    st.download_button(
                        "📥 Xuất File CSV/Excel Bảng Báo Cáo EQ Tự Động From DailyLogs",
                        df_synth.to_csv(index=False).encode('utf-8-sig'),
                        f"Bao_Cao_EQ_Tu_Dong_TFA_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv",
                        key="sa_dl_download_btn"
                    )
                else:
                    st.info("ℹ️ Chưa ghi nhận dữ liệu đánh giá hoặc nhật ký ngày phù hợp với bộ lọc đã chọn.")

        elif main_menu == "📈 3. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XU HƯỚNG PHÁT TRIỂN EQ TOÀN TRƯỜNG")
            df_comp_raw = st.session_state.comparisons_df
            df_comp_export = format_comparisons_export(df_comp_raw)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Toàn Trường")
            st.table(calculate_class_stats(df_comp_raw))
            
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Xu Hướng EQ Chuẩn Mẫu",
                df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bang_Xu_Huong_EQ_TFA_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
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
                            st.session_state.users_df["_clean"] = st.session_state.users_df["username"].apply(clean_key)
                            st.session_state.users_df = st.session_state.users_df.drop_duplicates(subset=["_clean"], keep="last").drop(columns=["_clean"])
                            
                            if save_sheet_to_gas("Users", st.session_state.users_df):
                                st.success(f"🎉 Đã lưu vĩnh viễn giáo viên {t_name} trên Google Sheets! TK: `{gen_u}` | Mật khẩu: `123456`")
                                st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")

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
                    
                    if st.session_state.get(f"editing_gv_{idx}", False):
                        with st.form(key=f"form_edit_gv_detail_{idx}"):
                            st.markdown(f"**Sửa thông tin cho Giáo viên: {u_name}**")
                            col_e1, col_e2, col_e3 = st.columns(3)
                            with col_e1: new_gv_class = st.selectbox("Khối Lớp:", TFA_CLASSES, index=TFA_CLASSES.index(u_class) if u_class in TFA_CLASSES else 0)
                            with col_e2: new_gv_name = st.text_input("Họ và tên:", value=u_name)
                            with col_e3: new_gv_pass = st.text_input("Mật khẩu mới:", value=str(row.get('password', row.get('Password', '123456'))))
                            btn_save_gv = st.form_submit_button("💾 Lưu Thay Đổi")
                            
                            if btn_save_gv:
                                st.session_state.users_df.loc[idx, 'name'] = new_gv_name.strip()
                                st.session_state.users_df.loc[idx, 'class_name'] = new_gv_class
                                st.session_state.users_df.loc[idx, 'password'] = new_gv_pass.strip()
                                if save_sheet_to_gas("Users", st.session_state.users_df):
                                    st.session_state[f"editing_gv_{idx}"] = False
                                    st.success("🎉 Đã cập nhật thông tin Giáo viên vĩnh viễn!")
                                    st.rerun()
                    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("Cơ sở chưa có giáo viên nào.")

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            st.subheader(f"📊 BÁO CÁO TỔNG HỢP EQ CƠ SỞ: {my_campus.upper()}")
            
            st.markdown("##### 🔍 Bộ Lọc Dữ Liệu Báo Cáo Cơ Sở (Phân Cấp Động)")
            col_ca1, col_ca2, col_ca3 = st.columns(3)
            with col_ca1: ca_sel_class = st.selectbox("1. Chọn Khối Lớp:", ["Tất cả các lớp"] + TFA_CLASSES, key="ca_eval_class")
            with col_ca2: ca_sel_year = st.selectbox("2. Chọn Năm Học:", ["Tất cả năm học"] + SCHOOL_YEAR_OPTIONS, key="ca_eval_year")
            with col_ca3: ca_sel_term = st.selectbox("3. Mốc Thời Gian (Tháng/Quý):", ["Tất cả kỳ/tháng"] + [f"Tháng {m}" for m in range(1, 13)] + ["Quý 1", "Quý 2", "Quý 3", "Quý 4"], key="ca_eval_term")
            
            col_ca4, col_ca5 = st.columns(2)
            u_df = st.session_state.users_df
            teacher_list = ["Tất cả giáo viên"]
            if not u_df.empty:
                t_mask = (u_df["role"].apply(clean_key) == "teacher") & (u_df["campus_code"].apply(clean_key) == clean_key(my_code))
                if ca_sel_class != "Tất cả các lớp":
                    t_mask = t_mask & u_df["class_name"].apply(lambda v: is_class_match(v, ca_sel_class))
                teacher_list += sorted(list(set(u_df[t_mask]["name"].dropna().tolist())))
            with col_ca4: ca_sel_teacher = st.selectbox("4. Chọn Giáo Viên:", teacher_list, key="ca_eval_teacher")
            
            s_df = st.session_state.students_df
            student_list = ["Tất cả học sinh"]
            if not s_df.empty:
                if ca_sel_teacher != "Tất cả giáo viên":
                    s_df = s_df[s_df["teacher_user"].apply(lambda v: is_teacher_match(v, {"name": ca_sel_teacher, "username": ca_sel_teacher}))]
                student_list += sorted(list(set(s_df["student_name"].dropna().tolist())))
            with col_ca5: ca_sel_student = st.selectbox("5. Chọn Học Sinh:", student_list, key="ca_eval_student")
            
            st.markdown("---")
            df_eval_raw = st.session_state.evaluations_df
            df_eval_filtered = filter_records_multilevel(
                df_eval_raw, campus_code=my_code, campus_name=my_campus,
                class_type=ca_sel_class, school_year=ca_sel_year,
                term_val=ca_sel_term, teacher_name=ca_sel_teacher, student_name=ca_sel_student
            )
            
            if not df_eval_filtered.empty:
                st.markdown("#### 1. Báo Cáo Đánh Giá EQ 6 Tiêu Chí Cơ Sở (Đã Lưu)")
                df_export = format_evaluations_export(df_eval_filtered)
                st.dataframe(df_export, use_container_width=True)
                st.download_button(
                    "📥 Xuất File CSV/Excel Báo Cáo EQ Cơ Sở (Theo Bộ Lọc)",
                    df_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bao_Cao_EQ_{my_code}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv",
                    key="ca_eval_download_btn"
                )
            else:
                st.markdown("#### ⚡ BÁO CÁO EQ TỰ ĐỘNG TỔNG HỢP TỪ NHẬT KÝ HẰNG NGÀY (DAILY LOGS)")
                df_daily_raw = st.session_state.daily_logs_df
                df_synth = synthesize_daily_logs_report(
                    df_daily_raw, campus_name=my_campus, class_type=ca_sel_class,
                    school_year=ca_sel_year, term_val=ca_sel_term,
                    teacher_name=ca_sel_teacher, student_name=ca_sel_student
                )
                if not df_synth.empty:
                    st.dataframe(df_synth, use_container_width=True)
                    st.download_button(
                        f"📥 Tải Báo Cáo EQ Tự Động Từ Nhật Ký Ngày Cơ Sở {my_code} (.csv)",
                        df_synth.to_csv(index=False).encode('utf-8-sig'),
                        f"Bao_Cao_EQ_Tu_Dong_DailyLogs_{my_code}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv",
                        key="ca_dl_download_btn"
                    )
                else:
                    st.info("ℹ️ Chưa ghi nhận dữ liệu đánh giá hoặc nhật ký ngày phù hợp với bộ lọc đã chọn.")

        else:
            st.subheader(f"📈 BẢNG SO SÁNH XU HƯỚNG EQ CƠ SỞ: {my_campus.upper()}")
            c_col = "campus" if "campus" in st.session_state.comparisons_df.columns else "Campus"
            df_comp_c = filter_df_by_clean_col(st.session_state.comparisons_df, c_col, my_campus)
            df_comp_export = format_comparisons_export(df_comp_c)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Xu Hướng EQ Cơ Sở",
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
            st.subheader("🏫 TỰ TẠO LỚP HỌC & QUẢN LÝ HỌC SINH")
            
            with st.form(key="form_update_class_name"):
                col_l1, col_l2 = st.columns(2)
                with col_l1: sel_class_type = st.selectbox("Chọn Khối lớp:", TFA_CLASSES)
                with col_l2: custom_class_name = st.text_input("Tên riêng của Lớp:", value=user_info.get("class_name", sel_class_type))
                btn_class = st.form_submit_button("💾 Cập Nhật Tên Lớp")
                if btn_class:
                    u_col = "username" if "username" in st.session_state.users_df.columns else "Username"
                    user_mask = st.session_state.users_df[u_col].apply(clean_key) == clean_key(user_key)
                    user_idx = st.session_state.users_df[user_mask].index
                    if not user_idx.empty:
                        st.session_state.users_df.loc[user_idx, "class_name"] = custom_class_name
                        if save_sheet_to_gas("Users", st.session_state.users_df):
                            st.success(f"🎉 Đã lưu tên lớp: **{custom_class_name}**")
                            st.rerun()

            st.markdown("---")
            
            with st.form(key="form_add_student", clear_on_submit=True):
                st.markdown("##### ➕ Thêm Học Sinh Mới")
                col_std1, col_std2 = st.columns([1.8, 2.2])
                with col_std1: new_student_val = st.text_input("Họ và tên học sinh mới:")
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
                                "teacher_user": clean_key(user_key),
                                "student_name": clean_name,
                                "student_note": clean_note
                            }])
                            st.session_state.students_df = pd.concat([st.session_state.students_df, new_std_row], ignore_index=True)
                            
                        st.session_state.students_df["_t_clean"] = st.session_state.students_df[t_col].apply(clean_key)
                        st.session_state.students_df["_s_clean"] = st.session_state.students_df[s_col].apply(clean_key)
                        st.session_state.students_df = st.session_state.students_df.drop_duplicates(subset=["_t_clean", "_s_clean"], keep="last").drop(columns=["_t_clean", "_s_clean"])
                        
                        if save_sheet_to_gas("Students", st.session_state.students_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn bé **{clean_name}** vào danh sách lớp!")
                            st.rerun()

            st.markdown("---")
            st.markdown("##### 📋 Danh Sách Học Sinh Trong Lớp")
            
            t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
            my_stds_df = filter_teacher_records(st.session_state.students_df, t_col, user_info)
            
            if not my_stds_df.empty:
                for idx in my_stds_df.index:
                    row = st.session_state.students_df.loc[idx]
                    s_name = row.get('student_name', row.get('Student_Name', ''))
                    s_note = str(row.get('student_note', row.get('Student_Note', ''))).strip()
                    if pd.isna(s_note) or s_note.lower() in ["nan", "none"]: s_note = ""
                    
                    c_s1, c_s2, c_s3 = st.columns([3.2, 0.9, 0.9])
                    with c_s1:
                        st.write(f"👦/👧 **{s_name}**")
                        if s_note: st.markdown(f"<span class='note-badge'>📌 Ghi chú: {s_note}</span>", unsafe_allow_html=True)
                    with c_s2:
                        if st.button("✏️ Sửa", key=f"edit_std_{idx}"):
                            st.session_state[f"editing_std_{idx}"] = not st.session_state.get(f"editing_std_{idx}", False)
                    with c_s3:
                        if st.button("🗑️ Xóa", key=f"del_std_{idx}"):
                            st.session_state.students_df = st.session_state.students_df.drop(idx).reset_index(drop=True)
                            if save_sheet_to_gas("Students", st.session_state.students_df):
                                st.success(f"Đã xóa học sinh **{s_name}**!")
                                st.rerun()
                    
                    if st.session_state.get(f"editing_std_{idx}", False):
                        with st.form(key=f"form_edit_std_{idx}"):
                            st.markdown(f"**Chỉnh sửa thông tin bé: {s_name}**")
                            col_es1, col_es2 = st.columns(2)
                            with col_es1: new_name_val = st.text_input("Họ và tên:", value=s_name)
                            with col_es2: new_note_val = st.text_input("Ghi chú đặc biệt:", value=s_note)
                            btn_save_edit = st.form_submit_button("💾 Lưu Thay Đổi")
                            if btn_save_edit:
                                st.session_state.students_df.loc[idx, 'student_name'] = new_name_val.strip()
                                st.session_state.students_df.loc[idx, 'student_note'] = new_note_val.strip()
                                if save_sheet_to_gas("Students", st.session_state.students_df):
                                    st.session_state[f"editing_std_{idx}"] = False
                                    st.success(f"🎉 Đã cập nhật thông tin bé **{new_name_val.strip()}**!")
                                    st.rerun()
                    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("Lớp chưa có học sinh nào.")

        elif main_menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
            st.subheader("📋 HỒ SƠ CẢM XÚC CÁ NHÂN (HẰNG NGÀY)")
            
            t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
            s_col = "student_name" if "student_name" in st.session_state.students_df.columns else "Student_Name"
            
            my_stds_df = filter_teacher_records(st.session_state.students_df, t_col, user_info)
            my_stds = my_stds_df[s_col].dropna().tolist() if not my_stds_df.empty and s_col in my_stds_df.columns else []
            
            if not my_stds:
                st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng thêm học sinh ở Mục 1!")
            else:
                col_s1, col_s2, col_s3 = st.columns([1.5, 1.5, 1])
                with col_s1: std_select = st.selectbox("👦/👧 Chọn học sinh:", my_stds)
                with col_s2: log_date = st.date_input("🗓️ Chọn Ngày cần nhập / xem lại:", value=datetime.today())
                with col_s3:
                    std_match = my_stds_df[my_stds_df[s_col] == std_select] if not my_stds_df.empty and s_col in my_stds_df.columns else pd.DataFrame()
                    if not std_match.empty:
                        n_col = "student_note" if "student_note" in std_match.columns else "Student_Note"
                        val_note = std_match.iloc[0].get(n_col, "")
                        std_note_info = str(val_note).strip() if pd.notna(val_note) else ""
                        if std_note_info.lower() in ["nan", "none"]: std_note_info = ""
                        if std_note_info:
                            st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**\n\n📌 **Lưu ý:** {std_note_info}")
                        else:
                            st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**")
                    else:
                        st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**")
                
                selected_date_str = log_date.strftime("%d/%m/%Y")
                
                # SEARCH FOR EXISTING DAILY LOG
                d_df = st.session_state.daily_logs_df
                existing_log = None
                
                if not d_df.empty:
                    d_t_col = "teacher" if "teacher" in d_df.columns else "Teacher"
                    d_s_col = "student" if "student" in d_df.columns else "Student"
                    d_d_col = "date" if "date" in d_df.columns else "Date"
                    
                    matched_logs = filter_teacher_records(d_df, d_t_col, user_info)
                    if not matched_logs.empty:
                        match_log_mask = matched_logs.apply(
                            lambda r: is_student_match(r.get(d_s_col), std_select) and clean_date_str(r.get(d_d_col)) == clean_date_str(selected_date_str),
                            axis=1
                        )
                        if match_log_mask.any():
                            existing_log = matched_logs[match_log_mask].iloc[-1]
                
                if existing_log is not None:
                    st.success(f"ℹ️ **Đã tìm thấy Nhật ký ngày {selected_date_str} của bé {std_select}.** Bạn có thể xem lại hoặc chỉnh sửa thông tin bên dưới rồi bấm Lưu!")
                else:
                    st.info(f"🗓️ Ngày **{selected_date_str}** chưa có nhật ký. Nhập thông tin bên dưới để tạo mới!")

                saved_details_json = {}
                saved_note_context = ""
                saved_note_interv = ""
                saved_summary = ""
                saved_trend = "Duy trì cảm xúc tích cực, vui vẻ cả ngày"
                saved_custom_trend = ""
                
                if existing_log is not None:
                    saved_note_context = str(existing_log.get("note", existing_log.get("Note", "")))
                    if saved_note_context.lower() in ["nan", "none"]: saved_note_context = ""
                    
                    saved_note_interv = str(existing_log.get("intervention", existing_log.get("Intervention", "")))
                    if saved_note_interv.lower() in ["nan", "none"]: saved_note_interv = ""
                    
                    raw_summary_val = str(existing_log.get("summary", existing_log.get("Summary", "")))
                    if raw_summary_val.lower() in ["nan", "none"]: raw_summary_val = ""
                    
                    if raw_summary_val.startswith("[") and "]" in raw_summary_val:
                        parts = raw_summary_val.split("]", 1)
                        trend_in_bracket = parts[0].replace("[", "").strip()
                        saved_summary = parts[1].strip()
                        
                        daily_trend_options_base = [
                            "Duy trì cảm xúc tích cực, vui vẻ cả ngày",
                            "Có xáo trộn nhỏ ở đầu ngày, nhanh chóng cân bằng",
                            "Tự tin, hào hứng tham gia các hoạt động nhóm",
                            "Hơi thu mình, rụt rè nhưng hợp tác khi cô khuyến khích",
                            "Dễ kích động, cần cô hỗ trợ xoa dịu và theo dõi sát"
                        ]
                        
                        if trend_in_bracket in daily_trend_options_base:
                            saved_trend = trend_in_bracket
                        else:
                            saved_trend = "Khác (Tự nhập nhận xét riêng...)"
                            saved_custom_trend = trend_in_bracket
                    else:
                        saved_summary = raw_summary_val

                    raw_json_str = str(existing_log.get("details_json", existing_log.get("Details_Json", "")))
                    if raw_json_str and raw_json_str.startswith("{"):
                        try:
                            saved_details_json = json.loads(raw_json_str)
                        except Exception:
                            saved_details_json = {}

                st.markdown("---")
                st.markdown("#### 1. Hoạt động trong ngày")
                
                routine_rows = []
                for r in TFA_ROUTINES:
                    r_item = {"Hoạt động": r}
                    act_data = saved_details_json.get(r, {}) if saved_details_json else {}
                    active_emos = act_data.get("emotions", []) if isinstance(act_data, dict) else []
                    act_note = act_data.get("note", "") if isinstance(act_data, dict) else ""
                    
                    if not saved_details_json and existing_log is not None:
                        old_emos_text = str(existing_log.get("emotions", existing_log.get("Emotions", "")))
                        if r in old_emos_text:
                            for e_col in EMOTION_COLS:
                                e_name = e_col.split(" ")[0]
                                if e_name in old_emos_text:
                                    active_emos.append(e_col)

                    for e_col in EMOTION_COLS:
                        r_item[e_col] = True if e_col in active_emos else False
                        
                    r_item["Ghi chú chi tiết hành vi"] = act_note
                    routine_rows.append(r_item)
                
                df_routine_init = pd.DataFrame(routine_rows)
                
                dynamic_prefix = f"{clean_key(std_select)}_{selected_date_str.replace('/', '_')}"
                
                edited_routine_df = st.data_editor(
                    df_routine_init,
                    column_config={
                        "Hoạt động": st.column_config.TextColumn("Hoạt động trong ngày", disabled=True, width="medium"),
                        "Ghi chú chi tiết hành vi": st.column_config.TextColumn("Ghi chú bối cảnh", width="large")
                    },
                    hide_index=True, use_container_width=True, key=f"editor_{dynamic_prefix}"
                )
                
                st.markdown("---")

                daily_trend_options = [
                    "Duy trì cảm xúc tích cực, vui vẻ cả ngày",
                    "Có xáo trộn nhỏ ở đầu ngày, nhanh chóng cân bằng",
                    "Tự tin, hào hứng tham gia các hoạt động nhóm",
                    "Hơi thu mình, rụt rè nhưng hợp tác khi cô khuyến khích",
                    "Dễ kích động, cần cô hỗ trợ xoa dịu và theo dõi sát",
                    "Khác (Tự nhập nhận xét riêng...)"
                ]
                
                trend_index = daily_trend_options.index(saved_trend) if saved_trend in daily_trend_options else 5

                with st.form(key=f"daily_form_{dynamic_prefix}"):
                    col_o1, col_o2 = st.columns(2)
                    with col_o1: note_context = st.text_area("📌 Bối cảnh và biểu hiện nổi bật:", value=saved_note_context)
                    with col_o2: note_intervention = st.text_area("🤝 Can thiệp và hỗ trợ của giáo viên:", value=saved_note_interv)
                        
                    st.markdown("---")
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        sel_trend = st.selectbox(
                            "📈 Xu hướng cảm xúc chung trong ngày:", 
                            daily_trend_options, 
                            index=trend_index, 
                            key=f"trend_sel_{dynamic_prefix}"
                        )
                        
                        custom_trend_text = st.text_input(
                            "✍️ Nhập xu hướng riêng (khi chọn Khác):", 
                            value=saved_custom_trend, 
                            key=f"custom_trend_input_{dynamic_prefix}"
                        )
                            
                    with col_d2: daily_summary = st.text_area("💬 Nhận xét bổ sung của giáo viên:", value=saved_summary)
                    
                    btn_save_daily = st.form_submit_button("💾 LƯU HỒ SƠ CẢM XÚC HẰNG NGÀY")
                    
                    if btn_save_daily:
                        emotions_summary_list = []
                        details_dict = {}
                        for idx, row in edited_routine_df.iterrows():
                            act_name = row["Hoạt động"]
                            active_emos = [e_col for e_col in EMOTION_COLS if row[e_col] == True]
                            act_note = str(row["Ghi chú chi tiết hành vi"]).strip()
                            if active_emos or act_note:
                                e_str = ", ".join(active_emos) if active_emos else "Ghi nhận"
                                emotions_summary_list.append(f"{act_name}: {e_str}" + (f" ({act_note})" if act_note else ""))
                            details_dict[act_name] = {"emotions": active_emos, "note": act_note}
                        
                        full_emotions_str = " | ".join(emotions_summary_list) if emotions_summary_list else "Bình thường"
                        json_str = json.dumps(details_dict, ensure_ascii=False)
                        
                        final_trend_str = custom_trend_text.strip() if sel_trend == "Khác (Tự nhập nhận xét riêng...)" and custom_trend_text.strip() else sel_trend
                        
                        d_df = st.session_state.daily_logs_df
                        d_t_col = "teacher" if "teacher" in d_df.columns else "Teacher"
                        d_s_col = "student" if "student" in d_df.columns else "Student"
                        d_d_col = "date" if "date" in d_df.columns else "Date"
                        
                        matched_logs = filter_teacher_records(d_df, d_t_col, user_info)
                        existing_mask = pd.Series([False] * len(d_df), index=d_df.index)
                        
                        if not matched_logs.empty:
                            for idx in matched_logs.index:
                                row_s = d_df.loc[idx, d_s_col]
                                row_d = d_df.loc[idx, d_d_col]
                                if is_student_match(row_s, std_select) and clean_date_str(row_d) == clean_date_str(selected_date_str):
                                    existing_mask.loc[idx] = True
                        
                        if existing_mask.any():
                            st.session_state.daily_logs_df.loc[existing_mask, "emotions"] = full_emotions_str
                            st.session_state.daily_logs_df.loc[existing_mask, "note"] = note_context
                            st.session_state.daily_logs_df.loc[existing_mask, "intervention"] = note_intervention
                            st.session_state.daily_logs_df.loc[existing_mask, "summary"] = f"[{final_trend_str}] {daily_summary}"
                            st.session_state.daily_logs_df.loc[existing_mask, "details_json"] = json_str
                        else:
                            new_log = pd.DataFrame([{
                                "teacher": user_info.get("name", user_info.get("raw_username", user_key)),
                                "campus": user_info['campus'],
                                "class": user_info.get('class_name', 'Pre-school (3-4 tuổi)'),
                                "student": std_select, "date": selected_date_str,
                                "routine": "Toàn bộ hoạt động trong ngày", "emotions": full_emotions_str,
                                "note": note_context, "intervention": note_intervention,
                                "summary": f"[{final_trend_str}] {daily_summary}", "details_json": json_str
                            }])
                            st.session_state.daily_logs_df = pd.concat([st.session_state.daily_logs_df, new_log], ignore_index=True)

                        if save_sheet_to_gas("DailyLogs", st.session_state.daily_logs_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn Hồ sơ cảm xúc ngày {selected_date_str} cho bé **{std_select}**!")
                            st.rerun()

        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ")
            
            t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
            s_col = "student_name" if "student_name" in st.session_state.students_df.columns else "Student_Name"
            my_stds_df = filter_teacher_records(st.session_state.students_df, t_col, user_info)
            my_stds = my_stds_df[s_col].dropna().tolist() if not my_stds_df.empty and s_col in my_stds_df.columns else []
            
            if not my_stds: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_e1, col_e2, col_e3, col_e4 = st.columns([1.5, 1.2, 1.2, 1.2])
                with col_e1: std_eval = st.selectbox("Chọn học sinh:", my_stds)
                with col_e2: eval_school_year = st.selectbox("Năm học:", SCHOOL_YEAR_OPTIONS, index=1)
                with col_e3: 
                    eval_month = st.selectbox("Chọn Tháng đánh giá:", [f"Tháng {m}" for m in range(1, 13)], index=8)
                    m_num = int(eval_month.replace('Tháng ', ''))
                    term = f"{eval_month} / Kỳ {1 if (m_num >= 9 or m_num == 1) else 2}"
                with col_e4:
                    eval_date_val = st.date_input("🗓️ Ngày đánh giá:", value=datetime.today())
                    eval_date_str = eval_date_val.strftime("%d/%m/%Y")
                    
                user_class_str = user_info.get('class_name', 'Kindergarten (4-5 tuổi)')
                if "Pre-school" in user_class_str or "3-4" in user_class_str: curr_age_group = "Pre-school (3-4 tuổi)"
                elif "Pre-primary" in user_class_str or "5-6" in user_class_str: curr_age_group = "Pre-primary (5-6 tuổi)"
                else: curr_age_group = "Kindergarten (4-5 tuổi)"
                
                st.info(f"📘 Bộ tiêu chí: **{curr_age_group}** | 📅 Ngày đánh giá: **{eval_date_str}** | 🏫 Năm học: **{eval_school_year}**")
                
                if st.button("⚡ TỰ ĐỘNG TỔNG HỢP EQ THÁNG (1-CLICK TỪ NHẬT KÝ HẰNG NGÀY)"):
                    mapped_res = auto_map_daily_to_criteria(std_eval, user_info['name'], st.session_state.daily_logs_df)
                    if mapped_res:
                        st.session_state[f"tc1_{std_eval}"] = mapped_res["TC1"]
                        st.session_state[f"tc2_{std_eval}"] = mapped_res["TC2"]
                        st.session_state[f"tc3_{std_eval}"] = mapped_res["TC3"]
                        st.session_state[f"tc4_{std_eval}"] = mapped_res["TC4"]
                        st.session_state[f"tc5_{std_eval}"] = mapped_res["TC5"]
                        st.session_state[f"tc6_{std_eval}"] = mapped_res["TC6"]
                        st.session_state[f"ctx_{std_eval}"] = mapped_res["Context"]
                        st.session_state[f"cnc_{std_eval}"] = mapped_res["Conclusion"]
                        st.session_state[f"pln_{std_eval}"] = mapped_res["Plan"]
                        st.success(f"🎉 Đã tự động phân tích nhật ký cho bé **{std_eval}**!")

                curr_crit_map = CRITERIA_DATA.get(curr_age_group, CRITERIA_DATA["Kindergarten (4-5 tuổi)"])
                col_c1, col_c2 = st.columns(2)
                
                def_tc1 = st.session_state.get(f"tc1_{std_eval}", 3)
                def_tc2 = st.session_state.get(f"tc2_{std_eval}", 3)
                def_tc3 = st.session_state.get(f"tc3_{std_eval}", 3)
                def_tc4 = st.session_state.get(f"tc4_{std_eval}", 3)
                def_tc5 = st.session_state.get(f"tc5_{std_eval}", 3)
                def_tc6 = st.session_state.get(f"tc6_{std_eval}", 3)
                
                opts = [1, 2, 3, 4]
                
                with col_c1:
                    st.markdown("##### 1. TC1: Nhận biết cảm xúc bản thân")
                    tc1_val = st.radio("Chọn Mức cho TC1:", options=opts, index=def_tc1-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc1_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC1'][tc1_val]}")
                    
                    st.markdown("##### 2. TC2: Gọi tên và diễn đạt cảm xúc")
                    tc2_val = st.radio("Chọn Mức cho TC2:", options=opts, index=def_tc2-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc2_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC2'][tc2_val]}")
                    
                    st.markdown("##### 3. TC3: Điều chỉnh và kiểm soát cảm xúc")
                    tc3_val = st.radio("Chọn Mức cho TC3:", options=opts, index=def_tc3-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc3_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC3'][tc3_val]}")

                with col_c2:
                    st.markdown("##### 4. TC4: Đồng cảm và quan hệ xã hội")
                    tc4_val = st.radio("Chọn Mức cho TC4:", options=opts, index=def_tc4-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc4_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC4'][tc4_val]}")
                    
                    st.markdown("##### 5. TC5: Ảnh hưởng môi trường đến cảm xúc")
                    tc5_val = st.radio("Chọn Mức cho TC5:", options=opts, index=def_tc5-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc5_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC5'][tc5_val]}")
                    
                    st.markdown("##### 6. TC6: Phản ứng khi cảm xúc được công nhận")
                    tc6_val = st.radio("Chọn Mức cho TC6:", options=opts, index=def_tc6-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc6_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC6'][tc6_val]}")

                peq = round((tc1_val + tc2_val + tc3_val + tc4_val + tc5_val + tc6_val) / 6.0, 2)
                group_clean = "DUY TRÌ" if peq >= 3.2 else ("CẦN CẢI THIỆN" if peq >= 2.0 else "HỖ TRỢ ĐẶC BIỆT")
                
                st.markdown("---")
                context_input = st.text_area("Bối cảnh / Minh chứng điển hình:", value=st.session_state.get(f"ctx_{std_eval}", f"Dựa trên theo dõi tháng..."))
                conclusion_input = st.text_area("Kết luận xu hướng phát triển:", value=st.session_state.get(f"cnc_{std_eval}", f"Bé {std_eval} thuộc nhóm {group_clean}..."))
                plan_input = st.text_area("Kế hoạch tác động tiếp theo:", value=st.session_state.get(f"pln_{std_eval}", f"Tiếp tục hỗ trợ bé..."))
                
                col_save_btn, col_exp_btn = st.columns([1.5, 1.5])
                
                with col_save_btn:
                    if st.button("💾 Lưu Bảng Đánh Giá EQ Lên Google Sheets"):
                        e_df = st.session_state.evaluations_df
                        e_t_col = "teacher" if "teacher" in e_df.columns else "Teacher"
                        e_s_col = "student" if "student" in e_df.columns else "Student"
                        e_term_col = "term" if "term" in e_df.columns else "Term"
                        e_y_col = "school_year" if "school_year" in e_df.columns else "School_Year"
                        
                        existing_mask = pd.Series([False] * len(e_df), index=e_df.index)
                        matched_evals = filter_teacher_records(e_df, e_t_col, user_info)
                        if not matched_evals.empty:
                            for idx in matched_evals.index:
                                row_s = e_df.loc[idx, e_s_col]
                                row_term = str(e_df.loc[idx, e_term_col]).strip()
                                row_y = str(e_df.loc[idx, e_y_col]).strip()
                                if is_student_match(row_s, std_eval) and row_term == str(term).strip() and row_y == str(eval_school_year).strip():
                                    existing_mask.loc[idx] = True
                        
                        if existing_mask.any():
                            st.session_state.evaluations_df.loc[existing_mask, "eval_date"] = eval_date_str
                            st.session_state.evaluations_df.loc[existing_mask, "tc1"] = tc1_val
                            st.session_state.evaluations_df.loc[existing_mask, "tc2"] = tc2_val
                            st.session_state.evaluations_df.loc[existing_mask, "tc3"] = tc3_val
                            st.session_state.evaluations_df.loc[existing_mask, "tc4"] = tc4_val
                            st.session_state.evaluations_df.loc[existing_mask, "tc5"] = tc5_val
                            st.session_state.evaluations_df.loc[existing_mask, "tc6"] = tc6_val
                            st.session_state.evaluations_df.loc[existing_mask, "p_eq"] = peq
                            st.session_state.evaluations_df.loc[existing_mask, "group_clean"] = group_clean
                            st.session_state.evaluations_df.loc[existing_mask, "context"] = context_input
                            st.session_state.evaluations_df.loc[existing_mask, "conclusion"] = conclusion_input
                            st.session_state.evaluations_df.loc[existing_mask, "plan"] = plan_input
                        else:
                            new_eval = pd.DataFrame([{
                                "teacher": user_info['name'], "campus": user_info['campus'],
                                "class": user_info.get('class_name', curr_age_group), "student": std_eval,
                                "school_year": eval_school_year, "term": term, "eval_date": eval_date_str,
                                "tc1": tc1_val, "tc2": tc2_val, "tc3": tc3_val, "tc4": tc4_val, "tc5": tc5_val, "tc6": tc6_val,
                                "p_eq": peq, "group_clean": group_clean,
                                "context": context_input, "conclusion": conclusion_input, "plan": plan_input
                            }])
                            st.session_state.evaluations_df = pd.concat([st.session_state.evaluations_df, new_eval], ignore_index=True)

                        if save_sheet_to_gas("Evaluations", st.session_state.evaluations_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn đánh giá EQ cho bé **{std_eval}**!")
                            st.rerun()

                with col_exp_btn:
                    single_eval_df = pd.DataFrame([{
                        "teacher": user_info['name'], "campus": user_info['campus'],
                        "class": user_info.get('class_name', curr_age_group), "student": std_eval,
                        "school_year": eval_school_year, "term": term, "eval_date": eval_date_str,
                        "tc1": tc1_val, "tc2": tc2_val, "tc3": tc3_val, "tc4": tc4_val, "tc5": tc5_val, "tc6": tc6_val,
                        "p_eq": peq, "group_clean": group_clean,
                        "context": context_input, "conclusion": conclusion_input, "plan": plan_input
                    }])
                    single_export = format_evaluations_export(single_eval_df)
                    st.download_button(
                        f"📄 Xuất Phiếu Đánh Giá EQ Riêng Cho Bé {std_eval}",
                        single_export.to_csv(index=False).encode('utf-8-sig'),
                        f"Phieu_Danh_Gia_EQ_{std_eval}_{eval_date_val.strftime('%Y%m%d')}.csv", "text/csv"
                    )

        elif main_menu == "📈 4. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XÁC NHẬN XU HƯỚNG PHÁT TRIỂN EQ")
            
            t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
            s_col = "student_name" if "student_name" in st.session_state.students_df.columns else "Student_Name"
            my_stds_df = filter_teacher_records(st.session_state.students_df, t_col, user_info)
            my_stds = my_stds_df[s_col].dropna().tolist() if not my_stds_df.empty and s_col in my_stds_df.columns else []
            
            if not my_stds: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_cmp_hdr1, col_cmp_hdr2, col_cmp_hdr3 = st.columns([1.5, 1.2, 1.3])
                with col_cmp_hdr1: std_comp = st.selectbox("👦/👧 Chọn học sinh cần so sánh:", my_stds)
                with col_cmp_hdr2: comp_school_year = st.selectbox("Năm học:", SCHOOL_YEAR_OPTIONS, index=1)
                with col_cmp_hdr3:
                    comp_date_val = st.date_input("🗓️ Ngày lập so sánh:", value=datetime.today())
                    comp_date_str = comp_date_val.strftime("%d/%m/%Y")
                    
                comp_type = st.radio("📌 Chọn hình thức so sánh:", ["So sánh 2 Kỳ (Kỳ 1 vs Kỳ 2)", "So sánh giữa 2 Tháng bất kỳ"], horizontal=True)
                col_cmp1, col_cmp2, col_cmp3 = st.columns(3)
                
                if "2 Kỳ" in comp_type:
                    period_1_label, period_2_label = "Kỳ 1 (Tháng 9 - 12)", "Kỳ 2 (Tháng 1 - 5)"
                else:
                    month_list = [f"Tháng {m}" for m in range(1, 13)]
                    with col_cmp1: period_1_label = st.selectbox("Đợt 1:", month_list, index=0)
                    with col_cmp2: period_2_label = st.selectbox("Đợt 2:", month_list, index=1)
                        
                with col_cmp1: score_t1 = st.number_input(f"Điểm {period_1_label}:", min_value=1.0, max_value=4.0, value=2.2, step=0.1)
                with col_cmp2: score_t2 = st.number_input(f"Điểm {period_2_label}:", min_value=1.0, max_value=4.0, value=3.0, step=0.1)
                with col_cmp3:
                    delta_score = round(score_t2 - score_t1, 2)
                    trend_tag = "TIẾN BỘ VƯỢT BẬC" if delta_score >= 0.5 else ("TIẾN BỘ" if delta_score > 0 else ("DUY TRÌ ÔN ĐỊNH" if delta_score == 0 else "CẦN LƯU Ý (THỤT LÙI)"))
                    st.metric("Biến thiên (Delta):", f"{delta_score:+.2f}", delta=trend_tag)
                
                c_input = st.text_area("Kết luận xu hướng:", value=f"Bé {std_comp} có xu hướng {trend_tag.lower()}...")
                p_input = st.text_area("Kế hoạch tác động tiếp theo:", value=f"Tiếp tục đồng hành hỗ trợ bé...")
                
                col_save_cmp, col_exp_cmp = st.columns([1.5, 1.5])
                
                with col_save_cmp:
                    if st.button("💾 Lưu Bảng So Sánh Xu Hướng EQ"):
                        c_df = st.session_state.comparisons_df
                        c_t_col = "teacher" if "teacher" in c_df.columns else "Teacher"
                        c_s_col = "student" if "student" in c_df.columns else "Student"
                        c_type_col = "comp_type" if "comp_type" in c_df.columns else "Comp_Type"
                        c_p1_col = "period_1" if "period_1" in c_df.columns else "Period_1"
                        c_p2_col = "period_2" if "period_2" in c_df.columns else "Period_2"
                        
                        existing_mask = pd.Series([False] * len(c_df), index=c_df.index)
                        matched_comps = filter_teacher_records(c_df, c_t_col, user_info)
                        if not matched_comps.empty:
                            for idx in matched_comps.index:
                                row_s = c_df.loc[idx, c_s_col]
                                row_type = str(c_df.loc[idx, c_type_col]).strip() if c_type_col in c_df.columns else ""
                                row_p1 = str(c_df.loc[idx, c_p1_col]).strip() if c_p1_col in c_df.columns else ""
                                row_p2 = str(c_df.loc[idx, c_p2_col]).strip() if c_p2_col in c_df.columns else ""
                                if is_student_match(row_s, std_comp) and row_type == str(comp_type).strip() and row_p1 == str(period_1_label).strip() and row_p2 == str(period_2_label).strip():
                                    existing_mask.loc[idx] = True
                        
                        if existing_mask.any():
                            st.session_state.comparisons_df.loc[existing_mask, "comp_date"] = comp_date_str
                            st.session_state.comparisons_df.loc[existing_mask, "score_term1"] = score_t1
                            st.session_state.comparisons_df.loc[existing_mask, "score_term2"] = score_t2
                            st.session_state.comparisons_df.loc[existing_mask, "delta"] = delta_score
                            st.session_state.comparisons_df.loc[existing_mask, "trend"] = trend_tag
                            st.session_state.comparisons_df.loc[existing_mask, "conclusion"] = c_input
                            st.session_state.comparisons_df.loc[existing_mask, "plan"] = p_input
                        else:
                            new_comp = pd.DataFrame([{
                                "teacher": user_info['name'], "campus": user_info['campus'],
                                "class": user_info.get('class_name', 'Kindergarten (4-5 tuổi)'), "student": std_comp,
                                "school_year": comp_school_year, "comp_type": comp_type,
                                "period_1": period_1_label, "period_2": period_2_label,
                                "score_term1": score_t1, "score_term2": score_t2,
                                "delta": delta_score, "trend": trend_tag,
                                "conclusion": c_input, "plan": p_input, "comp_date": comp_date_str
                            }])
                            st.session_state.comparisons_df = pd.concat([st.session_state.comparisons_df, new_comp], ignore_index=True)

                        if save_sheet_to_gas("Comparisons", st.session_state.comparisons_df):
                            st.success(f"🎉 Đã lưu Bảng So Sánh Xu Hướng EQ cho bé **{std_comp}**!")
                            st.rerun()

                with col_exp_cmp:
                    single_comp_df = pd.DataFrame([{
                        "teacher": user_info['name'], "campus": user_info['campus'],
                        "class": user_info.get('class_name', 'Kindergarten (4-5 tuổi)'), "student": std_comp,
                        "school_year": comp_school_year, "comp_type": comp_type,
                        "period_1": period_1_label, "period_2": period_2_label,
                        "score_term1": score_t1, "score_term2": score_t2,
                        "delta": delta_score, "trend": trend_tag,
                        "conclusion": c_input, "plan": p_input, "comp_date": comp_date_str
                    }])
                    single_export_cmp = format_comparisons_export(single_comp_df)
                    st.download_button(
                        f"📄 Xuất Bảng So Sánh EQ Riêng Cho Bé {std_comp}",
                        single_export_cmp.to_csv(index=False).encode('utf-8-sig'),
                        f"Bang_So_Sanh_EQ_{std_comp}_{comp_date_val.strftime('%Y%m%d')}.csv", "text/csv"
                    )

        else:
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ VÀ XU HƯỚNG CỦA LỚP")
            
            df_my_eval = filter_teacher_records(st.session_state.evaluations_df, "teacher", user_info)
            if not df_my_eval.empty:
                st.markdown("##### 1. Bảng Đánh Giá EQ 6 Tiêu Chí Của Lớp (Đã Lưu)")
                df_my_eval_export = format_evaluations_export(df_my_eval)
                st.dataframe(df_my_eval_export, use_container_width=True)
                render_eq_charts(df_my_eval, f"LỚP {user_info.get('class_name', '')}")
                st.download_button(
                    "📥 Xuất CSV/Excel Bảng Tổng Hợp EQ Lớp",
                    df_my_eval_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bao_Cao_EQ_Lop_{user_info['name']}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
                )
            else:
                st.markdown("##### ⚡ BÁO CÁO EQ TỰ ĐỘNG TỔNG HỢP TỪ NHẬT KÝ HẰNG NGÀY (DAILY LOGS)")
                df_synth_class = synthesize_daily_logs_report(st.session_state.daily_logs_df, teacher_name=user_info['name'])
                if not df_synth_class.empty:
                    st.dataframe(df_synth_class, use_container_width=True)
                    st.download_button(
                        "📥 Tải CSV/Excel Báo Cáo EQ Tự Động Lớp (.csv)",
                        df_synth_class.to_csv(index=False).encode('utf-8-sig'),
                        f"Bao_Cao_EQ_Tu_Dong_Lop_{user_info['name']}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
                    )
                else:
                    st.info("ℹ️ Lớp chưa có bài đánh giá hay nhật ký ngày nào.")
            
            st.markdown("---")
            st.markdown("##### 2. Bảng Xu Hướng & So Sánh EQ Của Lớp")
            df_my_comp = filter_teacher_records(st.session_state.comparisons_df, "teacher", user_info)
            df_my_comp_export = format_comparisons_export(df_my_comp)
            st.dataframe(df_my_comp_export, use_container_width=True)
            st.table(calculate_class_stats(df_my_comp))
            st.download_button(
                "📥 Xuất CSV/Excel Bảng Xu Hướng EQ Lớp",
                df_my_comp_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bang_Xu_Huong_EQ_Lop_{user_info['name']}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

