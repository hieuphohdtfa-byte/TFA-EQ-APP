import re
import os
import streamlit as st
import pandas as pd
import requests
import os
import json
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
def clean_key(val):
    """ Xóa khoảng trắng, chữ thường, bỏ .0 và chuẩn hóa số 0 ở đầu SĐT/Mã """
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip().lower()
    s = s.replace(".0", "")
    if s in ["nan", "none"]:
        return ""
    if s.startswith("0") and len(s) > 1:
        s = s[1:]
    return s

def filter_df_by_clean_col(df, col_name, target_val):
    """ Lọc DataFrame không lo phân biệt hoa/thường, khoảng trắng, số 0 ở đầu hay đuôi .0 """
    if df is None or df.empty or col_name not in df.columns:
        return pd.DataFrame()
    target_clean = clean_key(target_val)
    mask = df[col_name].apply(clean_key) == target_clean
    return df[mask]

def get_gas_sheet_rows(gas_data, sheet_name):
    """ Tìm và lấy danh sách dòng dữ liệu từ gas_data """
    if not isinstance(gas_data, dict):
        return []
        
    for sub_key in ["data", "result", "sheets", "payload"]:
        if sub_key in gas_data and isinstance(gas_data[sub_key], dict):
            gas_data = gas_data[sub_key]
            break

    clean_target = str(sheet_name).strip().lower().replace(" ", "").replace("_", "")
    
    for k, v in gas_data.items():
        clean_k = str(k).strip().lower().replace(" ", "").replace("_", "")
        if clean_k == clean_target or clean_k == clean_target + "s" or clean_target == clean_k + "s":
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

