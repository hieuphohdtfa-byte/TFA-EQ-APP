import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN VÀ THƯƠNG HIỆU HỆ THỐNG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TFA - Xu Hướng Phát Triển Cảm Xúc Cho Trẻ",
    layout="wide",
    page_icon="🏫",
    initial_sidebar_state="expanded"
)

# Thẻ Header thương hiệu
st.markdown("""
    <div style="background-color: #0072C6; padding: 15px; border-radius: 8px; color: white; margin-bottom: 20px;">
        <h2 style="margin:0; color:white;">🏫 HỆ THỐNG CẢM XÚC (EQ) - THE FIRST ACADEMY (TFA)</h2>
        <p style="margin:5px 0 0 0; opacity: 0.9;">Ứng dụng quản lý & theo dõi Xu hướng phát triển cảm xúc cho trẻ mầm non</p>
    </div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DỮ LIỆU ĐA CƠ SỞ (DỄ DÀNG THÊM CƠ SỞ MỚI BẰNG CÁCH THÊM DÒNG)
# -----------------------------------------------------------------------------
TFA_CAMPUS_DATA = {
    "Cơ sở TFA Hà Đô (Cát Lái, TP.HCM)": ["Lớp Mầm Hà Đô (3-4T)", "Lớp Chồi Hà Đô (4-5T)", "Lớp Lá Hà Đô (5-6T)"],
    "Cơ sở TFA Lê Văn Sỹ (Quận 3, TP.HCM)": ["Lớp Mầm LVS (3-4T)", "Lớp Chồi LVS (4-5T)", "Lớp Lá LVS (5-6T)"],
    "Cơ sở TFA Dương Bạch Mai (Quận 8, TP.HCM)": ["Lớp Mầm DBM (3-4T)", "Lớp Chồi DBM (4-5T)", "Lớp Lá DBM (5-6T)"],
    "Cơ sở TFA Him Lam (Quận 7, TP.HCM)": ["Lớp Mầm Him Lam (3-4T)", "Lớp Chồi Him Lam (4-5T)", "Lớp Lá Him Lam (5-6T)"],
    "Cơ sở TFA Trần Thị Lý (Đà Nẵng)": ["Lớp Mầm ĐN (3-4T)", "Lớp Chồi ĐN (4-5T)", "Lớp Lá ĐN (5-6T)"]
}

# -----------------------------------------------------------------------------
# 3. MENUS CHÍNH TRÊN APP
# -----------------------------------------------------------------------------
st.sidebar.title("📌 DANH MỤC ỨNG DỤNG")
app_mode = st.sidebar.radio(
    "Chọn mục làm việc:",
    ["📖 1. Giới thiệu & Nền tảng EQ", "💡 2. Hướng dẫn Quy trình", "🏫 3. Quản lý Đánh giá theo Cơ sở"]
)

# -----------------------------------------------------------------------------
# MỤC 1: GIỚI THIỆU
# -----------------------------------------------------------------------------
if app_mode == "📖 1. Giới thiệu & Nền tảng EQ":
    st.subheader("📖 GIỚI THIỆU HỆ THỐNG ĐÁNH GIÁ EQ CỦA TRẺ")
    st.info("Ứng dụng hỗ trợ giáo viên theo dõi và nâng cao năng lực cảm xúc cho trẻ từ 3–6 tuổi trên toàn hệ thống The FIRST Academy.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 🏢 Mạng lưới 5 Cơ sở Áp dụng")
        for campus in TFA_CAMPUS_DATA.keys():
            st.write(f"- **{campus}**")
    with col2:
        st.write("### 🎯 6 Tiêu chí Đánh giá EQ Chuẩn hóa")
        st.write("1. **TC1:** Nhận biết cảm xúc bản thân")
        st.write("2. **TC2:** Gọi tên & diễn đạt cảm xúc")
        st.write("3. **TC3:** Điều chỉnh & kiểm soát cảm xúc")
        st.write("4. **TC4:** Đồng cảm & quan hệ xã hội")
        st.write("5. **TC5:** Ảnh hưởng môi trường đến cảm xúc")
        st.write("6. **TC6:** Phản ứng khi cảm xúc được công nhận")

# -----------------------------------------------------------------------------
# MỤC 2: HƯỚNG DẪN
# -----------------------------------------------------------------------------
elif app_mode == "💡 2. Hướng dẫn Quy trình":
    st.subheader("💡 HƯỚNG DẪN THAO TÁC 3 BƯỚC CHO GIÁO VIÊN")
    st.markdown("""
    1. **Bước 1 (Nhật ký Hằng ngày):** Chọn Cơ sở ➔ Chọn Lớp ➔ Chạm biểu tượng Emoji nhận diện cảm xúc của trẻ trong ngày.
    2. **Bước 2 (Đánh giá Định kỳ):** Chọn Mức 1–4 cho 6 Tiêu chí. App sẽ tự động tính điểm $P_{EQ}$ và phân nhóm (*Duy trì*, *Cần cải thiện*, *Hỗ trợ đặc biệt*).
    3. **Bước 3 (Báo cáo Xu hướng):** Xem tự động kết quả so sánh độ biến thiên giữa các kỳ để nắm bắt đà tiến bộ của toàn lớp.
    """)

# -----------------------------------------------------------------------------
# MỤC 3: QUẢN LÝ DỮ LIỆU CƠ SỞ & LỚP HỌC
# -----------------------------------------------------------------------------
else:
    st.subheader("🏫 ĐÁNH GIÁ & THEO DÕI CẢM XÚC THEO LỚP HỌC")
    
    # Lựa chọn Cơ sở và Lớp
    c_campus, c_class = st.columns(2)
    with c_campus:
        selected_campus = st.selectbox("🏢 Chọn Cơ sở:", list(TFA_CAMPUS_DATA.keys()))
    with c_class:
        selected_class = st.selectbox("🏫 Chọn Lớp học:", TFA_CAMPUS_DATA[selected_campus])
        
    st.success(f"📍 Đang thao tác: **{selected_campus}** ➔ **{selected_class}**")
    
    # 3 Tab chức năng chính
    tab_daily, tab_eval, tab_report = st.tabs([
        "📝 Nhật ký Cảm xúc Hằng ngày", 
        "🎯 Đánh giá EQ 6 Tiêu chí", 
        "📊 Báo cáo & Xu hướng Lớp"
    ])
    
    # TAB 1: NHẬT KÝ HẰNG NGÀY
    with tab_daily:
        st.write("##### 📝 Nhật ký ghi nhận cảm xúc hằng ngày")
        student_daily = st.selectbox("Chọn học sinh:", ["Nguyễn Tony", "Trần Hamy", "Lê Laland", "Đào Minh Kiên"], key="std_d")
        st.date_input("Ngày theo dõi:")
        st.multiselect("Cảm xúc nổi bật trong ngày:", ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng / Chán nản 😮‍💨", "Tự hào 🌟"])
        st.text_area("Quan sát bối cảnh & Can thiệp của cô (hoặc bấm Micro nói):")
        if st.button("💾 Lưu Nhật Ký Ngày"):
            st.success(f"Đã lưu nhật ký ngày thành công cho bé {student_daily}!")

    # TAB 2: ĐÁNH GIÁ 6 TIÊU CHÍ
    with tab_eval:
        st.write("##### 🎯 Đánh giá 6 Tiêu chí EQ Định kỳ (Mức 1 - 4)")
        student_eval = st.selectbox("Chọn học sinh đánh giá:", ["Nguyễn Tony", "Trần Hamy", "Lê Laland", "Đào Minh Kiên"], key="std_e")
        
        c1, c2 = st.columns(2)
        with c1:
            tc1 = st.slider("TC1: Nhận biết cảm xúc bản thân", 1, 4, 2)
            tc2 = st.slider("TC2: Gọi tên và diễn đạt cảm xúc", 1, 4, 3)
            tc3 = st.slider("TC3: Điều chỉnh & kiểm soát cảm xúc", 1, 4, 2)
        with c2:
            tc4 = st.slider("TC4: Đồng cảm & quan hệ xã hội", 1, 4, 2)
            tc5 = st.slider("TC5: Ảnh hưởng môi trường đến cảm xúc", 1, 4, 3)
            tc6 = st.slider("TC6: Phản ứng khi cảm xúc được công nhận", 1, 4, 3)
            
        peq = round((tc1 + tc2 + tc3 + tc4 + tc5 + tc6) / 6.0, 2)
        st.metric(f"Điểm EQ Tổng hợp (P_EQ) của {student_eval}:", peq)
        
        if peq >= 3.2:
            st.success("🟢 Nhóm DUY TRÌ (P_EQ >= 3.2) - Đạt năng lực tự quản trị & ổn định")
        elif peq >= 2.0:
            st.warning("🟠 Nhóm CẦN CẢI THIỆN (2.0 <= P_EQ < 3.2) - Đang phát triển, nhận biết có điều kiện")
        else:
            st.error("🔴 Nhóm HỖ TRỢ ĐẶC BIỆT (P_EQ < 2.0) - Cần can thiệp & phối hợp gia đình khẩn cấp")

    # TAB 3: BÁO CÁO XU HƯỚNG
    with tab_report:
        st.write(f"##### 📊 Bảng phân tích Xu hướng Biến thiên EQ toàn lớp ({selected_class})")
        df_report = pd.DataFrame([
            {"STT": 1, "Tên học sinh": "Nguyễn Tony", "Kỳ 1 (T6)": 2.2, "Kỳ 2 (T7)": 3.0, "Thay đổi": "+0.8", "Xu hướng": "TIẾN BỘ VƯỢT BẬC"},
            {"STT": 2, "Tên học sinh": "Trần Hamy", "Kỳ 1 (T6)": 3.8, "Kỳ 2 (T7)": 3.0, "Thay đổi": "-0.8", "Xu hướng": "CẦN LƯU Ý (THỤT LÙI)"},
            {"STT": 3, "Tên học sinh": "Lê Laland", "Kỳ 1 (T6)": 2.5, "Kỳ 2 (T7)": 3.5, "Thay đổi": "+1.0", "Xu hướng": "TIẾN BỘ VƯỢT BẬC"},
            {"STT": 4, "Tên học sinh": "Đào Minh Kiên", "Kỳ 1 (T6)": 1.8, "Kỳ 2 (T7)": 3.0, "Thay đổi": "+1.2", "Xu hướng": "TIẾN BỘ VƯỢT BẬC"}
        ])
        st.dataframe(df_report, use_container_width=True)
