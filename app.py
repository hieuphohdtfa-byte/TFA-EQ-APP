import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG & GIAO DIỆN VÀNG - TRẮNG - XÁM
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TFA - Xu Hướng Phát Triển Cảm Xúc Cho Trẻ",
    layout="wide",
    page_icon="☀️"
)

# Custom CSS giao diện Vàng - Trắng - Xám
st.markdown("""
    <style>
        .stApp {
            background-color: #FFFDF5;
        }
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
        section[data-testid="stSidebar"] {
            background-color: #FFF9E6;
            border-right: 1px solid #FFE082;
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
    "Toddler 1",
    "Toddler 2",
    "Pre-school",
    "Kindergarten",
    "Pre-primary"
]

# -----------------------------------------------------------------------------
# 3. LƯU TRỮ SESSION STATE (CƠ SỞ DỮ LIỆU TẠM THỜI)
# -----------------------------------------------------------------------------
if 'users' not in st.session_state:
    st.session_state.users = {
        # 1. Admin Tổng Hệ Thống
        "admin": {
            "password": "admin123",
            "name": "Hệ Thống TFA EQ",
            "role": "super_admin",
            "campus_code": "ALL",
            "campus": "Tất cả cơ sở"
        },
        # 2. BGH Từng Cơ Sở
        "bghHD": {
            "password": "123456", "name": "BGH Cơ Sở Hà Đô", "role": "campus_admin",
            "campus_code": "HD", "campus": CAMPUS_MAP["HD"]
        },
        "bghTTL": {
            "password": "123456", "name": "BGH Cơ Sở Trần Thị Lý", "role": "campus_admin",
            "campus_code": "TTL", "campus": CAMPUS_MAP["TTL"]
        },
        "bghDBM": {
            "password": "123456", "name": "BGH Cơ Sở Dương Bạch Mai", "role": "campus_admin",
            "campus_code": "DBM", "campus": CAMPUS_MAP["DBM"]
        },
        "bghHL": {
            "password": "123456", "name": "BGH Cơ Sở Him Lam", "role": "campus_admin",
            "campus_code": "HL", "campus": CAMPUS_MAP["HL"]
        },
        "bghLVS": {
            "password": "123456", "name": "BGH Cơ Sở Lê Văn Sỹ", "role": "campus_admin",
            "campus_code": "LVS", "campus": CAMPUS_MAP["LVS"]
        },
        # 3. Tài khoản Giáo viên Mẫu
        "0900000000HD": {
            "password": "123456", "name": "Cô Thu Hương", "role": "teacher",
            "campus_code": "HD", "campus": CAMPUS_MAP["HD"], "class_name": "Kindergarten 1"
        }
    }

if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

if 'students_db' not in st.session_state:
    st.session_state.students_db = {
        "0900000000HD": ["Nguyễn Tony", "Trần Hamy", "Lê Laland", "Đào Minh Kiên"]
    }

if 'evaluations_db' not in st.session_state:
    st.session_state.evaluations_db = []

if 'daily_logs_db' not in st.session_state:
    st.session_state.daily_logs_db = []

# -----------------------------------------------------------------------------
# 4. HEADER THƯƠNG HIỆU
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="main-header">
        <h2>☀️ HỆ THỐNG QUẢN LÝ EQ - THE FIRST ACADEMY (TFA)</h2>
        <p>Ứng dụng Theo dõi & Đánh giá Xu hướng Phát triển Cảm xúc Cho Trẻ Mầm Non</p>
    </div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. CỔNG ĐĂNG NHẬP (BẢO MẬT & TỐI GIẢN - CHỈ HIỆN FORM ĐĂNG NHẬP)
# -----------------------------------------------------------------------------
if st.session_state.logged_user is None:
    st.subheader("🔐 ĐĂNG NHẬP HỆ THỐNG")
    
    col_login, _ = st.columns([1, 1])
    with col_login:
        login_user = st.text_input("Tên đăng nhập:", key="login_u").strip()
        login_pass = st.text_input("Mật khẩu:", type="password", key="login_p").strip()
        
        if st.button("Đăng Nhập"):
            if login_user in st.session_state.users and st.session_state.users[login_user]["password"] == login_pass:
                st.session_state.logged_user = login_user
                u_info = st.session_state.users[login_user]
                st.success(f"🎉 Đăng nhập thành công! Chào mừng {u_info['name']}")
                st.rerun()
            else:
                st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác! Vui lòng kiểm tra lại.")

# -----------------------------------------------------------------------------
# 6. KHÔNG GIAN LÀM VIỆC THEO VAI TRÒ
# -----------------------------------------------------------------------------
else:
    user_info = st.session_state.users[st.session_state.logged_user]
    user_key = st.session_state.logged_user
    role = user_info.get("role", "teacher")
    
    # --- SIDEBAR THÔNG TIN ---
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
        main_menu = st.sidebar.radio(
            "DANH MỤC SUPER ADMIN:",
            [
                "👑 1. Tạo & Quản lý Tài khoản (BGH & Giáo viên)",
                "📊 2. Báo cáo EQ Toàn Hệ Thống",
                "📝 3. Nhật ký Cảm xúc Toàn Hệ Thống"
            ]
        )
        
        if main_menu == "👑 1. Tạo & Quản lý Tài khoản (BGH & Giáo viên)":
            st.subheader("👑 QUẢN LÝ TÀI KHOẢN TOÀN HỆ THỐNG")
            tab_acc1, tab_acc2 = st.tabs(["➕ Tạo Tài Khoản Mới", "📋 Danh Sách Tài Khoản"])
            
            with tab_acc1:
                acc_type = st.radio("Chọn loại tài khoản muốn tạo:", ["Giáo Viên (SĐT + Mã Cơ sở)", "BGH Cơ Sở"])
                
                if acc_type == "Giáo Viên (SĐT + Mã Cơ sở)":
                    c1, c2, c3 = st.columns(3)
                    with c1: t_phone = st.text_input("Số điện thoại (VD: 0912345678):").strip()
                    with c2: t_code = st.selectbox("Cơ sở:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}")
                    with c3: t_name = st.text_input("Họ tên Giáo viên:").strip()
                    t_pass = st.text_input("Mật khẩu khởi tạo:", value="123456")
                    
                    if st.button("➕ Tạo Tài Khoản Giáo Viên"):
                        if t_phone and t_name:
                            gen_u = f"{t_phone}{t_code}"
                            st.session_state.users[gen_u] = {
                                "password": t_pass, "name": t_name, "role": "teacher",
                                "campus_code": t_code, "campus": CAMPUS_MAP[t_code], "class_name": "Chưa tạo lớp"
                            }
                            st.session_state.students_db[gen_u] = []
                            st.success(f"🎉 Đã tạo TK Giáo viên: `{gen_u}` | Pass: `{t_pass}`")
                        else: st.error("Vui lòng điền đầy đủ thông tin!")
                            
                else:
                    c1, c2 = st.columns(2)
                    with c1: bgh_code = st.selectbox("Chọn Cơ sở quản lý:", list(CAMPUS_MAP.keys()), format_func=lambda x: f"{x} - {CAMPUS_MAP[x]}", key="bgh_c")
                    with c2: bgh_name = st.text_input("Tên đại diện BGH:", value=f"BGH {CAMPUS_MAP[bgh_code]}").strip()
                    bgh_u = st.text_input("Tên đăng nhập BGH:", value=f"bgh{bgh_code}").strip()
                    bgh_p = st.text_input("Mật khẩu BGH:", value="123456")
                    
                    if st.button("➕ Tạo Tài Khoản BGH Cơ Sở"):
                        st.session_state.users[bgh_u] = {
                            "password": bgh_p, "name": bgh_name, "role": "campus_admin",
                            "campus_code": bgh_code, "campus": CAMPUS_MAP[bgh_code]
                        }
                        st.success(f"🎉 Đã tạo TK BGH Cơ sở: `{bgh_u}` | Pass: `{bgh_p}`")

            with tab_acc2:
                acc_list = []
                for k, v in st.session_state.users.items():
                    acc_list.append({
                        "Tài khoản": k, "Họ tên / Đại diện": v.get("name"),
                        "Vai trò": "Super Admin" if v.get("role")=="super_admin" else ("BGH Cơ sở" if v.get("role")=="campus_admin" else "Giáo viên"),
                        "Cơ sở": v.get("campus"), "Mật khẩu": v.get("password")
                    })
                st.dataframe(pd.DataFrame(acc_list), use_container_width=True)

        elif main_menu == "📊 2. Báo cáo EQ Toàn Hệ Thống":
            st.subheader("📊 BÁO CÁO TỔNG HỢP EQ TOÀN HỆ THỐNG (5 CƠ SỞ)")
            sel_c = st.selectbox("Lọc Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()))
            evals = st.session_state.evaluations_db
            if sel_c != "Tất cả cơ sở": evals = [e for e in evals if e.get('Campus') == sel_c]
            
            if evals:
                df_all = pd.DataFrame(evals)
                st.dataframe(df_all, use_container_width=True)
                csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel / CSV Báo Cáo EQ Toàn Trường", csv_data, "Bao_Cao_EQ_Toan_Truong.csv", "text/csv")
            else: st.info("Chưa có dữ liệu đánh giá EQ nào.")

        else:
            st.subheader("📝 NHẬT KÝ CẢM XÚC TOÀN HỆ THỐNG")
            sel_c = st.selectbox("Lọc Cơ sở:", ["Tất cả cơ sở"] + list(CAMPUS_MAP.values()), key="log_c")
            logs = st.session_state.daily_logs_db
            if sel_c != "Tất cả cơ sở": logs = [l for l in logs if l.get('Campus') == sel_c]
            if logs:
                df_l = pd.DataFrame(logs)
                st.dataframe(df_l, use_container_width=True)
                csv_l = df_l.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất File Excel / CSV Nhật Ký Toàn Trường", csv_l, "Nhat_Ky_Cam_Xuc_Toan_Truong.csv", "text/csv")
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
                f"🏫 1. Quản lý Giáo viên & Lớp ({my_code})",
                f"📊 2. Báo cáo EQ Cơ sở ({my_code})",
                f"📝 3. Nhật ký Cảm xúc Cơ sở ({my_code})"
            ]
        )
        
        if main_menu == f"🏫 1. Quản lý Giáo viên & Lớp ({my_code})":
            st.subheader(f"🏫 BGH QUẢN LÝ CƠ SỞ: {my_campus.upper()}")
            st.markdown("##### ➕ Tạo tài khoản Giáo viên mới cho Cơ sở mình")
            col1, col2 = st.columns(2)
            with col1: t_phone = st.text_input("Số điện thoại Giáo viên:").strip()
            with col2: t_name = st.text_input("Họ và tên Giáo viên:").strip()
            
            if st.button("➕ Tạo Tài Khoản Giáo Viên Cơ Sở"):
                if t_phone and t_name:
                    gen_u = f"{t_phone}{my_code}"
                    st.session_state.users[gen_u] = {
                        "password": "123456", "name": t_name, "role": "teacher",
                        "campus_code": my_code, "campus": my_campus, "class_name": "Chưa tạo lớp"
                    }
                    st.session_state.students_db[gen_u] = []
                    st.success(f"🎉 Tạo thành công TK Giáo viên: `{gen_u}` | Mật khẩu mặc định: `123456`")
                else: st.error("Vui lòng điền đủ SĐT và Họ tên!")

            st.markdown("---")
            st.markdown(f"##### 📋 Danh sách Giáo viên thuộc {my_campus}")
            t_my_campus = []
            for k, v in st.session_state.users.items():
                if v.get("role") == "teacher" and v.get("campus_code") == my_code:
                    t_my_campus.append({
                        "Tài khoản (SĐT+Mã)": k, "Giáo viên": v.get("name"),
                        "Lớp phụ trách": v.get("class_name", "Chưa tạo"), "Mật khẩu": v.get("password")
                    })
            if t_my_campus: st.dataframe(pd.DataFrame(t_my_campus), use_container_width=True)
            else: st.info("Cơ sở chưa có giáo viên nào.")

        elif main_menu == f"📊 2. Báo cáo EQ Cơ sở ({my_code})":
            st.subheader(f"📊 BÁO CÁO TỔNG HỢP EQ - {my_campus.upper()}")
            campus_evals = [e for e in st.session_state.evaluations_db if e.get('Campus') == my_campus]
            
            if campus_evals:
                df_c = pd.DataFrame(campus_evals)
                st.dataframe(df_c, use_container_width=True)
                csv_c = df_c.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label=f"📥 Xuất Báo Cáo EQ {my_code} (Nộp BGH Tổng)", data=csv_c, file_name=f"Bao_Cao_EQ_{my_code}.csv", mime="text/csv")
            else: st.info(f"Chưa có dữ liệu đánh giá EQ nào thuộc {my_campus}.")

        else:
            st.subheader(f"📝 NHẬT KÝ CẢM XÚC - {my_campus.upper()}")
            campus_logs = [l for l in st.session_state.daily_logs_db if l.get('Campus') == my_campus]
            
            if campus_logs:
                df_cl = pd.DataFrame(campus_logs)
                st.dataframe(df_cl, use_container_width=True)
                csv_cl = df_cl.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label=f"📥 Xuất Nhật Ký Cảm Xúc {my_code} (Nộp BGH Tổng)", data=csv_cl, file_name=f"Nhat_Ky_Cam_Xuc_{my_code}.csv", mime="text/csv")
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
                "📊 4. Báo cáo & Xuất File Lớp"
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
                std_select = st.selectbox("Chọn học sinh:", students)
                log_date = st.date_input("Ngày theo dõi:")
                emotions = st.multiselect("Cảm xúc nổi bật trong ngày:", ["Vui 😊", "Buồn 😢", "Giận 😡", "Yêu thương 🥰", "Hào hứng 🤩", "Lo lắng / Chán nản 😮‍💨", "Tự hào 🌟"])
                note = st.text_area("Ghi chú bối cảnh & Can thiệp của giáo viên:")
                
                if st.button("💾 Lưu Nhật Ký Ngày"):
                    st.session_state.daily_logs_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_select,
                        "Date": str(log_date), "Emotions": ", ".join(emotions), "Note": note
                    })
                    st.success(f"Đã lưu nhật ký cho bé **{std_select}**!")

        elif main_menu == "🎯 3. Đánh giá EQ 6 Tiêu chí":
            st.subheader(f"🎯 ĐÁNH GIÁ EQ 6 TIÊU CHÍ - LỚP {user_info.get('class_name').upper()}")
            students = st.session_state.students_db.get(user_key, [])
            
            if not students: st.warning("⚠️ Lớp bạn chưa có học sinh. Vui lòng vào mục '1. Tạo Lớp & Quản lý Học sinh' để thêm bé!")
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
                if peq >= 3.2: group = "🟢 Nhóm Duy trì"
                elif peq >= 2.0: group = "🟠 Nhóm Cần cải thiện"
                else: group = "🔴 Nhóm HỖ TRỢ ĐẶC BIỆT"
                    
                st.metric("Điểm EQ Tổng hợp (P_EQ):", peq, delta=group)
                
                if st.button("💾 Lưu Kết Quả Đánh Giá"):
                    st.session_state.evaluations_db.append({
                        "Teacher": user_info['name'], "Campus": user_info['campus'],
                        "Class": user_info['class_name'], "Student": std_eval, "Term": term,
                        "TC1": tc1, "TC2": tc2, "TC3": tc3, "TC4": tc4, "TC5": tc5, "TC6": tc6,
                        "P_EQ": peq, "Group": group
                    })
                    st.success(f"Đã lưu kết quả đánh giá cho bé **{std_eval}**!")

        else:
            st.subheader(f"📊 BÁO CÁO & XUẤT FILE LỚP {user_info.get('class_name').upper()}")
            my_evals = [e for e in st.session_state.evaluations_db if e['Teacher'] == user_info['name']]
            my_logs = [l for l in st.session_state.daily_logs_db if l['Teacher'] == user_info['name']]
            
            tab_r1, tab_r2 = st.tabs(["🎯 Báo cáo EQ Lớp", "📝 Nhật ký Cảm xúc Lớp"])
            
            with tab_r1:
                if my_evals:
                    df_eval = pd.DataFrame(my_evals)
                    st.dataframe(df_eval, use_container_width=True)
                    csv_eval = df_eval.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất Báo Cáo EQ Lớp (CSV/Excel)", csv_eval, f"Bao_Cao_EQ_{user_info['class_name']}.csv", "text/csv")
                else: st.info("Chưa có dữ liệu đánh giá EQ nào.")

            with tab_r2:
                if my_logs:
                    df_logs = pd.DataFrame(my_logs)
                    st.dataframe(df_logs, use_container_width=True)
                    csv_logs = df_logs.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Xuất Nhật Ký Lớp (CSV/Excel)", csv_logs, f"Nhat_Ky_{user_info['class_name']}.csv", "text/csv")
                else: st.info("Chưa có nhật ký cảm xúc nào.")
