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
GAS_URL = "https://script.google.com/macros/s/AKfycbyLmKWVgiMnLk94OL1bjAVROT0jl-JhplqFmm1jpvIJMqZnUfzJUirRQMfyJsjgX34cPQ/exec"

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG & GIAO DIỆN VÀNG - TRẮNG - XÁM (TFA BRAND)
# (Lệnh Streamlit duy nhất đặt ngay đầu file)
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
# 2. BỘ TIÊU CHÍ EQ NGUYÊN BẢN 100% CHO CẢ 3 KHỐI LỚP (TỪ FILE 2. BỘ TIÊU CHÍ EQ)
# -----------------------------------------------------------------------------
CAMPUS_MAP = {
    "HD": "Cơ sở TFA Hà Đô (Phường Cát Lái, TP.HCM)",
    "TTL": "Cơ sở TFA Trần Thị Lý (Phường Hòa Cường, TP.Đà Nẵng)",
    "HL": "Cơ sở TFA Him Lam (Phường Tân Hưng, TP.HCM)",
    "DBM": "Cơ sở TFA Dương Bạch Mai (Phường Chánh Hưng, TP.HCM)",
    "LVS": "Cơ sở TFA Lê Văn Sỹ (Phường Phú Nhuận, TP.HCM)"
    "TTL": "Cơ sở TFA Trần Thị Lý (Phường Hòa Cường, TP.Đà Nẵng)"
}

TFA_CLASSES = ["Pre-school (3-4 tuổi)", "Kindergarten (4-5 tuổi)", "Pre-primary (5-6 tuổi)"]

TFA_ROUTINES = [
    "Đón trẻ - Thể dục sáng", "Ăn sáng", "Hoạt động có chủ đích",
    "Ăn trưa", "Ăn xế", "Hoạt động chiều", "Trả trẻ", "Tình huống phát sinh"
]
EMOTION_COLS = ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng 😮‍💨", "Tự hào 🌟"]

LOGO_FILE = "logo.png" if os.path.exists("logo.png") else ("Logo TFA Ver2.1 .png" if os.path.exists("Logo TFA Ver2.1 .png") else "logo.png")

