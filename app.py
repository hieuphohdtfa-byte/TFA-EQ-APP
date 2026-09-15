import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG & CUSTOM CSS (GIAO DIỆN VÀNG - TRẮNG - XÁM)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TFA - Xu Hướng Phát Triển Cảm Xúc Cho Trẻ",
    layout="wide",
    page_icon="☀️"
)

# Custom CSS tạo giao diện Vàng - Trắng - Xám
st.markdown("""
    <style>
        /* Màu nền toàn trang */
        .stApp {
            background-color: #FFFDF5;
        }
        /* Thanh Header chính màu Vàng */
        .main-header {
            background: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
            padding: 18px 25px;
            border-radius: 12px;
            color: #1A1A1A;
            box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
            margin-bottom: 25px;
        }
        .main-header h2 {
            color: #1A1A1A !important;
            font-weight: 700;
            margin: 0;
        }
        .main-header p {
            color: #333333;
            margin: 5px 0 0 0;
            font-size: 14px;
        }
        /* Nút bấm primary màu vàng */
        .stButton>button {
            background-color: #FFC107;
            color: #1A1A1A;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #FFB300;
            color: #000000;
            box-shadow: 0 2px 8px rgba(255, 179, 0, 0.4);
        }
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #FFF9E6;
            border-right: 1px solid #FFE082;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. KHỞI TẠO SESSION STATE (LƯU TRỮ DỮ LIỆU TẠM THỜI)
# -----------------------------------------------------------------------------
if 'users' not in st.session_state:
    # Tài khoản giáo viên mặc định mẫu
    st.session_state.users = {
        "co_huong": {
            "password": "123",
            "name": "Cô Thu Hương",
            "campus": "Cơ sở TFA Hà Đô (Cát Lái, TP.HCM)",
            "class_name": "Lớp Chồi Hà Đô (4-5T)"
        }
    }

if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

if 'students_db' not in st.session_state:
    # Dữ liệu học sinh khởi tạo theo từng tài khoản giáo viên
    st.session_state.students_db = {
        "co_huong": ["Nguyễn Tony", "Trần Hamy", "Lê Laland", "Đào Minh Kiên"]
    }

if 'evaluations_db' not in st.session_state:
    st.session_state.evaluations_db = []

if 'daily_logs_db' not in st.session_state:
    st.session_state.daily_logs_db = []

# Danh sách 5 Cơ sở thuộc hệ thống TFA
TFA_CAMPUSES = [
    "Cơ sở TFA Hà Đô (Cát Lái, TP.HCM)",
    "Cơ sở TFA Lê Văn Sỹ (Quận 3, TP.HCM)",
    "Cơ sở TFA Dương Bạch Mai (Quận 8, TP.HCM)",
    "Cơ sở TFA Him Lam (Quận 7, TP.HCM)",
    "Cơ sở TFA Trần Thị Lý (Đà Nẵng)"
]

# -----------------------------------------------------------------------------
# 3. HEADER THƯƠNG HIỆU
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="main-header">
        <h2>☀️ HỆ THỐNG QUẢN LÝ EQ - THE FIRST ACADEMY (TFA)</h2>
        <p>Ứng dụng Theo dõi & Đánh giá Xu hướng Phát triển Cảm xúc Cho Trẻ Mầm Non</p>
    </div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. MỤC ĐĂNG NHẬP / ĐĂNG KÝ TÀI KHOẢN GIÁO VIÊN
# -----------------------------------------------------------------------------
if st.session_state.logged_user is None:
    st.subheader("🔐 CỔNG ĐĂNG NHẬP / ĐĂNG KÝ GIÁO VIÊN")
    
    auth_tab1, auth_tab2 = st.tabs(["🔑 Đăng Nhập", "📝 Đăng Ký Tài Khoản Mới"])
    
    # --- FORM ĐĂNG NHẬP ---
    with auth_tab1:
        st.markdown("##### Đăng nhập tài khoản giáo viên")
        login_user = st.text_input("Tên đăng nhập / Mã GV:", key="login_u")
        login_pass = st.text_input("Mật khẩu:", type="password", key="login_p")
        
        if st.button("Đăng Nhập"):
            if login_user in st.session_state.users and st.session_state.users[login_user]["password"] == login_pass:
                st.session_state.logged_user = login_user
                st.success(f"🎉 Đăng nhập thành công! Chào mừng {st.session_state.users[login_user]['name']}")
                st.rerun()
            else:
                st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác!")

    # --- FORM ĐĂNG KÝ ---
    with auth_tab2:
        st.markdown("##### Đăng ký tài khoản giáo viên mới")
        reg_name = st.text_input("Họ và tên giáo viên:")
        reg_user = st.text_input("Tên đăng nhập mong muốn:")
        reg_pass = st.text_input("Mật khẩu:", type="password")
        reg_campus = st.selectbox("Chọn Cơ sở đang giảng dạy:", TFA_CAMPUSES)
        reg_class = st.text_input("Nhập tên Lớp phụ trách (VD: Lớp Chồi 1, Lớp Mầm 2):")
        
        if st.button("Đăng Ký Tài Khoản"):
            if reg_user in st.session_state.users:
                st.warning("⚠️ Tên đăng nhập này đã tồn tại! Vui lòng chọn tên khác.")
            elif not reg_user or not reg_pass or not reg_class or not reg_name:
                st.error("⚠️ Vui lòng điền đầy đủ các thông tin đăng ký.")
            else:
                st.session_state.users[reg_user] = {
                    "password": reg_pass,
                    "name": reg_name,
                    "campus": reg_campus,
                    "class_name": reg_class
                }
                st.session_state.students_db[reg_user] = []
                st.success("🎉 Đăng ký tài khoản thành công! Bạn có thể qua tab Đăng nhập ngay.")

# -----------------------------------------------------------------------------
# 5. KHÔNG GIAN LÀM VIỆC CỦA GIÁO VIÊN ĐÃ ĐĂNG NHẬP
# -----------------------------------------------------------------------------
else:
    user_info = st.session_state.users[st.session_state.logged_user]
    user_key = st.session_state.logged_user
    
    # Sidebar Thông tin Giáo viên & Đăng xuất
    st.sidebar.markdown(f"### 👤 Giáo viên: **{user_info['name']}**")
    st.sidebar.info(f"🏢 **Cơ sở:** {user_info['campus']}\n\n🏫 **Lớp:** {user_info['class_name']}")
    
    if st.sidebar.button("🚪 Đăng Xuất"):
        st.session_state.logged_user = None
        st.rerun()

    st.sidebar.markdown("---")
    main_menu = st.sidebar.radio(
        "DANH MỤC QUẢN LÝ:",
        [
            "🏫 1. Quản lý Lớp & Học sinh", 
            "📝 2. Nhật ký Cảm xúc Hằng ngày", 
            "🎯 3. Đánh giá EQ 6 Tiêu chí", 
            "📊 4. Báo cáo & Xuất File"
        ]
    )

    # --- MỤC 1: QUẢN LÝ LỚP & HỌC SINH ---
    if main_menu == "🏫 1. Quản lý Lớp & Học sinh":
        st.subheader(f"🏫 QUẢN LÝ DANH SÁCH LỚP: {user_info['class_name'].upper()}")
        st.write(f"**Cơ sở:** {user_info['campus']}")
        
        st.markdown("---")
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            st.markdown("##### ➕ Thêm Học sinh mới vào lớp")
            new_student = st.text_input("Nhập họ và tên học sinh mới:")
            if st.button("Thêm Học Sinh"):
                if new_student.strip():
                    st.session_state.students_db[user_key].append(new_student.strip())
                    st.success(f"Đã thêm bé **{new_student}** vào danh sách lớp!")
                    st.rerun()
                else:
                    st.warning("Vui lòng nhập tên học sinh!")

        with col_b:
            st.markdown("##### 📋 Danh sách Học sinh hiện tại của lớp")
            students = st.session_state.students_db.get(user_key, [])
            if students:
                for idx, s in enumerate(students, 1):
                    st.write(f"{idx}. **{s}**")
            else:
                st.info("Lớp chưa có học sinh nào. Vui lòng thêm học sinh mới!")

    # --- MỤC 2: NHẬT KÝ HẰNG NGÀY ---
    elif main_menu == "📝 2. Nhật ký Cảm xúc Hằng ngày":
        st.subheader("📝 NHẬT KÝ CẢM XÚC HẰNG NGÀY CỦA TRẺ")
        students = st.session_state.students_db.get(user_key, [])
        
        if not students:
            st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Quản lý Lớp & Học sinh' để thêm bé trước!")
        else:
            std_select = st.selectbox("Chọn học sinh:", students)
            log_date = st.date_input("Ngày theo dõi:")
            emotions = st.multiselect("Cảm xúc nổi bật trong ngày:", ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng / Chán nản 😮‍💨", "Tự hào 🌟"])
            note = st.text_area("Ghi chú bối cảnh & Can thiệp của giáo viên:")
            
            if st.button("💾 Lưu Nhật Ký Ngày"):
                st.session_state.daily_logs_db.append({
                    "Teacher": user_info['name'],
                    "Campus": user_info['campus'],
                    "Class": user_info['class_name'],
                    "Student": std_select,
                    "Date": str(log_date),
                    "Emotions": ", ".join(emotions),
                    "Note": note
                })
                st.success(f"Đã ghi nhận nhật ký hằng ngày cho bé **{std_select}**!")

    # --- MỤC 3: ĐÁNH GIÁ 6 TIÊU CHÍ ---
    elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
        st.subheader("🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ CHUẨN HÓA")
        students = st.session_state.students_db.get(user_key, [])
        
        if not students:
            st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Quản lý Lớp & Học sinh' để thêm bé trước!")
        else:
            std_eval = st.selectbox("Chọn học sinh đánh giá:", students)
            term = st.selectbox("Chọn Kỳ đánh giá:", ["Kỳ 1 (Đầu năm)", "Kỳ 2 (Cuối năm)"])
            
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
            elif peq >= 2.0:
                group = "🟠 Nhóm Cần cải thiện"
            else:
                group = "🔴 Nhóm Hỗ trợ đặc biệt"
                
            st.metric("Điểm EQ Tổng hợp (P_EQ):", peq, delta=group)
            
            if st.button("💾 Lưu Kết Quả Đánh Giá"):
                st.session_state.evaluations_db.append({
                    "Teacher": user_info['name'],
                    "Campus": user_info['campus'],
                    "Class": user_info['class_name'],
                    "Student": std_eval,
                    "Term": term,
                    "TC1": tc1, "TC2": tc2, "TC3": tc3,
                    "TC4": tc4, "TC5": tc5, "TC6": tc6,
                    "P_EQ": peq,
                    "Group": group
                })
                st.success(f"Đã lưu kết quả đánh giá cho bé **{std_eval}** thành công!")

    # --- MỤC 4: BÁO CÁO & XUẤT FILE ---
    else:
        st.subheader(f"📊 BÁO CÁO & XUẤT FILE CHO LỚP: {user_info['class_name'].upper()}")
        
        # Lọc dữ liệu thuộc đúng Lớp & Cơ sở của Giáo viên này
        my_evals = [e for e in st.session_state.evaluations_db if e['Teacher'] == user_info['name']]
        my_logs = [l for l in st.session_state.daily_logs_db if l['Teacher'] == user_info['name']]
        
        tab_r1, tab_r2 = st.tabs(["🎯 Báo cáo Kết quả EQ", "📝 Nhật ký Hằng ngày đã ghi"])
        
        with tab_r1:
            st.markdown("##### Bảng tổng hợp đánh giá EQ 6 Tiêu chí")
            if my_evals:
                df_eval = pd.DataFrame(my_evals)
                st.dataframe(df_eval, use_container_width=True)
                
                # Nút Xuất file CSV / Excel
                csv_eval = df_eval.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Xuất Báo Cáo EQ (File CSV / Excel)",
                    data=csv_eval,
                    file_name=f"Bao_Cao_EQ_{user_info['class_name']}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Chưa có dữ liệu đánh giá EQ nào được lưu cho lớp này.")

        with tab_r2:
            st.markdown("##### Bảng nhật ký cảm xúc hằng ngày")
            if my_logs:
                df_logs = pd.DataFrame(my_logs)
                st.dataframe(df_logs, use_container_width=True)
                
                csv_logs = df_logs.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Xuất Nhật Ký Cảm Xúc (File CSV / Excel)",
                    data=csv_logs,
                    file_name=f"Nhat_Ky_Cam_Xuc_{user_info['class_name']}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Chưa có nhật ký cảm xúc nào được lưu cho lớp này.")