# Thêm CSS Tối ưu hóa đặc biệt cho Màn hình Điện thoại di động
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
# 2. BỘ TIÊU CHÍ EQ NGUYÊN BẢN CẢ 3 KHỐI LỚP
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
        "TC1": {
            1: "Mức 1: Khóc/giận/vui nhưng không biết vì sao, không có sự kết nối giữa hành động và suy nghĩ.",
            2: "Mức 2: Trẻ chỉ nhận diện được khi cô đặt câu hỏi xác nhận trực tiếp ('Con đang buồn à?').",
            3: "Mức 3: Trẻ tự dùng từ đơn để thông báo trạng thái mà không cần cô hỏi trước ('Con buồn', 'Vui lắm').",
            4: "Mức 4: Tự nhận ra sớm trước khi bộc phát và thể hiện ra bên ngoài để tìm kiếm hỗ trợ."
        },
        "TC2": {
            1: "Mức 1: Trẻ biểu đạt cảm xúc thuần túy qua các phản ứng sinh lý (khóc, cười, la hét).",
            2: "Mức 2: Sử dụng từ vựng cảm xúc đơn lẻ ('Giận', 'Buồn', 'Vui') khi được gợi ý hoặc tự thân.",
            3: "Mức 3: Nói được câu đơn giản để định danh cảm xúc ('Con sợ quá', 'Con buồn').",
            4: "Mức 4: Trẻ diễn đạt + chỉ ra nguyên nhân bằng ngôn ngữ logic sơ khai."
        },
        "TC3": {
            1: "Mức 1: Phản ứng tiêu cực kéo dài > 5 phút và khó bị tác động bởi lời nói của cô.",
            2: "Mức 2: Bình tĩnh lại khi có sự can thiệp trực tiếp (khi cô ôm / trấn an).",
            3: "Mức 3: Nghe theo hướng dẫn, nhắc nhở nhẹ nhàng của cô để tự lấy lại bình tĩnh.",
            4: "Mức 4: Trẻ biết tự tìm các 'góc bình tĩnh' tự an toàn mà không cần cô can thiệp."
        },
        "TC4": {
            1: "Mức 1: Thờ ơ khi thấy bạn khác đang khóc, đau hoặc gặp khó khăn.",
            2: "Mức 2: Tạm dừng hoạt động để quan sát khi bạn có biểu hiện cảm xúc mạnh.",
            3: "Mức 3: Thực hiện các cử chỉ an ủi sơ khai (vuốt lưng, chia sẻ đồ chơi) với bạn.",
            4: "Mức 4: Chủ động kết nối giúp bạn giải tỏa / rủ bạn chơi chung để bạn hết buồn."
        },
        "TC5": {
            1: "Mức 1: Phụ thuộc hoàn toàn vào không khí lớp, dễ bùng nổ khi có thay đổi.",
            2: "Mức 2: Phụ thuộc vào sự an toàn quen thuộc, rụt rè khi môi trường thay đổi.",
            3: "Mức 3: Ổn định trong môi trường quen thuộc, thích nghi có điều kiện.",
            4: "Mức 4: Ít bị ảnh hưởng tiêu cực, duy trì được tâm trạng dù môi trường thay đổi."
        },
        "TC6": {
            1: "Mức 1: Có cơ chế phòng vệ, lảng tránh ánh mắt, tiếp tục khóc khi cô dỗ.",
            2: "Mức 2: Dịu lại 'nghe' cô nói nhưng chưa 'hiểu' hoặc chưa sẵn sàng làm theo.",
            3: "Mức 3: Hợp tác sau khi được công nhận, sẵn sàng thực hiện các yêu cầu đơn giản.",
            4: "Mức 4: Tự giải tỏa được tâm lý, chủ động tìm cô khi cần hỗ trợ."
        }
    },
    "Kindergarten (4-5 tuổi)": {
        "TC1": {
            1: "Mức 1: Nói được cảm xúc nhưng chưa giải thích được lý do ('Con không thích').",
            2: "Mức 2: Xác nhận được lý do khi cô gợi ý câu hỏi nguyên nhân - kết quả.",
            3: "Mức 3: Chủ động sử dụng câu ghép để giải thích trạng thái ('Con buồn vì bạn không chơi cùng').",
            4: "Mức 4: Nhận ra sớm cảm xúc, thông tin đến cô tự điều chỉnh hành vi trước khi bộc phát."
        },
        "TC2": {
            1: "Mức 1: Ổn định, kiểm soát các hành động bản năng (đánh, ném, khóc, hét).",
            2: "Mức 2: Tự gọi tên chính xác cảm xúc bằng câu đơn ngắn rõ ràng từ 2-3 từ.",
            3: "Mức 3: Nhận định được mối quan hệ giữa sự việc và trạng thái tâm lý ('Con buồn vì thua').",
            4: "Mức 4: Biểu đạt cảm xúc kèm mong muốn / giải pháp cụ thể để thay đổi tình huống."
        },
        "TC3": {
            1: "Mức 1: Hành vi bộc phát kéo dài, im lặng hậm hực quay đi.",
            2: "Mức 2: Phối hợp điều chỉnh khi cô hướng dẫn (hít thở, uống nước, rửa mặt).",
            3: "Mức 3: Chủ động tự điều chỉnh và dùng lời nói tự khích lệ ('Cố lên', 'Mình làm được').",
            4: "Mức 4: Chủ động tách khỏi nguồn xung đột, tự khôi phục sự tự tin để tiếp tục hoạt động."
        },
        "TC4": {
            1: "Mức 1: Nhận biết trạng thái vui, buồn, giận của bạn qua nét mặt, cử chỉ.",
            2: "Mức 2: Biểu đạt sự đồng cảm bằng hành động cụ thể (an ủi, vỗ tay, chia sẻ đồ chơi).",
            3: "Mức 3: Chủ động chia sẻ, an ủi bạn tự nhiên và thường xuyên không cần nhắc.",
            4: "Mức 4: Mời gọi, kết nối các bạn cùng chơi, sử dụng lời nói để hòa giải mâu thuẫn nhỏ."
        },
        "TC5": {
            1: "Mức 1: Còn phản ứng bản năng, bộc lộ sự khó chịu, lo lắng khi môi trường đổi.",
            2: "Mức 2: Hiểu liên hệ cảm xúc với ngoại cảnh và chủ động tìm sự chia sẻ từ cô.",
            3: "Mức 3: Biết lựa chọn không gian phù hợp (góc bình tĩnh) để giữ trạng thái ổn định.",
            4: "Mức 4: Chủ động nhắc nhở, giữ trật tự cùng cô để có không gian thoải mái."
        },
        "TC6": {
            1: "Mức 1: Chuyển hóa trạng thái bùng nổ sang lắng nghe khi được cô gọi đúng cảm xúc.",
            2: "Mức 2: Chủ động phối hợp kể lại sự việc, nguyên nhân khi có sự đồng cảm từ cô.",
            3: "Mức 3: Bình tĩnh, chủ động đề xuất giải quyết tình huống khi được công nhận.",
            4: "Mức 4: Hiểu nguyên nhân - kết quả của hành vi và đưa ra lời hứa không lặp lại."
        }
    },
    "Pre-primary (5-6 tuổi)": {
        "TC1": {
            1: "Mức 1: Chỉ nói được cảm xúc chung chung, chưa gọi tên được sắc thái thực tế.",
            2: "Mức 2: Sử dụng cụm từ cảm xúc bậc cao (hồi hộp, xấu hổ, tự hào).",
            3: "Mức 3: Lý giải được nguyên nhân, hiểu mối liên hệ giữa sự kiện và phản ứng.",
            4: "Mức 4: Nhận ra sớm, dự báo cường độ cảm xúc điềm tĩnh không cần nhắc nhở."
        },
        "TC2": {
            1: "Mức 1: Cảm xúc quá mạnh chỉ dùng âm thanh, hành động hoặc im lặng tuyệt đối.",
            2: "Mức 2: Diễn đạt được khi cô đặt câu hỏi lựa chọn với cảm xúc phức tạp.",
            3: "Mức 3: Nói rõ từ vựng sắc thái, tự kết nối logic nhân quả cảm xúc + nguyên nhân.",
            4: "Mức 4: Diễn đạt trọn vẹn cảm xúc bình tĩnh, rõ ràng kèm giải pháp khắc phục."
        },
        "TC3": {
            1: "Mức 1: Thời gian mất kiểm soát kéo dài (> 10 phút), từ chối vỗ về.",
            2: "Mức 2: Lấy lại cân bằng nhờ sự điều hướng của cô (5-7 phút).",
            3: "Mức 3: Tự điều chỉnh đạt 80%, hồi phục nhanh (3-5 phút), có ý thức quay lại nhóm.",
            4: "Mức 4: Tự phục hồi thời gian cực nhanh (< 2 phút), điều chỉnh thái độ phù hợp."
        },
        "TC4": {
            1: "Mức 1: Nhận biết cảm xúc bạn nhưng ưu tiên thỏa mãn nhu cầu cá nhân.",
            2: "Mức 2: Quan sát và thực hiện hành vi xã hội khi có sự nhắc nhở trực tiếp từ cô.",
            3: "Mức 3: Chủ động tương trợ tự phát, dùng kỹ năng thương lượng ('Tớ chơi trước, cậu chơi sau').",
            4: "Mức 4: Khả năng phối hợp nhóm xuất sắc, dẫn dắt hòa giải, tôn trọng sự khác biệt."
        },
        "TC5": {
            1: "Mức 1: Dễ bị kích động hoặc thu mình trước các thay đổi của môi trường.",
            2: "Mức 2: Nhận ra mình khó chịu do môi trường ('Ồn quá') nhưng chờ cô giải quyết.",
            3: "Mức 3: Biết tìm giải pháp thay thế, tự di chuyển ra chỗ yên tĩnh hơn.",
            4: "Mức 4: Giữ tâm thế ổn định, duy trì hiệu suất hoạt động bất chấp ngoại cảnh."
        },
        "TC6": {
            1: "Mức 1: Cần nhiều thời gian (> 15 phút), bị kẹt trong thế giới riêng.",
            2: "Mức 2: Chấp nhận sự đồng cảm nhưng thụ động, cần cô khích lệ thêm.",
            3: "Mức 3: Phản hồi tích cực ngay sau khi được công nhận, xác nhận 'Con đỡ buồn rồi'.",
            4: "Mức 4: Thể hiện sự trưởng thành: biết cảm ơn người lắng nghe, tìm cách giải quyết."
        }
    }
}