# GIỮ NGUYÊN 100% NỘI DUNG NGUYÊN BẢN TỪ DOCUMENT "2. BỘ TIÊU CHÍ EQ CỦA TRẺ.DOCX"
CRITERIA_DATA = {
    "Pre-school (3-4 tuổi)": {
        "TC1": {
            1: "Mức 1: Khóc/giận/vui nhưng không biết vì sao, không có sự kết nối giữa hành động và suy nghĩ.",
            2: "Mức 2: Trẻ chỉ nhận diện được khi cô đặt câu hỏi xác nhận trực tiếp. Trả lời khi cô hỏi: 'Con đang buồn à?', 'Con thích nó à?'",
            3: "Mức 3: Trẻ tự dùng từ đơn để thông báo trạng thái mà không cần cô hỏi trước. Tự nói: 'Con buồn', 'Không thích', 'Vui lắm'.",
            4: "Mức 4: Tự nhận ra sớm trước khi bộc phát. Trẻ có dấu hiệu nhận ra cảm xúc từ sớm (trước khi bùng nổ) và thể hiện ra bên ngoài để tìm kiếm sự hỗ trợ, chia sẻ."
        },
        "TC2": {
            1: "Mức 1: Trẻ chỉ biểu đạt cảm xúc thuần túy qua các phản ứng sinh lý và xung năng (khóc, cười, la hét) mà chưa có sự kết nối với ngôn ngữ.",
            2: "Mức 2: Trẻ sử dụng từ vựng cảm xúc đơn lẻ, nói 1 từ đơn ('Giận', 'Buồn', 'Vui') để gọi tên trạng thái khi được gợi ý hoặc tự thân.",
            3: "Mức 3: Trẻ có khả năng nói câu đơn giản để định danh cảm xúc ('Con sợ quá' hoặc 'Con buồn', 'Con vui lắm').",
            4: "Mức 4: Trẻ diễn đạt + chỉ ra nguyên nhân bằng ngôn ngữ logic sơ khai."
        },
        "TC3": {
            1: "Mức 1: Phản ứng tiêu cực kéo dài, ăn vạ, ném đồ/yêu thích quá độ > 5 phút và khó bị tác động bởi lời nói của giáo viên.",
            2: "Mức 2: Trẻ bình tĩnh lại khi có sự can thiệp trực tiếp như dừng khi cô ôm/trấn an.",
            3: "Mức 3: Trẻ nghe theo hướng dẫn, nhắc nhở nhẹ nhàng điều chỉnh của cô để tự lấy lại bình tĩnh.",
            4: "Mức 4: Trẻ biết tự tìm các 'điểm tự an toàn', tự tìm góc bình tĩnh không cần cô can thiệp."
        },
        "TC4": {
            1: "Mức 1: Hoàn toàn không có phản ứng hoặc phớt lờ, thờ ơ khi thấy bạn khác đang khóc, đau hoặc gặp khó khăn. Chỉ quan tâm đến nhu cầu cá nhân.",
            2: "Mức 2: Có tạm dừng các hoạt động cá nhân để quan sát, theo dõi khi bạn có biểu hiện cảm xúc mạnh (khóc, giận, la hét, vui) nhưng không hành động.",
            3: "Mức 3: Trẻ thực hiện các cử chỉ an ủi sơ khai bằng hành động cụ thể: biết vuốt lưng/an ủi khi thấy bạn gặp vấn đề, dưới sự khích lệ hoặc tự thân.",
            4: "Mức 4: Chủ động kết nối giúp bạn giải tỏa/ chia sẻ niềm vui hoặc đề xuất chơi chung để bạn hết buồn ('Bạn đừng khóc nữa, chơi với tớ này')."
        },
        "TC5": {
            1: "Mức 1: Phụ thuộc hoàn toàn vào không khí lớp kể cả những thay đổi nhỏ hay xuất hiện những yếu tố lạ.",
            2: "Mức 2: Phụ thuộc vào sự an toàn quen thuộc, dễ bị lây cảm xúc, lo lắng, rụt rè và ngừng tương tác khi môi trường thay đổi.",
            3: "Mức 3: Ổn định trong môi trường quen thuộc, thích nghi có điều kiện.",
            4: "Mức 4: Ít bị ảnh hưởng tiêu cực, duy trì được tâm trạng dù môi trường có sự thay đổi."
        },
        "TC6": {
            1: "Mức 1: Có cơ chế phòng vệ, lảng tránh ánh mắt, không trả lời tiếp tục khóc, ăn vạ khi cô đã dỗ.",
            2: "Mức 2: Trẻ dịu lại 'nghe' khi cô nói nhưng chưa 'hiểu' hoặc chưa muốn thực hiện theo. Cần thời gian chờ lâu.",
            3: "Mức 3: Hợp tác sau khi được công nhận, kết nối lại và sẵn sàng thực hiện các yêu cầu đơn giản.",
            4: "Mức 4: Tự giải tỏa được tâm lý, chủ động tìm cô khi cần."
        }
    },
    "Kindergarten (4-5 tuổi)": {
        "TC1": {
            1: "Mức 1: Nói được cảm xúc nhưng chưa giải thích được lý do bởi lấn át bởi những hành động. Giận/buồn/vui nhưng chỉ nói 'con không thích', 'Con thích' mà chưa hiểu và nói được lý do.",
            2: "Mức 2: Xác nhận được lý do khi cô gợi ý câu hỏi nguyên nhân-kết quả. Có thể trả lời khi cô hỏi: 'Con buồn vì bạn lấy đồ chơi của con'.",
            3: "Mức 3: Chủ động sử dụng câu ghép để giải thích trạng thái: 'Con buồn vì bạn không chơi với con', 'Con vui vì thích bạn'.",
            4: "Mức 4: Nhận ra sớm cảm xúc, thông tin đến cô tự điều chỉnh hành vi, đưa giải pháp trước khi bộc phát: 'Con đang giận nên con muốn ngồi yên một chút', 'Muốn chia sẻ cùng bạn'."
        },
        "TC2": {
            1: "Mức 1: Ổn định, kiểm soát các hành động bản năng (đánh, ném, khóc, hét, chạy nhảy quá mức). Trẻ bắt đầu sử dụng ngôn ngữ bộc lộ trạng thái tâm lý.",
            2: "Mức 2: Trẻ tự gọi tên chính xác cảm xúc của mình bằng một câu đơn ngắn rõ ràng mà không cần giáo viên đặt câu hỏi gợi mở từ 2–3 từ: 'Con đang giận', 'Con buồn'.",
            3: "Mức 3: Nhận định được mối quan hệ giữa sự việc và trạng thái tâm lý cá nhân qua lời nói, cấu trúc 'nhân - quả' rõ hơn: 'Con buồn vì con thua trò chơi'; 'Con vui vì con thích điều đó'.",
            4: "Mức 4: Biểu đạt cảm xúc kèm mong muốn/ giải pháp cụ thể thay đổi tình huống: 'Con buồn vì bạn lấy bút của con, con muốn bạn trả lại'."
        },
        "TC3": {
            1: "Mức 1: Ổn định, kiềm chế, hành vi bộc phát vật lý ăn vạ kéo dài, vui mừng quá mức. Thay bằng bình tĩnh im lặng, hậm hực quay đi, dừng không hoạt động.",
            2: "Mức 2: Phối hợp điều chỉnh khi cô hướng dẫn, gợi ý để ngừng các phản ứng tiêu cực/quá khích (hít thở, uống nước, rửa mặt, tìm góc yên tĩnh).",
            3: "Mức 3: Chủ động tự điều chỉnh cảm xúc và dùng lời nói tự khích lệ ('Cố lên', 'Mình làm được', 'Con ngồi đây một chút cho hết giận') để duy trì trạng thái cân bằng, vượt qua khó khăn hoặc chờ đợi mà không cần cô can thiệp.",
            4: "Mức 4: Chủ động tách khỏi nguồn xung đột để bảo vệ cảm xúc bản thân, đồng thời tự khôi phục sự tự tin để tiếp tục hoàn thành hoạt động chung một cách hứng khởi."
        },
        "TC4": {
            1: "Mức 1: Trẻ nhận biết được trạng thái vui, buồn, giận của bạn qua nét mặt, cử chỉ và có phản ứng quan tâm cơ bản như dừng lại quan sát hoặc hỏi thăm 'Bạn sao vậy?'.",
            2: "Mức 2: Biểu đạt sự đồng cảm, thể hiện quan tâm bằng hành động cụ thể: an ủi hoặc giúp đỡ bạn (vỗ vai, chia sẻ đồ chơi, lấy khăn lau nước mắt hoặc đi tìm cô giúp bạn); vỗ tay, khen ngợi khi bạn vui và thành công.",
            3: "Mức 3: Trẻ chủ động hành động chia sẻ (an ủi khi bạn buồn, chúc mừng khi bạn vui) một cách tự nhiên và thường xuyên trong nhiều tình huống mà không cần giáo viên nhắc nhở.",
            4: "Mức 4: Trẻ chủ động mời gọi, kết nối các bạn cùng chơi và biết sử dụng lời nói để hòa giải các mâu thuẫn nhỏ và sự đoàn kết trong nhóm chơi/lớp."
        },
        "TC5": {
            1: "Mức 1: Còn phản ứng bản năng, nhận biết những sự thay đổi môi trường: bộc lộ sự khó chịu, lo lắng, khóc, phấn khích thu hút sự chú ý.",
            2: "Mức 2: Hiểu và nhận biết được liên hệ cảm xúc của mình với ngoại cảnh và chủ động tìm sự chia sẻ và hỗ trợ: 'Con buồn vì bạn buồn', 'Con thích vì lớp mình có đồ chơi mới'.",
            3: "Mức 3: Biết lựa chọn không gian phù hợp với cảm xúc cá nhân để giữ trạng thái ổn định, không bị cuốn theo sự xáo trộn, kích thích từ môi trường xung quanh ('tự lấy đồ chơi, ôm gấu bông', 'chọn góc chơi không gian chơi').",
            4: "Mức 4: Có tinh thần chủ động nhắc nhở, giữ trật tự cùng cô để có không gian thoải mái cho bản thân và tập thể."
        },
        "TC6": {
            1: "Mức 1: Trẻ có dấu hiệu chuyển hóa trạng thái bùng nổ (khóc, gào, ăn vạ), kích thích quá độ (vui, hạnh phúc) sang lắng nghe, thả lỏng cơ thể, giảm các phản ứng xung năng khi được cô gọi đúng cảm xúc và thấu hiểu.",
            2: "Mức 2: Trẻ chủ động phối hợp với cô: kể lại sự việc, nguyên nhân khi có sự đồng cảm và xoa dịu từ giáo viên ('Con buồn vì bạn lấy đồ chơi', 'Sợ tiếng ồn').",
            3: "Mức 3: Có sự bình tĩnh, chủ động đề xuất để giải quyết tình huống ('tự đi lấy khăn lau nước mắt, chủ động ra bắt tay làm hòa với bạn, hoặc tiếp tục hoàn thành bài vẽ dở') khi được công nhận cảm xúc.",
            4: "Mức 4: Hiểu về nguyên nhân - kết quả của hành vi, cảm xúc bản thân và đưa lời hứa để không lặp lại cảm xúc trên."
        }
    },
    "Pre-primary (5-6 tuổi)": {
        "TC1": {
            1: "Mức 1: Có khả năng định danh được những sắc thái cảm xúc phức tạp và không ăn vạ thô sơ. Chỉ nói được cảm xúc, sắc thái một cách chung chung, chưa gọi tên được cảm xúc thực tế.",
            2: "Mức 2: Trẻ bắt đầu sử dụng một vài cụm từ vựng cảm xúc bậc cao: hồi hộp, xấu hổ, tự hào thay vì chỉ nói vui/buồn và cảm xúc, sắc thái một cách chung chung.",
            3: "Mức 3: Lý giải được nguyên nhân, hiểu mối liên hệ giữa sự kiện khách quan và phản ứng chủ quan. Giải thích được tại sao mình có cảm xúc đó khi có sự gợi ý: 'Con thấy lo vì con chưa làm xong bài mà sắp hết giờ'.",
            4: "Mức 4: Nhận ra sớm và nói được cảm xúc + dự báo cường độ ngay khi sự việc xảy ra mà không cần nhắc nhở: 'Con đang cực kỳ thất vọng vì con đã rất cố gắng', 'Con đang hơi bực nên con muốn bình tĩnh trước'. Duy trì được sự điềm tĩnh khi nói."
        },
        "TC2": {
            1: "Mức 1: Cảm xúc quá mạnh trẻ chỉ dùng âm thanh, hành động (đẩy, kéo) để biểu đạt. Hoặc im lặng tuyệt đối, không thể thốt ra lời hoặc nói đơn giản 'Con không thích' dù cô đã dỗ dành, chia sẻ.",
            2: "Mức 2: Diễn đạt rập khuôn, hoặc diễn đạt được khi cô đặt câu hỏi lựa chọn với những cảm xúc phức tạp: 'Con đang thấy hụt hẫng vì bạn không chơi cùng hay con thấy giận?'.",
            3: "Mức 3: Nói rõ được từ vựng sắc thái, bắt đầu tự kết nối được logic nhân quả cảm xúc + nguyên nhân: 'Con buồn vì con thua trò chơi'. Nhưng cần cô hỏi thêm 'Điều gì làm con thấy như vậy?' mới kể rõ được câu chuyện.",
            4: "Mức 4: Diễn đạt trọn vẹn cảm xúc bình tĩnh, rõ ràng + giải pháp: 'Con buồn vì bạn không cho chơi, mình chơi chung được không?'. Bắt đầu hình thành khả năng kết nối Ngôn ngữ - Logic - Cảm xúc."
        },
        "TC3": {
            1: "Mức 1: Thời gian mất kiểm soát kéo dài (> 10 phút). Từ chối mọi sự vỗ về hay gợi ý bình tĩnh từ giáo viên. Cần tác động vật lý hoặc sự can thiệp liên tục từ giáo viên mới dịu lại.",
            2: "Mức 2: Trẻ lấy lại cân bằng được 100% nhờ sự điều hướng của giáo viên. Tốc độ hồi phục trung bình (5-7 phút). Nếu không được nhắc, trẻ sẽ tiếp tục trạng thái quá khích.",
            3: "Mức 3: Tự điều chỉnh đạt 80%. Thời gian hồi phục nhanh (3-5 phút). Có ý thức quay lại hoạt động nhóm sau chủ động nhận diện cảm xúc và đề xuất giải pháp: 'Cô ơi con ra góc ngồi một lát'. Cần một sự xác nhận hoặc khích lệ từ cô để thực hiện hành động đó.",
            4: "Mức 4: Tự nói phục hồi thời gian nhanh (< 2 phút): 'Con sẽ bình tĩnh rồi nói chuyện với bạn'. Biết điều chỉnh thái độ phù hợp với hoàn cảnh."
        },
        "TC4": {
            1: "Mức 1: Trẻ nhận biết được trạng thái cảm xúc của người khác qua nét mặt, cử chỉ. Biết dừng hoạt động cá nhân để hỏi han hoặc quan sát. Tuy nhiên, ưu tiên thỏa mãn nhu cầu cá nhân hơn quan tâm đến tác động cảm xúc lên đối tượng xung quanh.",
            2: "Mức 2: Trẻ bắt đầu biết quan sát và thực hiện các hành vi xã hội (chia sẻ, giúp đỡ, hỏi han) nhưng chỉ khi có sự nhắc nhở hoặc định hướng trực tiếp từ cô.",
            3: "Mức 3: Chủ động thực hiện hành vi tương trợ tự phát: biết hỏi han, an ủi khi bạn bất ổn. Bắt đầu sử dụng kỹ năng thương lượng để giải quyết mâu thuẫn: 'Tớ chơi trước, cậu chơi sau nhé' hoặc 'Chúng mình cùng chơi chung đi'. Biết cân bằng giữa nhu cầu cá nhân và lợi ích của bạn bè để duy trì cuộc chơi.",
            4: "Mức 4: Khả năng phối hợp nhóm và dẫn dắt giúp giải quyết, tôn trọng sự khác biệt: 'Hai bạn cùng chơi chung nhé'."
        },
        "TC5": {
            1: "Mức 1: Trẻ dễ bị kích động hoặc trở nên thu mình trước các thay đổi của môi trường, chưa biết cách tự thoát ra khỏi sự khó chịu do ngoại cảnh gây ra. Chưa hình thành màng lọc cảm xúc.",
            2: "Mức 2: Trẻ nhận ra mình khó chịu do môi trường 'Con thấy ồn quá' nhưng chỉ dừng lại ở việc than phiền hoặc chờ đợi cô giải quyết. Vẫn phụ thuộc vào sự can thiệp của cô để thay đổi trạng thái.",
            3: "Mức 3: Biết tìm kiếm các giải pháp thay thế phù hợp khi môi trường không như ý. Chủ động thay đổi vị trí hoặc hành động để giảm bớt ảnh hưởng của môi trường: tự di chuyển ra chỗ yên tĩnh hơn khi lớp quá ồn, hoặc tự tìm đồ chơi thay thế.",
            4: "Mức 4: Trẻ giữ được tâm thế ổn định dù môi trường thay đổi phức tạp. Duy trì hiệu suất hoạt động và thái độ tích cực bất chấp các biến số ngoại cảnh bất lợi: 'Thấy lớp lộn xộn, trẻ chủ động thu dọn để tạo không gian thoải mái cho mình và bạn'."
        },
        "TC6": {
            1: "Mức 1: Cần rất nhiều thời gian (> 15 phút), bị kẹt trong thế giới riêng, chưa có khả năng kết nối lại và nhiều phương pháp tiếp cận khác nhau từ giáo viên mới có thể bắt đầu dịu lại.",
            2: "Mức 2: Chấp nhận sự đồng cảm nhưng thụ động, dừng các phản ứng thái quá khi được cô gọi tên cảm xúc 'Cô biết con đang rất buồn'. Lấy lại bình tĩnh được nhưng không chủ động tham gia lại vào hoạt động lớp. Cần cô dắt tay hoặc khích lệ thêm mới chịu vận động.",
            3: "Mức 3: Phản hồi tích cực ngay sau khi được công nhận: biết gật đầu, lau nước mắt và chia sẻ thêm lý do khi cảm thấy được thấu hiểu. Biết dùng lời nói để xác nhận sự giải tỏa: 'Con đỡ buồn rồi ạ'.",
            4: "Mức 4: Thể hiện sự trưởng thành về tâm thế: không chỉ tự xoa dịu mà còn biết cảm ơn người đã lắng nghe mình. Chủ động tìm cách giải quyết: 'Con sẽ nói với bạn cho con chơi chung'."
        }
    }
}

# -----------------------------------------------------------------------------
# 🤖 THUẬT TOÁN MA TRẬN TỰ ĐỘNG "NHẶT" MINH CHỨNG VÀO 6 TIÊU CHÍ EQ
# -----------------------------------------------------------------------------
def auto_map_daily_to_criteria(student_name, teacher_name, daily_df):
    if daily_df is None or daily_df.empty:
        return None
    
    std_logs = daily_df[(daily_df['Student'] == student_name) & (daily_df['Teacher'] == teacher_name)]
    if std_logs.empty:
        return None
        
    neg_emotions_count = 0
    pos_emotions_count = 0
    total_logs = len(std_logs)
    
    context_evidences = []
    tc5_signals = [] # Môi trường / Đón trả trẻ
    tc4_signals = [] # Quan hệ bạn bè / Hoạt động nhóm
    tc3_signals = [] # Can thiệp / Tự cân bằng
    
    for _, row in std_logs.iterrows():
        emotions_text = str(row.get('Emotions', ''))
        note = str(row.get('Note', '')).strip()
        interv = str(row.get('Intervention', '')).strip()
        dt_str = str(row.get('Date', ''))
        
        has_neg = any(neg_e in emotions_text for neg_e in ["Buồn", "Giận", "Lo lắng"])
        has_pos = any(pos_e in emotions_text for pos_e in ["Vui", "Hào hứng", "Yêu thương", "Tự hào"])
        
        if has_neg: neg_emotions_count += 1
        if has_pos: pos_emotions_count += 1
        
        # Tách tín hiệu TC5 (Thích ứng môi trường Đón/Trả trẻ)
        if "Đón trẻ" in emotions_text or "Trả trẻ" in emotions_text or "Tình huống phát sinh" in emotions_text:
            if "Giận" in emotions_text or "Buồn" in emotions_text or "Lo lắng" in emotions_text:
                tc5_signals.append(1 if "khóc" in note.lower() or "ăn vạ" in note.lower() else 2)
            else:
                tc5_signals.append(4 if "tự giác" in note.lower() or "chủ động" in note.lower() else 3)
                
        # Tách tín hiệu TC4 (Đồng cảm & Quan hệ xã hội)
        if "Hoạt động chiều" in emotions_text or "Hoạt động có chủ đích" in emotions_text:
            if "Yêu thương" in emotions_text or "Tự hào" in emotions_text or "an ủi" in note.lower() or "chia sẻ" in note.lower():
                tc4_signals.append(4 if "chủ động" in note.lower() or "hòa giải" in note.lower() else 3)
            elif "Giận" in emotions_text:
                tc4_signals.append(1 if "đánh" in note.lower() or "tranh đồ" in note.lower() else 2)
                
        # Tách tín hiệu TC3 & TC6 (Can thiệp & Khả năng tự dịu)
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

    # Tính toán mức gợi ý cho từng Tiêu chí (1 - 4)
    if tc3_signals:
        auto_tc3 = round(sum(tc3_signals) / len(tc3_signals))
    else:
        auto_tc3 = 1 if neg_emotions_count > total_logs * 0.4 else (2 if neg_emotions_count > 0 else 3)
        
    auto_tc1 = 1 if neg_emotions_count > total_logs * 0.5 else (2 if neg_emotions_count > 2 else (4 if pos_emotions_count > total_logs * 0.7 else 3))
    auto_tc2 = auto_tc1
    auto_tc4 = round(sum(tc4_signals) / len(tc4_signals)) if tc4_signals else 3
    auto_tc5 = round(sum(tc5_signals) / len(tc5_signals)) if tc5_signals else (2 if neg_emotions_count > 3 else 3)
    auto_tc6 = auto_tc3
    
    # Đảm bảo điểm nằm trong khoảng 1..4
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
# 4. HÀM CHUẨN HÓA BẢNG XUẤT FILE EXCEL/CSV CHUẨN THEO MẪU
# -----------------------------------------------------------------------------
def format_evaluations_export(df):
    cols = [
        "STT", "Tên học sinh", "TC1", "TC2", "TC3", "TC4", "TC5", "TC6",
        "Điểm TB (PEQ)", "Nhóm Trạng Thái", "Bối cảnh/Minh chứng điển hình (hành vi cụ thể)",
        "Kết luận xu hướng", "Kế hoạch tác động tiếp theo", "Kỳ / Tháng", "Lớp", "Cơ sở", "Giáo viên"
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    export_df["Tên học sinh"] = df["Student"].values if "Student" in df.columns else ""
    export_df["TC1"] = pd.to_numeric(df["TC1"], errors='coerce').fillna(0) if "TC1" in df.columns else 0
    export_df["TC2"] = pd.to_numeric(df["TC2"], errors='coerce').fillna(0) if "TC2" in df.columns else 0
    export_df["TC3"] = pd.to_numeric(df["TC3"], errors='coerce').fillna(0) if "TC3" in df.columns else 0
    export_df["TC4"] = pd.to_numeric(df["TC4"], errors='coerce').fillna(0) if "TC4" in df.columns else 0
    export_df["TC5"] = pd.to_numeric(df["TC5"], errors='coerce').fillna(0) if "TC5" in df.columns else 0
    export_df["TC6"] = pd.to_numeric(df["TC6"], errors='coerce').fillna(0) if "TC6" in df.columns else 0
    
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
    cols = [
        "STT", "Tên học sinh", "Điểm đợt 1 (Kỳ 1)", "Điểm đợt 2 (Kỳ 2)",
        "Biến thiên", "Xu hướng EQ", "Kết luận xu hướng", "Kế hoạch tác động tiếp theo",
        "Lớp", "Cơ sở", "Giáo viên"
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    
    export_df = pd.DataFrame()
    export_df["STT"] = range(1, len(df) + 1)
    export_df["Tên học sinh"] = df["Student"].values if "Student" in df.columns else ""
    export_df["Điểm đợt 1 (Kỳ 1)"] = pd.to_numeric(df["Score_Term1"], errors='coerce').fillna(0.0) if "Score_Term1" in df.columns else 0.0
    export_df["Điểm đợt 2 (Kỳ 2)"] = pd.to_numeric(df["Score_Term2"], errors='coerce').fillna(0.0) if "Score_Term2" in df.columns else 0.0
    
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
    if df_comp is None or df_comp.empty:
        return pd.DataFrame([
            {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm DUY TRÌ (PEQ >= 3.2)", "Kỳ 1 / Tháng trước": "0.00%", "Kỳ 2 / Tháng sau": "0.00%", "Thay đổi (%)": "+0.00%"},
            {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm CẦN CẢI THIỆN (2.0 <= PEQ < 3.2)", "Kỳ 1 / Tháng trước": "0.00%", "Kỳ 2 / Tháng sau": "0.00%", "Thay đổi (%)": "+0.00%"},
            {"Chỉ số thống kê toàn lớp": "Tỉ lệ nhóm HỖ TRỢ ĐẶC BIỆT (PEQ < 2.0)", "Kỳ 1 / Tháng trước": "0.00%", "Kỳ 2 / Tháng sau": "0.00%", "Thay đổi (%)": "+0.00%"}
        ])
    
    total_stds = len(df_comp)
    s1 = pd.to_numeric(df_comp["Score_Term1"], errors='coerce').fillna(0) if "Score_Term1" in df_comp.columns else pd.Series([0]*total_stds)
    s2 = pd.to_numeric(df_comp["Score_Term2"], errors='coerce').fillna(0) if "Score_Term2" in df_comp.columns else pd.Series([0]*total_stds)
    
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
    if eval_df is None or eval_df.empty:
        st.info("Chưa có đủ dữ liệu để vẽ biểu đồ trực quan.")
        return
    
    st.markdown(f"#### 📊 BIỂU ĐỒ TRỰC QUAN PHÂN TÍCH CẢM XÚC EQ {title_prefix.upper()}")
    col_chart1, col_chart2 = st.columns(2)
    
    counts = eval_df["Group_Clean"].value_counts().reset_index() if "Group_Clean" in eval_df.columns else pd.DataFrame()
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
    if comp_df is None or comp_df.empty:
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
        
    trends = comp_df["Trend"].value_counts().reset_index() if "Trend" in comp_df.columns else pd.DataFrame()
    if not trends.empty:
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
            with st.form(key="form_create_bgh", clear_on_submit=True):
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
            df_export = format_evaluations_export(df_eval_raw)
            
            st.dataframe(df_export, use_container_width=True)
            if not df_eval_raw.empty:
                render_eq_charts(df_eval_raw, "(Toàn Trường)")
            else:
                st.info("ℹ️ Hệ thống chưa ghi nhận đánh giá EQ nào. Bạn vẫn có thể tải Khung Báo Cáo Mẫu (.csv) bên dưới.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Tổng Hợp EQ Chuẩn Mẫu",
                df_export.to_csv(index=False).encode('utf-8-sig'),
                "Bao_Cao_Tong_Hop_EQ_TFA.csv", "text/csv"
            )

        elif main_menu == "📈 3. Bảng So Sánh & Xu Hướng EQ":
            st.subheader("📈 BẢNG SO SÁNH & XU HƯỚNG PHÁT TRIỂN EQ TOÀN TRƯỜNG")
            df_comp_raw = st.session_state.comparisons_df
            df_comp_export = format_comparisons_export(df_comp_raw)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Toàn Trường")
            st.table(calculate_class_stats(df_comp_raw))
            
            if not df_comp_raw.empty:
                render_comparison_charts(df_comp_raw, "(Toàn Trường)")
            else:
                st.info("ℹ️ Chưa có dữ liệu so sánh xu hướng EQ toàn trường. Bạn vẫn có thể tải Khung Báo Cáo Mẫu bên dưới.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Xu Hướng EQ Chuẩn Mẫu",
                df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                "Bang_Xu_Huong_EQ_TFA.csv", "text/csv"
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
                        if gen_u in users_dict:
                            st.warning(f"⚠️ Tài khoản `{gen_u}` đã tồn tại!")
                        else:
                            new_row = pd.DataFrame([{
                                "username": gen_u, "password": "123456", "name": t_name,
                                "role": "teacher", "campus_code": my_code,
                                "campus": my_campus, "class_name": t_class, "status": "active"
                            }])
                            st.session_state.users_df = pd.concat([st.session_state.users_df, new_row], ignore_index=True)
                            save_sheet_to_gas("Users", st.session_state.users_df)
                            st.success(f"🎉 Đã lưu vĩnh viễn giáo viên {t_name} trên Google Sheets! TK: `{gen_u}` | Mật khẩu: `123456`")
                            st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")

            st.markdown("---")
            st.markdown(f"##### 📋 Danh Sách Giáo Viên Cơ Sở {my_code} (BGH có quyền Sửa / Đổi MK / Khóa / Xóa)")
            
            gv_idx_list = st.session_state.users_df[
                (st.session_state.users_df['role'] == 'teacher') & 
                (st.session_state.users_df['campus_code'] == my_code)
            ].index.tolist()
            
            if gv_idx_list:
                for idx in gv_idx_list:
                    row = st.session_state.users_df.loc[idx]
                    u_username = row['username']
                    u_name = row['name']
                    u_class = row.get('class_name', 'Chưa xếp lớp')
                    u_status = row.get('status', 'active')
                    status_badge = "🟢 Đang hoạt động" if u_status == "active" else "🔴 Đã khóa"
                    
                    c_g1, c_g2, c_g3, c_g4 = st.columns([2.5, 1, 1, 1])
                    with c_g1:
                        st.write(f"👩‍🏫 **{u_name}** | Lớp: `{u_class}` | TK: `{u_username}` | {status_badge}")
                    with c_g2:
                        if st.button("✏️ Sửa", key=f"edit_gv_btn_{idx}"):
                            st.session_state[f"editing_gv_{idx}"] = not st.session_state.get(f"editing_gv_{idx}", False)
                    with c_g3:
                        toggle_txt = "🔒 Khóa" if u_status == "active" else "🔓 Mở khóa"
                        if st.button(toggle_txt, key=f"toggle_gv_{idx}"):
                            new_st = "inactive" if u_status == "active" else "active"
                            st.session_state.users_df.loc[idx, 'status'] = new_st
                            save_sheet_to_gas("Users", st.session_state.users_df)
                            st.success(f"Đã chuyển trạng thái TK **{u_name}** sang `{new_st}`!")
                            st.rerun()
                    with c_g4:
                        if st.button("🗑️ Xóa", key=f"del_gv_{idx}"):
                            st.session_state.users_df = st.session_state.users_df.drop(idx).reset_index(drop=True)
                            save_sheet_to_gas("Users", st.session_state.users_df)
                            st.success(f"Đã xóa tài khoản giáo viên **{u_name}**!")
                            st.rerun()
                    
                    if st.session_state.get(f"editing_gv_{idx}", False):
                        with st.form(key=f"form_edit_gv_detail_{idx}"):
                            st.markdown(f"**Sửa thông tin cho Giáo viên: {u_name} (Nhấn Enter để Lưu)**")
                            col_e1, col_e2, col_e3 = st.columns(3)
                            with col_e1: new_gv_class = st.selectbox("Khối Lớp:", TFA_CLASSES, index=TFA_CLASSES.index(u_class) if u_class in TFA_CLASSES else 0)
                            with col_e2: new_gv_name = st.text_input("Họ và tên:", value=u_name)
                            with col_e3: new_gv_pass = st.text_input("Mật khẩu mới:", value=str(row['password']))
                            btn_save_gv = st.form_submit_button("💾 Lưu Thay Đổi (Hoặc nhấn Enter)")
                            
                            if btn_save_gv:
                                st.session_state.users_df.loc[idx, 'name'] = new_gv_name.strip()
                                st.session_state.users_df.loc[idx, 'class_name'] = new_gv_class
                                st.session_state.users_df.loc[idx, 'password'] = new_gv_pass.strip()
                                save_sheet_to_gas("Users", st.session_state.users_df)
                                st.session_state[f"editing_gv_{idx}"] = False
                                st.success("🎉 Đã cập nhật thông tin Giáo viên vĩnh viễn!")
                                st.rerun()
                    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("Cơ sở chưa có giáo viên nào. Hãy nhập thông tin ở bảng phía trên để tạo!")

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            st.subheader(f"📊 BÁO CÁO TỔNG HỢP EQ CƠ SỞ: {my_campus.upper()}")
            df_c = st.session_state.evaluations_df[st.session_state.evaluations_df['Campus'] == my_campus] if not st.session_state.evaluations_df.empty else pd.DataFrame()
            df_export = format_evaluations_export(df_c)
            
            st.dataframe(df_export, use_container_width=True)
            if not df_c.empty:
                render_eq_charts(df_c, f"({my_code})")
            else:
                st.info("ℹ️ Chưa có dữ liệu đánh giá EQ chính thức từ các lớp. Bạn vẫn có thể tải Khung Báo Cáo Mẫu (.csv) bên dưới.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Báo Cáo EQ Cơ Sở",
                df_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bao_Cao_EQ_{my_code}.csv", "text/csv"
            )

        else:
            st.subheader(f"📈 BẢNG SO SÁNH XU HƯỚNG EQ CƠ SỞ: {my_campus.upper()}")
            df_comp_c = st.session_state.comparisons_df[st.session_state.comparisons_df['Campus'] == my_campus] if not st.session_state.comparisons_df.empty else pd.DataFrame()
            df_comp_export = format_comparisons_export(df_comp_c)
            
            st.dataframe(df_comp_export, use_container_width=True)
            st.markdown("##### 📊 Bảng Thống Kê Chỉ Số Biến Thiên Cơ Sở")
            st.table(calculate_class_stats(df_comp_c))
            
            if not df_comp_c.empty:
                render_comparison_charts(df_comp_c, f"({my_code})")
            else:
                st.info("ℹ️ Chưa có dữ liệu so sánh xu hướng EQ từ các lớp. Bạn vẫn có thể tải Khung Báo Cáo Mẫu bên dưới.")
                
            st.download_button(
                "📥 Xuất File CSV/Excel Bảng Xu Hướng EQ Cơ Sở",
                df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                f"Bang_Xu_Huong_EQ_{my_code}.csv", "text/csv"
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
                btn_class = st.form_submit_button("💾 Cập Nhật Tên Lớp (Hoặc nhấn Enter)")
                if btn_class:
                    user_idx = st.session_state.users_df[st.session_state.users_df['username'] == user_key].index
                    if not user_idx.empty:
                        st.session_state.users_df.loc[user_idx, "class_name"] = custom_class_name
                        save_sheet_to_gas("Users", st.session_state.users_df)
                        st.success(f"🎉 Đã lưu tên lớp: **{custom_class_name}**")
                        st.rerun()

            st.markdown("---")
            
            with st.form(key="form_add_student", clear_on_submit=True):
                st.markdown("##### ➕ Thêm Học Sinh Mới (Gõ tên bé xong nhấn Enter)")
                new_student_val = st.text_input("Họ và tên học sinh mới:", key="input_new_student")
                btn_std = st.form_submit_button("➕ Thêm Học Sinh (Hoặc nhấn Enter)")
                
                if btn_std:
                    clean_name = new_student_val.strip()
                    if clean_name:
                        new_std_row = pd.DataFrame([{"teacher_user": user_key, "student_name": clean_name}])
                        st.session_state.students_df = pd.concat([st.session_state.students_df, new_std_row], ignore_index=True)
                        save_sheet_to_gas("Students", st.session_state.students_df)
                        st.success(f"🎉 Đã lưu vĩnh viễn bé **{clean_name}** vào Google Sheet!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập họ tên học sinh!")

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
                            new_name_val = st.text_input("Sửa lại họ và tên (Nhấn Enter để Lưu):", value=s_name)
                            btn_save_edit = st.form_submit_button("💾 Lưu Thay Đổi (Hoặc nhấn Enter)")
                            if btn_save_edit:
                                st.session_state.students_df.loc[idx, 'student_name'] = new_name_val.strip()
                                save_sheet_to_gas("Students", st.session_state.students_df)
                                st.session_state[f"editing_std_{idx}"] = False
                                st.success(f"🎉 Đã cập nhật tên thành **{new_name_val.strip()}**!")
                                st.rerun()
                    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("Lớp chưa có học sinh nào. Hãy nhập tên bé ở ô phía trên nhé!")

        # ---------------------------------------------------------------------
        # 📝 2. NHẬT KÝ CẢM XÚC HẰNG NGÀY (GIAO DIỆN TINH GỌN, CHỈ TÍCH CẢM XÚC & BỐI CẢNH)
        # ---------------------------------------------------------------------
        elif main_menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
            st.subheader("📋 HỒ SƠ CẢM XÚC CÁ NHÂN (HẰNG NGÀY)")
            st.caption("Ghi nhận cảm xúc & bối cảnh thực tế theo từng hoạt động trong ngày (Không bắt buộc chọn Mức độ gượng ép)")
            
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds:
                st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Quản lý Học sinh' để thêm học sinh trước!")
            else:
                col_s1, col_s2, col_s3 = st.columns([1.5, 1.5, 1])
                with col_s1: std_select = st.selectbox("👦/👧 Chọn học sinh:", my_stds)
                with col_s2: log_date = st.date_input("🗓️ Ngày theo dõi:", value=datetime.today())
                with col_s3: st.info(f"🏫 Lớp: **{user_info.get('class_name', 'Mầm')}**")
                
                dynamic_prefix = f"{std_select}_{log_date}"
                
                st.markdown("---")
                st.markdown("#### 1. Hoạt động trong ngày (Chỉ cần tích chọn cảm xúc & gõ ghi chú nếu có tình huống)")
                
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
                        "Ghi chú chi tiết hành vi": ""
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
                        "Ghi chú chi tiết hành vi": st.column_config.TextColumn("Ghi chú bối cảnh / hành vi cụ thể (Nếu có)", width="large")
                    },
                    hide_index=True,
                    use_container_width=True,
                    key=f"editor_{dynamic_prefix}"
                )
                
                st.markdown("---")
                st.markdown("#### 2. Quan sát nhanh của giáo viên & Đánh giá ngày")
                
                with st.form(key=f"daily_form_{dynamic_prefix}"):
                    col_o1, col_o2 = st.columns(2)
                    with col_o1:
                        note_context = st.text_area("📌 Bối cảnh và biểu hiện nổi bật:", placeholder="Mô tả cụ thể hành vi, cử chỉ hay bối cảnh xảy ra cảm xúc (VD: Tranh đồ chơi với bạn, khóc bám mẹ...)", key=f"context_{dynamic_prefix}")
                    with col_o2:
                        note_intervention = st.text_area("🤝 Can thiệp và hỗ trợ của giáo viên:", placeholder="Ghi lại hành động dỗ dành, ôm xoa dịu, hỏi gợi mở hay góc bình tĩnh cô đã dùng...", key=f"intervention_{dynamic_prefix}")
                        
                    st.markdown("---")
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        daily_trend = st.selectbox("📈 Xu hướng cảm xúc chung trong ngày:", [
                            "Duy trì cảm xúc tích cực, vui vẻ cả ngày",
                            "Có xáo trộn nhỏ ở đầu ngày, nhanh chóng cân bằng",
                            "Cần sự can thiệp và hỗ trợ dỗ dành nhiều từ cô",
                            "Cần lưu ý đặc biệt / Có biểu hiện bùng nổ cảm xúc"
                        ], key=f"trend_{dynamic_prefix}")
                    with col_d2:
                        daily_summary = st.text_area("💬 Nhận xét tự do của giáo viên:", placeholder="Cô tự do gõ nhận xét hoặc lưu ý cá nhân về bé trong ngày...", key=f"summary_{dynamic_prefix}")
                    
                    st.write("")
                    btn_save_daily = st.form_submit_button("💾 LƯU HỒ SƠ CẢM XÚC HẰNG NGÀY (HOẶC NHẤN ENTER)")
                    
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
                            
                            details_dict[act_name] = {
                                "emotions": active_emos,
                                "note": act_note
                            }
                        
                        full_emotions_str = " | ".join(emotions_summary_list) if emotions_summary_list else "Bình thường ở tất cả hoạt động"
                        json_str = json.dumps(details_dict, ensure_ascii=False)
                        
                        new_log = pd.DataFrame([{
                            "Teacher": user_info['name'],
                            "Campus": user_info['campus'],
                            "Class": user_info.get('class_name', 'Pre-school (3-4 tuổi)'),
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
            my_logs = st.session_state.daily_logs_df[st.session_state.daily_logs_df['Teacher'] == user_info['name']] if not st.session_state.daily_logs_df.empty else pd.DataFrame()
            if not my_logs.empty:
                st.dataframe(my_logs[['Date', 'Student', 'Emotions', 'Note', 'Intervention', 'Summary']], use_container_width=True)
            else:
                st.info("Chưa có hồ sơ cảm xúc hằng ngày nào được lưu.")

        # ---------------------------------------------------------------------
        # 🎯 3. ĐÁNH GIÁ EQ 6 TIÊU CHÍ (CÓ MA TRẬN NHẶT TỰ ĐỘNG 1-CLICK TỪ NHẬT KÝ)
        # ---------------------------------------------------------------------
        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ (CÓ MA TRẬN NHẶT TỰ ĐỘNG THÔNG MINH)")
            st.caption("Cô chỉ cần tích chọn cảm xúc hằng ngày ➔ Bấm nút '⚡ TỰ ĐỘNG TỔNG HỢP' là hệ thống tự nhặt minh chứng & gợi ý điểm vào đúng 6 tiêu chí!")
            
            my_stds = st.session_state.students_df[st.session_state.students_df['teacher_user'] == user_key]['student_name'].tolist()
            if not my_stds: st.warning("⚠️ Lớp bạn chưa có học sinh.")
            else:
                col_e1, col_e2, col_e3 = st.columns([1.5, 1.5, 1.2])
                with col_e1: std_eval = st.selectbox("Chọn học sinh:", my_stds)
                with col_e2: 
                    eval_month = st.selectbox("Chọn Tháng đánh giá:", [f"Tháng {m}" for m in range(1, 13)], index=8)
                    term = f"{eval_month} / Kỳ {1 if int(eval_month.replace('Tháng ', '')) <= 6 else 2}"
                with col_e3:
                    user_class_str = user_info.get('class_name', 'Kindergarten (4-5 tuổi)')
                    if "Pre-school" in user_class_str or "3-4" in user_class_str:
                        curr_age_group = "Pre-school (3-4 tuổi)"
                    elif "Pre-primary" in user_class_str or "5-6" in user_class_str:
                        curr_age_group = "Pre-primary (5-6 tuổi)"
                    else:
                        curr_age_group = "Kindergarten (4-5 tuổi)"
                    
                    st.success(f"📘 Bộ tiêu chí: **{curr_age_group}**")
                
                # --- NÚT 1-CLICK TỰ ĐỘNG NHẶT MINH CHỨNG & ĐIỀN ĐIỂM ---
                st.markdown("---")
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
                        st.success(f"🎉 Đã tự động phân tích nhật ký và nhặt minh chứng vào 6 tiêu chí cho bé **{std_eval}**!")
                    else:
                        st.warning(f"⚠️ Chưa tìm thấy nhật ký hằng ngày của bé {std_eval}. Đang dùng mức mặc định chuẩn lứa tuổi!")

                # --- TRỢ LÝ MINH CHỨNG TỔNG HỢP TỪ NHẬT KÝ CẢM XÚC THÁNG ---
                with st.expander(f"🔍 TRỢ LÝ MINH CHỨNG CẢM XÚC THÁNG CỦA BÉ {std_eval.upper()} (TỰ ĐỘNG GOM TỪ NHẬT KÝ HẰNG NGÀY)", expanded=True):
                    std_logs = st.session_state.daily_logs_df[
                        (st.session_state.daily_logs_df['Student'] == std_eval) & 
                        (st.session_state.daily_logs_df['Teacher'] == user_info['name'])
                    ] if not st.session_state.daily_logs_df.empty else pd.DataFrame()
                    
                    if not std_logs.empty:
                        col_ev1, col_ev2 = st.columns(2)
                        with col_ev1:
                            st.markdown(f"**📊 Tổng số ngày có ghi nhận nhật ký:** `{len(std_logs)} ngày`")
                            all_emos_str = " ".join(std_logs['Emotions'].dropna().tolist())
                            vui_cnt = all_emos_str.count("Vui")
                            buon_cnt = all_emos_str.count("Buồn")
                            gian_cnt = all_emos_str.count("Giận")
                            lo_cnt = all_emos_str.count("Lo lắng")
                            st.write(f"- 😊 **Vui vẻ / Hào hứng:** {vui_cnt} lượt")
                            st.write(f"- 😢 **Buồn / Lo lắng:** {buon_cnt + lo_cnt} lượt")
                            st.write(f"- 😡 **Giận / Khóc bực:** {gian_cnt} lượt")
                        with col_ev2:
                            st.markdown("**📌 Bối cảnh & Can thiệp nổi bật gần đây:**")
                            for idx_l, row_l in std_logs.tail(3).iterrows():
                                st.markdown(f"- *Ngày {row_l['Date']}:* {row_l['Emotions']} | **Bối cảnh:** {row_l['Note']} | **Can thiệp:** {row_l['Intervention']}")
                    else:
                        st.info(f"Chưa có dữ liệu nhật ký hằng ngày cho bé {std_eval} trong tháng này. Bạn vẫn có thể thực hiện đánh giá độc lập bên dưới.")

                st.markdown("---")
                st.markdown(f"#### 📝 BẢNG ĐÁNH GIÁ 6 TIÊU CHÍ EQ NHÓM {curr_age_group.upper()}")
                st.caption("Hệ thống tự điền theo gợi ý từ nhật ký hoặc Cô có thể tự tay điều chỉnh lại theo thực tế")
                
                curr_crit_map = CRITERIA_DATA.get(curr_age_group, CRITERIA_DATA["Kindergarten (4-5 tuổi)"])
                
                col_c1, col_c2 = st.columns(2)
                
                def_tc1 = st.session_state.get(f"tc1_{std_eval}", 3)
                def_tc2 = st.session_state.get(f"tc2_{std_eval}", 3)
                def_tc3 = st.session_state.get(f"tc3_{std_eval}", 3)
                def_tc4 = st.session_state.get(f"tc4_{std_eval}", 3)
                def_tc5 = st.session_state.get(f"tc5_{std_eval}", 3)
                def_tc6 = st.session_state.get(f"tc6_{std_eval}", 3)
                
                with col_c1:
                    st.markdown("##### 1. TC1: Nhận biết cảm xúc bản thân")
                    tc1_val = st.radio("Chọn Mức cho TC1:", [1, 2, 3, 4], index=def_tc1-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc1_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC1'][tc1_val]}")
                    
                    st.markdown("##### 2. TC2: Gọi tên và diễn đạt cảm xúc")
                    tc2_val = st.radio("Chọn Mức cho TC2:", [1, 2, 3, 4], index=def_tc2-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc2_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC2'][tc2_val]}")
                    
                    st.markdown("##### 3. TC3: Điều chỉnh và kiểm soát cảm xúc")
                    tc3_val = st.radio("Chọn Mức cho TC3:", [1, 2, 3, 4], index=def_tc3-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc3_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC3'][tc3_val]}")

                with col_c2:
                    st.markdown("##### 4. TC4: Đồng cảm và quan hệ xã hội")
                    tc4_val = st.radio("Chọn Mức cho TC4:", [1, 2, 3, 4], index=def_tc4-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc4_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC4'][tc4_val]}")
                    
                    st.markdown("##### 5. TC5: Ảnh hưởng môi trường đến cảm xúc")
                    tc5_val = st.radio("Chọn Mức cho TC5:", [1, 2, 3, 4], index=def_tc5-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc5_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC5'][tc5_val]}")
                    
                    st.markdown("##### 6. TC6: Phản ứng khi cảm xúc được công nhận")
                    tc6_val = st.radio("Chọn Mức cho TC6:", [1, 2, 3, 4], index=def_tc6-1, format_func=lambda x: f"Mức {x}", key=f"radio_tc6_{std_eval}", horizontal=True)
                    st.info(f"💡 {curr_crit_map['TC6'][tc6_val]}")

                peq = round((tc1_val + tc2_val + tc3_val + tc4_val + tc5_val + tc6_val) / 6.0, 2)
                group_clean = "DUY TRÌ" if peq >= 3.2 else ("CẦN CẢI THIỆN" if peq >= 2.0 else "HỖ TRỢ ĐẶC BIỆT")
                
                st.markdown("---")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("Điểm EQ Tổng hợp (PEQ):", peq, delta=f"Nhóm: {group_clean}")
                with col_m2:
                    st.info(f"📌 **Phân nhóm trạng thái:** `{group_clean}`\n\n*(PEQ ≥ 3.2: Duy trì phong độ | 2.0 ≤ PEQ < 3.2: Cần cải thiện | PEQ < 2.0: Hỗ trợ đặc biệt)*")
                
                def_ctx = st.session_state.get(f"ctx_{std_eval}", f"Dựa trên theo dõi tháng, bé {std_eval} có xu hướng...")
                def_cnc = st.session_state.get(f"cnc_{std_eval}", f"Bé {std_eval} thuộc nhóm {group_clean}, thể hiện sự...")
                def_pln = st.session_state.get(f"pln_{std_eval}", f"Tiếp tục hỗ trợ bé {std_eval} thực hành góc bình tĩnh và khuyến khích...")
                
                context_input = st.text_area("Bối cảnh / Minh chứng điển hình (Hành vi cụ thể):", value=def_ctx, key=f"context_area_{std_eval}")
                conclusion_input = st.text_area("Kết luận xu hướng phát triển:", value=def_cnc, key=f"conclusion_area_{std_eval}")
                plan_input = st.text_area("Kế hoạch tác động tiếp theo:", value=def_pln, key=f"plan_area_{std_eval}")
                
                if st.button("💾 Lưu Bảng Đánh Giá EQ (Lên Google Sheets)"):
                    new_eval = pd.DataFrame([{
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info.get('class_name', curr_age_group), "Student": std_eval, "Term": term,
                        "TC1": tc1_val, "TC2": tc2_val, "TC3": tc3_val, "TC4": tc4_val, "TC5": tc5_val, "TC6": tc6_val,
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
                
                c_input = st.text_area("Kết luận xu hướng:", value=f"Bé {std_comp} có xu hướng {trend_tag.lower()}...", key="comp_c_area")
                p_input = st.text_area("Kế hoạch tác động tiếp theo:", value=f"Tiếp tục đồng hành hỗ trợ bé {std_comp}...", key="comp_p_area")
                
                if st.button("💾 Lưu Bảng So Sánh Xu Hướng EQ (Lên Google Sheets)"):
                    st.session_state.comparisons_df = st.session_state.comparisons_df[
                        ~((st.session_state.comparisons_df['Teacher'] == user_info['name']) & (st.session_state.comparisons_df['Student'] == std_comp))
                    ]
                    
                    new_comp = pd.DataFrame([{
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info.get('class_name', 'Mầm'), "Student": std_comp,
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
            my_comps = st.session_state.comparisons_df[st.session_state.comparisons_df['Teacher'] == user_info['name']] if not st.session_state.comparisons_df.empty else pd.DataFrame()
            df_comp_exp = format_comparisons_export(my_comps)
            st.dataframe(df_comp_exp, use_container_width=True)
            
            st.markdown("##### 📊 THỐNG KÊ TỈ LỆ % PHÂN BỔ TOÀN LỚP (KỲ 1 VS KỲ 2)")
            st.table(calculate_class_stats(my_comps))

        # ---------------------------------------------------------------------
        # 📊 5. BÁO CÁO & XUẤT FILE LỚP (EXCEL / CSV CHUẨN CỘT MẪU)
        # ---------------------------------------------------------------------
        else:
            st.subheader("📊 BÁO CÁO TỔNG HỢP & XUẤT FILE ĐÁNH GIÁ EQ CỦA LỚP")
            
            tab_rep1, tab_rep2 = st.tabs(["📋 1. Bảng Kết Quả Đánh Giá EQ (6 Tiêu Chí)", "📈 2. Bảng So Sánh Xu Hướng EQ (2 Kỳ)"])
            
            with tab_rep1:
                my_evals = st.session_state.evaluations_df[st.session_state.evaluations_df['Teacher'] == user_info['name']] if not st.session_state.evaluations_df.empty else pd.DataFrame()
                df_eval_export = format_evaluations_export(my_evals)
                st.dataframe(df_eval_export, use_container_width=True)
                
                if not my_evals.empty:
                    render_eq_charts(my_evals, f"Lớp {user_info.get('class_name', '')}")
                else:
                    st.info("ℹ️ Lớp chưa có dữ liệu đánh giá EQ chính thức. Bạn vẫn có thể tải Khung Báo Cáo Mẫu (.csv) bên dưới.")
                    
                st.download_button(
                    "📥 XUẤT FILE EXCEL/CSV BẢNG TỔNG HỢP EQ CHUẨN MẪU",
                    df_eval_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bang_Tong_Hop_EQ_Lop_{user_info.get('class_name', '')}.csv",
                    "text/csv"
                )

            with tab_rep2:
                my_comps = st.session_state.comparisons_df[st.session_state.comparisons_df['Teacher'] == user_info['name']] if not st.session_state.comparisons_df.empty else pd.DataFrame()
                df_comp_export = format_comparisons_export(my_comps)
                st.dataframe(df_comp_export, use_container_width=True)
                
                st.markdown("##### 📊 Bảng Thống Kê Thay Đổi Chỉ Số Tỉ Lệ % Toàn Lớp")
                st.table(calculate_class_stats(my_comps))
                
                if not my_comps.empty:
                    render_comparison_charts(my_comps, f"Lớp {user_info.get('class_name', '')}")
                else:
                    st.info("ℹ️ Lớp chưa có dữ liệu so sánh xu hướng EQ. Bạn vẫn có thể tải Khung Báo Cáo Mẫu (.csv) bên dưới.")
                    
                st.download_button(
                    "📥 XUẤT FILE EXCEL/CSV BẢNG XU HƯỚNG EQ CHUẨN MẪU",
                    df_comp_export.to_csv(index=False).encode('utf-8-sig'),
                    f"Bang_Xu_Huong_EQ_Lop_{user_info.get('class_name', '')}.csv",
                    "text/csv"
                )