# -----------------------------------------------------------------------------
# 🤖 THUẬT TOÁN MA TRẬN TỰ ĐỘNG "NHẶT" MINH CHỨNG VÀO 6 TIÊU CHÍ EQ
# -----------------------------------------------------------------------------
def auto_map_daily_to_criteria(student_name, teacher_name, daily_df):
    if daily_df is None or daily_df.empty:
        return None
    
    t_col = "teacher" if "teacher" in daily_df.columns else "Teacher"
    s_col = "student" if "student" in daily_df.columns else "Student"
    
    std_logs = daily_df[
        (daily_df[s_col].apply(clean_key) == clean_key(student_name)) & 
        (daily_df[t_col].apply(clean_key) == clean_key(teacher_name))
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
        dt_str = str(row.get(date_col, ''))
        
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
        auto_conclusion = f"Bé {student_name} có trí tuệ cảm xúc phát triển rất tích cực (PEQ={auto_peq}), thuộc nhóm DUY TRÌ PHONG ĐỘ. Bé tự chủ cảm xúc tốt và biết hòa nhập với bạn bè."
        auto_plan = f"Kế hoạch: Tiếp tục phát huy năng lực tự chủ, giao vai trò thủ lĩnh nhóm và khuyến khích bé hỗ trợ các bạn khác trong lớp."
    elif auto_group == "CẦN CẢI THIỆN":
        auto_conclusion = f"Bé {student_name} đang trong quá trình phát triển cảm xúc (PEQ={auto_peq}), thuộc nhóm CẦN CẢI THIỆN. Đã có nhận thức nhưng còn bộc phát ở một số tình huống."
        auto_plan = f"Kế hoạch: Hướng dẫn bé thực hành gọi tên cảm xúc, gợi ý sử dụng Góc bình tĩnh khi bé gặp khó khăn hoặc có xáo trộn."
    else:
        auto_conclusion = f"Bé {student_name} gặp nhiều khó khăn trong quản trị cảm xúc (PEQ={auto_peq}), thuộc nhóm HỖ TRỢ ĐẶC BIỆT. Bé dễ bùng nổ và cần sự đồng hành sát sao từ cô."
        auto_plan = f"Kế hoạch: Thiết lập can thiệp 1-1, sử dụng kỹ thuật dỗ dành ôm xoa dịu, phối hợp chặt chẽ với phụ huynh để thống nhất phương pháp tại nhà."

    return {
        "TC1": auto_tc1, "TC2": auto_tc2, "TC3": auto_tc3,
        "TC4": auto_tc4, "TC5": auto_tc5, "TC6": auto_tc6,
        "P_EQ": auto_peq, "Group_Clean": auto_group,
        "Context": auto_context, "Conclusion": auto_conclusion, "Plan": auto_plan
    }

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

def remove_accents(input_str):
    if not input_str: return ''
    s = str(input_str).strip()
    s = re.sub(r'[àáảãạăằắẳẵặâầấẩẫậ]', 'a', s)
    s = re.sub(r'[ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ]', 'A', s)
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
    s = re.sub(r'[đ]', 'd', s)
    s = re.sub(r'[Đ]', 'D', s)
    return s

def clean_key(val):
    if val is None or pd.isna(val): return ''
    s = remove_accents(str(val)).strip().lower().replace('.0', '')
    if s in ['nan', 'none']: return ''
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def clean_dict_key(k):
    s = remove_accents(str(k)).lower()
    return re.sub(r'[^a-z0-9]', '', s)

def get_row_value(row_dict, possible_keys, default=''):
    if not isinstance(row_dict, dict):
        return default
    clean_map = {clean_dict_key(k): v for k, v in row_dict.items()}
    for key in possible_keys:
        ck = clean_dict_key(key)
        if ck in clean_map and clean_map[ck] is not None:
            val = str(clean_map[ck]).strip()
            if val and val.lower() not in ['nan', 'none']:
                return val
    return default

CAMPUS_KEYWORDS = {
    'HD': ['hado', 'ha do', 'catlai', 'cat lai', 'hd'],
    'HL': ['himlam', 'him lam', 'tanhung', 'tan hung', 'hl'],
    'DBM': ['duongbachmai', 'duong bach mai', 'chanhhung', 'chanh hung', 'dbm'],
    'LVS': ['levansy', 'le van sy', 'phunhuan', 'phu nhuan', 'lvs'],
    'TTL': ['tranthily', 'tran thi ly', 'hoacuong', 'hoa cuong', 'ttl']
}

def is_campus_match(c1, c2):
    k1 = clean_key(c1)
    k2 = clean_key(c2)
    if not k1 or not k2 or 'tatca' in k1 or 'tatca' in k2 or k1 == 'all' or k2 == 'all':
        return True
    if k1 == k2 or k1 in k2 or k2 in k1:
        return True
    for code, kw_list in CAMPUS_KEYWORDS.items():
        k_code = clean_key(code)
        if (k1 == k_code or any(clean_key(kw) in k1 for kw in kw_list)) and (k2 == k_code or any(clean_key(kw) in k2 for kw in kw_list)):
            return True
    return False

def is_match(v1, v2):
    k1 = clean_key(v1)
    k2 = clean_key(v2)
    if not k1 or not k2 or 'tatca' in k1 or 'tatca' in k2 or k1 == 'all' or k2 == 'all':
        return True
    return k1 == k2 or k1 in k2 or k2 in k1

def filter_records_multilevel(df, campus_val=None, class_val=None, teacher_val=None, student_val=None):
    if df is None or df.empty:
        return pd.DataFrame()
    res = df.copy()
    if campus_val:
        c_col = 'campus' if 'campus' in res.columns else ('Campus' if 'Campus' in res.columns else '')
        if c_col: res = res[res[c_col].apply(lambda x: is_campus_match(x, campus_val))]
    if class_val:
        cl_col = 'class' if 'class' in res.columns else ('class_name' if 'class_name' in res.columns else '')
        if cl_col: res = res[res[cl_col].apply(lambda x: is_match(x, class_val))]
    if teacher_val:
        t_col = 'teacher' if 'teacher' in res.columns else ('name' if 'name' in res.columns else '')
        if t_col: res = res[res[t_col].apply(lambda x: is_match(x, teacher_val))]
    if student_val:
        s_col = 'student' if 'student' in res.columns else ('student_name' if 'student_name' in res.columns else '')
        if s_col: res = res[res[s_col].apply(lambda x: is_match(x, student_val))]
    return res

def normalize_users_df(raw_rows, default_users_df):
    if not raw_rows:
        return default_users_df
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        std_row = {}
        std_row["username"] = get_row_value(r, ["username", "user", "tk", "tendangnhap", "taikhoan", "sdt"])
        std_row["password"] = get_row_value(r, ["password", "pass", "matkhau"])
        std_row["name"] = get_row_value(r, ["name", "hoten", "tengiaovien", "ten", "hovaten"])
        std_row["role"] = get_row_value(r, ["role", "vaitro", "chucvu"])
        std_row["campus_code"] = get_row_value(r, ["campuscode", "macoso", "code"])
        std_row["campus"] = get_row_value(r, ["campus", "coso", "tencoso"])
        std_row["class_name"] = get_row_value(r, ["classname", "class", "lop", "khoilop"])
        std_row["status"] = get_row_value(r, ["status", "trangthai"], default="active")
        if std_row["username"]:
            norm_rows.append(std_row)
    df = pd.DataFrame(norm_rows) if norm_rows else pd.DataFrame()
    for c in ["username", "password", "name", "role", "campus_code", "campus", "class_name", "status"]:
        if c not in df.columns: df[c] = ""
    all_df = pd.concat([default_users_df, df], ignore_index=True)
    all_df["_u_clean"] = all_df["username"].apply(clean_key)
    all_df = all_df[all_df["_u_clean"] != ""].drop_duplicates(subset=["_u_clean"], keep="last").drop(columns=["_u_clean"])
    return all_df

def normalize_students_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher_user", "teacher_name", "campus_code", "campus", "class_name", "student_name", "birth_date", "gender", "notes"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        std_row = {}
        std_row["teacher_user"] = clean_key(get_row_value(r, ["teacheruser", "teacher", "giaovien"]))
        std_row["teacher_name"] = get_row_value(r, ["teachername", "teacher", "giaovien", "tengiaovien"])
        std_row["campus_code"] = get_row_value(r, ["campuscode", "macoso", "code"])
        std_row["campus"] = get_row_value(r, ["campus", "coso", "tencoso"])
        std_row["class_name"] = get_row_value(r, ["classname", "class", "lop", "khoilop"])
        std_row["student_name"] = get_row_value(r, ["studentname", "student", "tenhocsinh", "hocsinh", "tenbe"])
        std_row["birth_date"] = get_row_value(r, ["birthdate", "ngaysinh", "dobi"])
        std_row["gender"] = get_row_value(r, ["gender", "gioitinh"])
        std_row["notes"] = get_row_value(r, ["notes", "ghichu", "luuy"])
        if std_row["student_name"]:
            norm_rows.append(std_row)
    return pd.DataFrame(norm_rows)

def normalize_evaluations_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher", "campus", "class", "student", "school_year", "term", "eval_date", "tc1", "tc2", "tc3", "tc4", "tc5", "tc6", "p_eq", "group_clean", "context", "conclusion", "plan"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        std_row = {}
        std_row["teacher"] = get_row_value(r, ["teacher", "giaovien", "tengiaovien"])
        std_row["campus"] = get_row_value(r, ["campus", "coso", "tencoso"])
        std_row["class"] = get_row_value(r, ["class", "lop", "khoilop", "tenlop"])
        std_row["student"] = get_row_value(r, ["student", "tenhocsinh", "hocsinh", "tenbe", "hotenhocsinh"])
        std_row["school_year"] = get_row_value(r, ["schoolyear", "namhoc"])
        std_row["term"] = get_row_value(r, ["term", "ky", "kythang", "thang"])
        std_row["eval_date"] = get_row_value(r, ["evaldate", "ngay", "ngaydanhgia"])
        for tc in ["tc1", "tc2", "tc3", "tc4", "tc5", "tc6"]:
            std_row[tc] = get_row_value(r, [tc], default="0")
        std_row["p_eq"] = get_row_value(r, ["p_eq", "peq", "peqscore", "diemtbpeq", "diemtb"], default="0")
        std_row["group_clean"] = get_row_value(r, ["groupclean", "nhom", "nhomtrangthai"])
        std_row["context"] = get_row_value(r, ["context", "boicanhminhchungdienhinhhanhvicuthe", "boicanh", "minhchung"])
        std_row["conclusion"] = get_row_value(r, ["conclusion", "ketluan", "ketluanxuhuong"])
        std_row["plan"] = get_row_value(r, ["plan", "kehoach", "kehoachtacdongtieptheo"])
        norm_rows.append(std_row)
    return pd.DataFrame(norm_rows)

def normalize_dailylogs_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher", "campus", "class", "student", "log_date", "routine", "emotion", "trigger", "action", "teacher_support", "result"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        std_row = {}
        std_row["teacher"] = get_row_value(r, ["teacher", "giaovien", "tengiaovien"])
        std_row["campus"] = get_row_value(r, ["campus", "coso", "tencoso"])
        std_row["class"] = get_row_value(r, ["class", "lop", "khoilop", "tenlop"])
        std_row["student"] = get_row_value(r, ["student", "tenhocsinh", "hocsinh", "tenbe"])
        std_row["log_date"] = get_row_value(r, ["logdate", "ngay", "ngaynhatky"])
        std_row["routine"] = get_row_value(r, ["routine", "hoatdong", "khunghoatdong"])
        std_row["emotion"] = get_row_value(r, ["emotion", "camxuc"])
        std_row["trigger"] = get_row_value(r, ["trigger", "nguyennhan", "yautobocphat"])
        std_row["action"] = get_row_value(r, ["action", "hanhvi", "bieuhien"])
        std_row["teacher_support"] = get_row_value(r, ["teachersupport", "xuly", "cohotro"])
        std_row["result"] = get_row_value(r, ["result", "ketqua"])
        norm_rows.append(std_row)
    return pd.DataFrame(norm_rows)

def normalize_comparisons_df(raw_rows):
    if not raw_rows:
        return pd.DataFrame(columns=["teacher", "campus", "class", "student", "school_year", "comp_type", "period_1", "period_2", "score_term1", "score_term2", "delta", "trend", "conclusion", "plan", "comp_date"])
    norm_rows = []
    for r in raw_rows:
        if not isinstance(r, dict): continue
        std_row = {
            "teacher": get_row_value(r, ["teacher", "giaovien", "tengiaovien"]),
            "campus": get_row_value(r, ["campus", "coso", "tencoso"]),
            "class": get_row_value(r, ["class", "lop", "khoilop", "tenlop"]),
            "student": get_row_value(r, ["student", "tenhocsinh", "hocsinh", "tenbe", "hotenhocsinh"]),
            "school_year": get_row_value(r, ["schoolyear", "namhoc"]),
            "comp_type": get_row_value(r, ["comptype", "loaisosanh"]),
            "period_1": get_row_value(r, ["period1", "dot1"]),
            "period_2": get_row_value(r, ["period2", "dot2"]),
            "score_term1": get_row_value(r, ["scoreterm1", "diemdot1"], default="0"),
            "score_term2": get_row_value(r, ["scoreterm2", "diemdot2"], default="0"),
            "delta": get_row_value(r, ["delta", "bienthien"], default="0"),
            "trend": get_row_value(r, ["trend", "xuhuong", "xuhuongeq"]),
            "conclusion": get_row_value(r, ["conclusion", "ketluan", "ketluanxuhuong"]),
            "plan": get_row_value(r, ["plan", "kehoach", "kehoachtacdongtieptheo"]),
            "comp_date": get_row_value(r, ["compdate", "ngay", "ngaysosanh"])
        }
        norm_rows.append(std_row)
    return pd.DataFrame(norm_rows)

def load_all_from_gas():
    try:
        res = requests.get(f"{GAS_URL}?action=read_all", allow_redirects=True, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict):
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
            st.session_state.users_df = normalize_users_df(get_gas_sheet_rows(gas_data, "Users"), DEFAULT_USERS_DF)
            st.session_state.students_df = normalize_students_df(get_gas_sheet_rows(gas_data, "Students"))
            st.session_state.evaluations_df = normalize_evaluations_df(get_gas_sheet_rows(gas_data, "Evaluations"))
            st.session_state.daily_logs_df = normalize_dailylogs_df(get_gas_sheet_rows(gas_data, "DailyLogs"))
            st.session_state.comparisons_df = normalize_comparisons_df(get_gas_sheet_rows(gas_data, "Comparisons"))
            st.session_state.gas_loaded = True

init_app_data()

if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

if st.session_state.logged_user is None and hasattr(st, "query_params"):
    saved_user = st.query_params.get("user", None)
    if saved_user:
        st.session_state.logged_user = clean_key(saved_user)

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
        if clean_key(u_key) == clean_u:
            if u_info["password"] == clean_p:
                return True, u_key, u_info, "OK"
            else:
                return False, None, None, "WRONG_PASSWORD"
    return False, None, None, "NOT_FOUND"

# -----------------------------------------------------------------------------
# 4. HÀM CHUẨN HÓA BẢNG XUẤT FILE EXCEL/CSV
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
    export_df["Điểm đợt 1"] = pd.to_numeric(get_series("score_term1"), errors='coerce').fillna(0.0)
    export_df["Đợt 2"] = get_series("period_2")
    export_df["Điểm đợt 2"] = pd.to_numeric(get_series("score_term2"), errors='coerce').fillna(0.0)
    export_df["Biến thiên"] = pd.to_numeric(get_series("delta"), errors='coerce').fillna(0.0)
    export_df["Xu hướng EQ"] = get_series("trend")
    export_df["Kết luận xu hướng"] = get_series("conclusion")
    export_df["Kế hoạch tác động tiếp theo"] = get_series("plan")
    
    return export_df

def calculate_class_stats(df_comp):
    if df_comp is None or df_comp.empty:
        return pd.DataFrame([
            {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm DUY TRÌ (PEQ >= 3.2)", "Đợt 1": "0.00%", "Đợt 2": "0.00%", "Thay đổi (%)": "+0.00%"},
            {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm CẦN CẢI THIỆN (2.0 <= PEQ < 3.2)", "Đợt 1": "0.00%", "Đợt 2": "0.00%", "Thay đổi (%)": "+0.00%"},
            {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm HỖ TRỢ ĐẶC BIỆT (PEQ < 2.0)", "Đợt 1": "0.00%", "Đợt 2": "0.00%", "Thay đổi (%)": "+0.00%"}
        ])
    
    total_stds = len(df_comp)
    col_s1 = "score_term1" if "score_term1" in df_comp.columns else "Score_Term1"
    col_s2 = "score_term2" if "score_term2" in df_comp.columns else "Score_Term2"
    
    s1 = pd.to_numeric(df_comp[col_s1], errors='coerce').fillna(0) if col_s1 in df_comp.columns else pd.Series([0.0] * total_stds)
    s2 = pd.to_numeric(df_comp[col_s2], errors='coerce').fillna(0) if col_s2 in df_comp.columns else pd.Series([0.0] * total_stds)
    
    duy_tri_1 = (s1 >= 3.2).sum() / total_stds * 100
    duy_tri_2 = (s2 >= 3.2).sum() / total_stds * 100
    
    cai_thien_1 = ((s1 >= 2.0) & (s1 < 3.2)).sum() / total_stds * 100
    cai_thien_2 = ((s2 >= 2.0) & (s2 < 3.2)).sum() / total_stds * 100
    
    ho_tro_1 = (s1 < 2.0).sum() / total_stds * 100
    ho_tro_2 = (s2 < 2.0).sum() / total_stds * 100
    
    return pd.DataFrame([
        {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm DUY TRÌ (PEQ >= 3.2)", "Đợt 1": f"{duy_tri_1:.2f}%", "Đợt 2": f"{duy_tri_2:.2f}%", "Thay đổi (%)": f"{duy_tri_2 - duy_tri_1:+.2f}%"},
        {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm CẦN CẢI THIỆN (2.0 <= PEQ < 3.2)", "Đợt 1": f"{cai_thien_1:.2f}%", "Đợt 2": f"{cai_thien_2:.2f}%", "Thay đổi (%)": f"{cai_thien_2 - cai_thien_1:+.2f}%"},
        {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm HỖ TRỢ ĐẶC BIỆT (PEQ < 2.0)", "Đợt 1": f"{ho_tro_1:.2f}%", "Đợt 2": f"{ho_tro_2:.2f}%", "Thay đổi (%)": f"{ho_tro_2 - ho_tro_1:+.2f}%"}
    ])

# -----------------------------------------------------------------------------
# 5. HÀM HỖ TRỢ VẼ BIỂU ĐỒ
# -----------------------------------------------------------------------------
def render_eq_charts(eval_df, title_prefix=""):
    if eval_df is None or eval_df.empty:
        st.info("Chưa có đủ dữ liệu để vẽ biểu đồ trực quan.")
        return
    
    st.markdown(f"#### 📊 BIỂU ĐỒ TRỰC QUAN PHÂN TÍCH CẢM XÚC EQ {title_prefix.upper()}")
    col_chart1, col_chart2 = st.columns(2)
    
    grp_col = "group_clean" if "group_clean" in eval_df.columns else "Group_Clean"
    counts = eval_df[grp_col].value_counts().reset_index() if grp_col in eval_df.columns else pd.DataFrame()
    if not counts.empty:
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
        
    tc_keys = ["tc1", "tc2", "tc3", "tc4", "tc5", "tc6"]
    tc_names = ["TC1: Nhận biết", "TC2: Bày tỏ", "TC3: Kiềm chế", "TC4: Đồng cảm", "TC5: Thích ứng", "TC6: Lắng nghe"]
    avg_scores = []
    for k in tc_keys:
        col_name = k if k in eval_df.columns else k.upper()
        if col_name in eval_df.columns:
            avg_scores.append(round(pd.to_numeric(eval_df[col_name], errors='coerce').mean(), 2))
        else:
            avg_scores.append(0)
    
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
# 7. GIAO DIỆN BÌA NGOÀI & ĐĂNG NHẬP
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
                success, u_key, u_info, err_code = authenticate_user(login_user, login_pass, users_dict)
                if success:
                    if u_info.get("status", "active") == "inactive":
                        st.error("❌ Tài khoản này đã bị NGƯNG HIỆU LỰC hoạt động!")
                    else:
                        st.session_state.logged_user = u_key
                        if hasattr(st, "query_params"):
                            st.query_params["user"] = u_key
                        st.success(f"🎉 Đăng nhập thành công! Chào mừng {u_info['name']}")
                        st.rerun()
                elif err_code == "WRONG_PASSWORD":
                    st.error("❌ Mật khẩu không chính xác!")
                else:
                    st.error(f"❌ Tên đăng nhập `{login_user}` không tồn tại trên hệ thống!")

        st.markdown("---")
        if st.button("🔄 Nạp Tải Lại Dữ Liệu Từ Google Sheet"):
            init_app_data(force_reload=True)
            st.success("🎉 Đã tải lại dữ liệu mới nhất từ Google Trang tính!")
            st.rerun()

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
    user_info = users_dict.get(st.session_state.logged_user, {
        "name": "Người dùng", "role": "teacher", "campus": "TFA", "class_name": "Lớp"
    })
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
            df_eval_raw = st.session_state.evaluations_df
            
            st.markdown("##### 🔍 BỘ LỌC DỮ LIỆU ĐA CẤP (TỰ ĐỘNG LIÊN THÔNG)")
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                sel_campus_sa = st.selectbox("🏫 1. Chọn Cơ sở:", ["Tất cả cơ sở"] + [f"{code} - {name}" for code, name in CAMPUS_MAP.items()], key="sa_eval_campus")
                campus_filter_val = sel_campus_sa.split(" - ")[0] if " - " in sel_campus_sa else sel_campus_sa
            with col_f2:
                sel_class_sa = st.selectbox("🏫 2. Chọn Khối Lớp:", ["Tất cả các lớp"] + TFA_CLASSES, key="sa_eval_class")
            
            df_step1 = filter_records_multilevel(df_eval_raw, campus_val=campus_filter_val, class_val=sel_class_sa)
            users_sa = filter_records_multilevel(st.session_state.users_df, campus_val=campus_filter_val, class_val=sel_class_sa)
            teachers_from_users = users_sa[users_sa["role"].apply(clean_key) == "teacher"]["name"].tolist() if not users_sa.empty else []
            teachers_from_evals = df_step1["teacher"].unique().tolist() if not df_step1.empty else []
            avail_teachers_sa = sorted(list(set([t for t in teachers_from_users + teachers_from_evals if t and clean_key(t) not in ["nan", "none"]])))
            
            with col_f3:
                sel_teacher_sa = st.selectbox("👩‍🏫 3. Chọn Giáo viên:", ["Tất cả giáo viên"] + avail_teachers_sa, key="sa_eval_teacher")
            
            df_step2 = filter_records_multilevel(df_step1, teacher_val=sel_teacher_sa)
            stds_sa = filter_records_multilevel(st.session_state.students_df, campus_val=campus_filter_val, class_val=sel_class_sa, teacher_val=sel_teacher_sa)
            students_from_stddf = stds_sa["student_name"].tolist() if not stds_sa.empty else []
            students_from_evals = df_step2["student"].unique().tolist() if not df_step2.empty else []
            avail_students_sa = sorted(list(set([s for s in students_from_stddf + students_from_evals if s and clean_key(s) not in ["nan", "none"]])))
            
            with col_f4:
                sel_student_sa = st.selectbox("👧 4. Chọn Học sinh:", ["Tất cả học sinh"] + avail_students_sa, key="sa_eval_student")
            
            df_eval_filtered = filter_records_multilevel(df_eval_raw, campus_val=campus_filter_val, class_val=sel_class_sa, teacher_val=sel_teacher_sa, student_val=sel_student_sa)
            df_export = format_evaluations_export(df_eval_filtered)
            
            st.dataframe(df_export, use_container_width=True)
            if not df_eval_filtered.empty:
                render_eq_charts(df_eval_filtered, "(Toàn Trường)")
            else:
                st.info("ℹ️ Chưa ghi nhận đánh giá EQ nào theo bộ lọc đã chọn. Bạn vẫn có thể tải Khung Báo Cáo Mẫu (.csv) bên dưới.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Tổng Hợp EQ Chuẩn Mẫu",
                df_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bao_Cao_Tong_Hop_EQ_TFA_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

        elif main_menu == "📈 3. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XU HƯỚNG PHÁT TRIỂN EQ TOÀN TRƯỜNG")
            df_comp_raw = st.session_state.comparisons_df
            
            st.markdown("##### 🔍 BỘ LỌC DỮ LIỆU ĐA CẤP (TỰ ĐỘNG LIÊN THÔNG)")
            col_fc1, col_fc2, col_fc3, col_fc4 = st.columns(4)
            with col_fc1:
                sel_campus_sac = st.selectbox("🏫 1. Chọn Cơ sở:", ["Tất cả cơ sở"] + [f"{code} - {name}" for code, name in CAMPUS_MAP.items()], key="sac_comp_campus")
                campus_filter_valc = sel_campus_sac.split(" - ")[0] if " - " in sel_campus_sac else sel_campus_sac
            with col_fc2:
                sel_class_sac = st.selectbox("🏫 2. Chọn Khối Lớp:", ["Tất cả các lớp"] + TFA_CLASSES, key="sac_comp_class")
            
            df_c_step1 = filter_records_multilevel(df_comp_raw, campus_val=campus_filter_valc, class_val=sel_class_sac)
            users_sac = filter_records_multilevel(st.session_state.users_df, campus_val=campus_filter_valc, class_val=sel_class_sac)
            teachers_from_usersc = users_sac[users_sac["role"].apply(clean_key) == "teacher"]["name"].tolist() if not users_sac.empty else []
            teachers_from_comps = df_c_step1["teacher"].unique().tolist() if not df_c_step1.empty else []
            avail_teachers_sac = sorted(list(set([t for t in teachers_from_usersc + teachers_from_comps if t and clean_key(t) not in ["nan", "none"]])))
            
            with col_fc3:
                sel_teacher_sac = st.selectbox("👩‍🏫 3. Chọn Giáo viên:", ["Tất cả giáo viên"] + avail_teachers_sac, key="sac_comp_teacher")
            
            df_c_step2 = filter_records_multilevel(df_c_step1, teacher_val=sel_teacher_sac)
            stds_sac = filter_records_multilevel(st.session_state.students_df, campus_val=campus_filter_valc, class_val=sel_class_sac, teacher_val=sel_teacher_sac)
            students_from_stddfc = stds_sac["student_name"].tolist() if not stds_sac.empty else []
            students_from_comps = df_c_step2["student"].unique().tolist() if not df_c_step2.empty else []
            avail_students_sac = sorted(list(set([s for s in students_from_stddfc + students_from_comps if s and clean_key(s) not in ["nan", "none"]])))
            
            with col_fc4:
                sel_student_sac = st.selectbox("👧 4. Chọn Học sinh:", ["Tất cả học sinh"] + avail_students_sac, key="sac_comp_student")
            
            df_comp_filtered = filter_records_multilevel(df_comp_raw, campus_val=campus_filter_valc, class_val=sel_class_sac, teacher_val=sel_teacher_sac, student_val=sel_student_sac)
            df_comp_export = format_comparisons_export(df_comp_filtered)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Toàn Trường")
            st.table(calculate_class_stats(df_comp_filtered))
            
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
            df_eval_raw = st.session_state.evaluations_df
            df_c_raw = filter_records_multilevel(df_eval_raw, campus_val=my_campus)
            
            st.markdown("##### 🔍 BỘ LỌC DỮ LIỆU CƠ SỞ (TỰ ĐỘNG LIÊN THÔNG)")
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                sel_class_bgh = st.selectbox("🏫 1. Chọn Khối Lớp:", ["Tất cả các lớp"] + TFA_CLASSES, key="bgh_eval_class")
            
            df_bgh_step1 = filter_records_multilevel(df_c_raw, campus_val=my_campus, class_val=sel_class_bgh)
            users_bgh = filter_records_multilevel(st.session_state.users_df, campus_val=my_campus, class_val=sel_class_bgh)
            teachers_from_users = users_bgh[users_bgh["role"].apply(clean_key) == "teacher"]["name"].tolist() if not users_bgh.empty else []
            teachers_from_evals = df_bgh_step1["teacher"].unique().tolist() if not df_bgh_step1.empty else []
            avail_teachers_bgh = sorted(list(set([t for t in teachers_from_users + teachers_from_evals if t and clean_key(t) not in ["nan", "none"]])))
            
            with col_b2:
                sel_teacher_bgh = st.selectbox("👩‍🏫 2. Chọn Giáo viên:", ["Tất cả giáo viên"] + avail_teachers_bgh, key="bgh_eval_teacher")
            
            df_bgh_step2 = filter_records_multilevel(df_bgh_step1, teacher_val=sel_teacher_bgh)
            stds_bgh = filter_records_multilevel(st.session_state.students_df, campus_val=my_campus, class_val=sel_class_bgh, teacher_val=sel_teacher_bgh)
            students_from_stddf = stds_bgh["student_name"].tolist() if not stds_bgh.empty else []
            students_from_evals = df_bgh_step2["student"].unique().tolist() if not df_bgh_step2.empty else []
            avail_students_bgh = sorted(list(set([s for s in students_from_stddf + students_from_evals if s and clean_key(s) not in ["nan", "none"]])))
            
            with col_b3:
                sel_student_bgh = st.selectbox("👧 3. Chọn Học sinh:", ["Tất cả học sinh"] + avail_students_bgh, key="bgh_eval_student")
            
            df_c_filtered = filter_records_multilevel(df_c_raw, campus_val=my_campus, class_val=sel_class_bgh, teacher_val=sel_teacher_bgh, student_val=sel_student_bgh)
            df_export = format_evaluations_export(df_c_filtered)
            
            st.dataframe(df_export, use_container_width=True)
            if not df_c_filtered.empty:
                render_eq_charts(df_c_filtered, f"({my_campus})")
            else:
                st.info("ℹ️ Cơ sở chưa có dữ liệu đánh giá EQ phù hợp với bộ lọc đã chọn.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Báo Cáo EQ Cơ Sở",
                df_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bao_Cao_EQ_{my_code}_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv"
            )

        else:
            st.subheader(f"📈 BẢNG SO SÁNH XU HƯỚNG EQ CƠ SỞ: {my_campus.upper()}")
            df_comp_raw = st.session_state.comparisons_df
            df_comp_c_raw = filter_records_multilevel(df_comp_raw, campus_val=my_campus)
            
            st.markdown("##### 🔍 BỘ LỌC DỮ LIỆU CƠ SỞ (TỰ ĐỘNG LIÊN THÔNG)")
            col_bc1, col_bc2, col_bc3 = st.columns(3)
            with col_bc1:
                sel_class_bghc = st.selectbox("🏫 1. Chọn Khối Lớp:", ["Tất cả các lớp"] + TFA_CLASSES, key="bghc_comp_class")
            
            df_bghc_step1 = filter_records_multilevel(df_comp_c_raw, campus_val=my_campus, class_val=sel_class_bghc)
            users_bghc = filter_records_multilevel(st.session_state.users_df, campus_val=my_campus, class_val=sel_class_bghc)
            teachers_from_usersc = users_bghc[users_bghc["role"].apply(clean_key) == "teacher"]["name"].tolist() if not users_bghc.empty else []
            teachers_from_compsc = df_bghc_step1["teacher"].unique().tolist() if not df_bghc_step1.empty else []
            avail_teachers_bghc = sorted(list(set([t for t in teachers_from_usersc + teachers_from_compsc if t and clean_key(t) not in ["nan", "none"]])))
            
            with col_bc2:
                sel_teacher_bghc = st.selectbox("👩‍🏫 2. Chọn Giáo viên:", ["Tất cả giáo viên"] + avail_teachers_bghc, key="bghc_comp_teacher")
            
            df_bghc_step2 = filter_records_multilevel(df_bghc_step1, teacher_val=sel_teacher_bghc)
            stds_bghc = filter_records_multilevel(st.session_state.students_df, campus_val=my_campus, class_val=sel_class_bghc, teacher_val=sel_teacher_bghc)
            students_from_stddfc = stds_bghc["student_name"].tolist() if not stds_bghc.empty else []
            students_from_compsc = df_bghc_step2["student"].unique().tolist() if not df_bghc_step2.empty else []
            avail_students_bghc = sorted(list(set([s for s in students_from_stddfc + students_from_compsc if s and clean_key(s) not in ["nan", "none"]])))
            
            with col_bc3:
                sel_student_bghc = st.selectbox("👧 3. Chọn Học sinh:", ["Tất cả học sinh"] + avail_students_bghc, key="bghc_comp_student")
            
            df_comp_c_filtered = filter_records_multilevel(df_comp_c_raw, campus_val=my_campus, class_val=sel_class_bghc, teacher_val=sel_teacher_bghc, student_val=sel_student_bghc)
            df_comp_export = format_comparisons_export(df_comp_c_filtered)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Cơ Sở")
            st.table(calculate_class_stats(df_comp_c_filtered))
            
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
            my_stds_df = filter_df_by_clean_col(st.session_state.students_df, t_col, user_key)
            
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
            
            my_stds_df = filter_df_by_clean_col(st.session_state.students_df, t_col, user_key)
            my_stds = my_stds_df[s_col].tolist() if not my_stds_df.empty and s_col in my_stds_df.columns else []
            
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
                        if n_col in std_match.columns:
                            val_note = std_match.iloc[0][n_col]
                            std_note_info = str(val_note).strip() if pd.notna(val_note) else ""
                        else:
                            std_note_info = ""
                        if std_note_info.lower() in ["nan", "none"]:
                            std_note_info = ""
                        
                        if std_note_info:
                            st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**\n\n📌 **Lưu ý:** {std_note_info}")
                        else:
                            st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**")
                    else:
                        st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**")
                
                selected_date_str = log_date.strftime("%d/%m/%Y")
                
                d_df = st.session_state.daily_logs_df
                existing_log = None
                
                if not d_df.empty:
                    d_t_col = "teacher" if "teacher" in d_df.columns else "Teacher"
                    d_s_col = "student" if "student" in d_df.columns else "Student"
                    d_d_col = "date" if "date" in d_df.columns else "Date"
                    
                    match_log_mask = (
                        (d_df[d_t_col].apply(clean_key) == clean_key(user_info['name'])) &
                        (d_df[d_s_col].apply(clean_key) == clean_key(std_select)) &
                        (d_df[d_d_col].astype(str).str.strip() == selected_date_str)
                    )
                    
                    if match_log_mask.any():
                        existing_log = d_df[match_log_mask].iloc[-1]
                
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
                        
                        existing_mask = (
                            (d_df[d_t_col].apply(clean_key) == clean_key(user_info['name'])) &
                            (d_df[d_s_col].apply(clean_key) == clean_key(std_select)) &
                            (d_df[d_d_col].astype(str).str.strip() == selected_date_str)
                        )
                        
                        if existing_mask.any():
                            st.session_state.daily_logs_df.loc[existing_mask, "emotions"] = full_emotions_str
                            st.session_state.daily_logs_df.loc[existing_mask, "note"] = note_context
                            st.session_state.daily_logs_df.loc[existing_mask, "intervention"] = note_intervention
                            st.session_state.daily_logs_df.loc[existing_mask, "summary"] = f"[{final_trend_str}] {daily_summary}"
                            st.session_state.daily_logs_df.loc[existing_mask, "details_json"] = json_str
                        else:
                            new_log = pd.DataFrame([{
                                "teacher": user_info['name'], "campus": user_info['campus'],
                                "class": user_info.get('class_name', 'Pre-school (3-4 tuổi)'),
                                "student": std_select, "date": selected_date_str,
                                "routine": "Toàn bộ hoạt động trong ngày", "emotions": full_emotions_str,
                                "note": note_context, "intervention": note_intervention,
                                "summary": f"[{final_trend_str}] {daily_summary}", "details_json": json_str
                            }])
                            st.session_state.daily_logs_df = pd.concat([st.session_state.daily_logs_df, new_log], ignore_index=True)
                        
                        st.session_state.daily_logs_df["_t"] = st.session_state.daily_logs_df[d_t_col].apply(clean_key)
                        st.session_state.daily_logs_df["_s"] = st.session_state.daily_logs_df[d_s_col].apply(clean_key)
                        st.session_state.daily_logs_df["_d"] = st.session_state.daily_logs_df[d_d_col].astype(str).str.strip()
                        st.session_state.daily_logs_df = st.session_state.daily_logs_df.drop_duplicates(subset=["_t", "_s", "_d"], keep="last").drop(columns=["_t", "_s", "_d"])

                        if save_sheet_to_gas("DailyLogs", st.session_state.daily_logs_df):
                            st.success(f"🎉 Đã lưu vĩnh viễn Hồ sơ cảm xúc ngày {selected_date_str} cho bé **{std_select}**!")
                            st.rerun()

        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ")
            
            t_col = "teacher_user" if "teacher_user" in st.session_state.students_df.columns else "Teacher_User"
            s_col = "student_name" if "student_name" in st.session_state.students_df.columns else "Student_Name"
            my_stds_df = filter_df_by_clean_col(st.session_state.students_df, t_col, user_key)
            my_stds = my_stds_df[s_col].tolist() if not my_stds_df.empty and s_col in my_stds_df.columns else []
            
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
                        
                        existing_mask = (
                            (e_df[e_t_col].apply(clean_key) == clean_key(user_info['name'])) &
                            (e_df[e_s_col].apply(clean_key) == clean_key(std_eval)) &
                            (e_df[e_term_col].astype(str).str.strip() == str(term).strip()) &
                            (e_df[e_y_col].astype(str).str.strip() == str(eval_school_year).strip())
                        )
                        
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
                            
                        st.session_state.evaluations_df["_t"] = st.session_state.evaluations_df[e_t_col].apply(clean_key)
                        st.session_state.evaluations_df["_s"] = st.session_state.evaluations_df[e_s_col].apply(clean_key)
                        st.session_state.evaluations_df["_term"] = st.session_state.evaluations_df[e_term_col].astype(str).str.strip()
                        st.session_state.evaluations_df["_y"] = st.session_state.evaluations_df[e_y_col].astype(str).str.strip()
                        st.session_state.evaluations_df = st.session_state.evaluations_df.drop_duplicates(subset=["_t", "_s", "_term", "_y"], keep="last").drop(columns=["_t", "_s", "_term", "_y"])

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
            my_stds_df = filter_df_by_clean_col(st.session_state.students_df, t_col, user_key)
            my_stds = my_stds_df[s_col].tolist() if not my_stds_df.empty and s_col in my_stds_df.columns else []
            
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
                        
                        existing_mask = (
                            (c_df[c_t_col].apply(clean_key) == clean_key(user_info['name'])) &
                            (c_df[c_s_col].apply(clean_key) == clean_key(std_comp)) &
                            (c_df[c_type_col].astype(str).str.strip() == str(comp_type).strip()) &
                            (c_df[c_p1_col].astype(str).str.strip() == str(period_1_label).strip()) &
                            (c_df[c_p2_col].astype(str).str.strip() == str(period_2_label).strip())
                        )
                        
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
                            
                        st.session_state.comparisons_df["_t"] = st.session_state.comparisons_df[c_t_col].apply(clean_key)
                        st.session_state.comparisons_df["_s"] = st.session_state.comparisons_df[c_s_col].apply(clean_key)
                        st.session_state.comparisons_df["_p1"] = st.session_state.comparisons_df[c_p1_col].astype(str).str.strip()
                        st.session_state.comparisons_df["_p2"] = st.session_state.comparisons_df[c_p2_col].astype(str).str.strip()
                        st.session_state.comparisons_df = st.session_state.comparisons_df.drop_duplicates(subset=["_t", "_s", "_p1", "_p2"], keep="last").drop(columns=["_t", "_s", "_p1", "_p2"])

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
            
            t_col = "teacher" if "teacher" in st.session_state.evaluations_df.columns else "Teacher"
            df_my_eval = filter_df_by_clean_col(st.session_state.evaluations_df, t_col, user_info['name'])
            df_my_eval_export = format_evaluations_export(df_my_eval)
            
            st.markdown("##### 1. Bảng Đánh Giá EQ 6 Tiêu Chí Của Lớp")
            st.dataframe(df_my_eval_export, use_container_width=True)
            
            if not df_my_eval.empty:
                render_eq_charts(df_my_eval, f"LỚP {user_info.get('class_name', '')}")
            
            st.markdown("---")
            st.markdown("##### 2. Bảng Xu Hướng & So Sánh EQ Của Lớp")
            
            tc_col = "teacher" if "teacher" in st.session_state.comparisons_df.columns else "Teacher"
            df_my_comp = filter_df_by_clean_col(st.session_state.comparisons_df, tc_col, user_info['name'])
            df_my_comp_export = format_comparisons_export(df_my_comp)
            
            st.dataframe(df_my_comp_export, use_container_width=True)
            st.markdown("##### 📊 Thống Kê Biến Thiên EQ Toàn Lớp")
            st.table(calculate_class_stats(df_my_comp))
            
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
