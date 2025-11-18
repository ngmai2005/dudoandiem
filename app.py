import streamlit as st
import pickle
import numpy as np
import shap
import matplotlib.pyplot as plt

#Từ auth import đăng kí, đăng nhập, lưu phiên làm việc và lấy lịch sử dự đoán
from auth import register, login, save_prediction, get_history

#Giao diện Đăng kí, Đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Trạng thái bật/tắt trang lịch sử
if "view_history" not in st.session_state:
    st.session_state.view_history = False

# Khởi tạo role mặc định nếu chưa có
if "role" not in st.session_state:
    st.session_state.role = "user"

# --- Phần đăng nhập / đăng ký (thay thế phần cũ) ---
if not st.session_state.logged_in:

    st.title(" Hệ thống đăng nhập")

    menu = st.radio("Chọn chức năng:", ["Đăng nhập", "Đăng ký"])

    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")

    if menu == "Đăng nhập":
        if st.button("Đăng nhập"):
            ok, msg, role = login(username, password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error(msg)

    else:  # Đăng ký
        # Cho phép admin tạo tài khoản admin nếu đang đăng ký bằng admin (ở đây mặc định role=user)
        role_choice = st.selectbox("Chọn role (chỉ dùng nếu bạn có quyền admin để tạo admin)", ["user", "admin"])
        if st.button("Tạo tài khoản"):
            ok, msg = register(username, password, role=role_choice)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.stop()   # NGĂN KHÔNG CHO CHẠY QUA TRANG DỰ ĐOÁN


# Hàm dự đoán điểm
def predict_score(model, hours, classwork, homework):
    user_input = np.array([[hours, classwork, homework]])
    prediction = model.predict(user_input)[0]
    predicted_score = np.clip(prediction, 0, 10)
    return predicted_score, user_input


# Hàm lấy SHAP values
def get_shap_info(model, user_input):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(user_input)
    
    # Nếu multi-output, lấy output đầu tiên
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    shap_values = shap_values[0]  # lấy 1D array cho 1 mẫu
    
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = base_value[0]
    
    return shap_values, base_value


# Hàm hiển thị SHAP
def display_shap(shap_values, base_value, user_input, feature_names):
    st.subheader("Giải thích vì sao mô hình dự đoán như vậy:")
    
    for i, feature in enumerate(feature_names):
        value = user_input[0][i]
        contribution = shap_values[i]
        effect = "🔺 tăng" if contribution > 0 else "🔻 giảm"
        st.write(f"- **{feature} ({value})**: góp phần {effect} **{abs(contribution):.2f} điểm**")
    
    st.write(
        f"Tổng hợp lại, điểm cơ sở là **{base_value:.2f}**, "
        f"sau khi cộng/trừ các yếu tố trên, mô hình dự đoán ra **{np.clip(np.sum(shap_values)+base_value,0,10):.2f}** điểm."
    )
    
    # Biểu đồ SHAP
    st.subheader("Biểu đồ tác động của từng yếu tố")
    colors = ['red' if val > 0 else 'blue' for val in shap_values]
    fig, ax = plt.subplots()
    ax.barh(feature_names, shap_values, color=colors)
    ax.set_xlabel("Mức độ ảnh hưởng đến điểm dự đoán")
    ax.set_title("Biểu đồ tác động của từng yếu tố")
    st.pyplot(fig)


# MAIN APP
# Load mô hình
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

    if st.session_state.role == "admin":
        st.sidebar.subheader("Admin Panel")
        admin_page = st.sidebar.radio("Quản lý:", ["Xem Users", "Xóa User", "Reset Password"])

        from auth import get_all_users, delete_user, reset_password

        # Xem danh sách users
        if admin_page == "Xem Users":
            users = get_all_users()
            import pandas as pd
            df = pd.DataFrame(users, columns=["ID", "Username", "Role"])
            st.subheader("Danh sách tài khoản")
            st.dataframe(df)

        # Xóa user
        elif admin_page == "Xóa User":
            username_del = st.text_input("Nhập username cần xóa:")
            if st.button("Xóa"):
                if username_del == "admin":
                    st.error("Không thể xóa admin!")
                else:
                    delete_user(username_del)
                    st.success("Đã xóa!")

        # Reset password
        elif admin_page == "Reset Password":
            username_reset = st.text_input("Username cần reset:")
            new_pass = st.text_input("Mật khẩu mới:")
            if st.button("Đặt lại mật khẩu"):
                reset_password(username_reset, new_pass)
                st.success("Mật khẩu đã được cập nhật!")


st.title("Ứng dụng AI Dự đoán Điểm Thi Sinh Viên")

# Nút chuyển sang trang lịch sử
if st.button("Xem lịch sử dự đoán"):
    st.session_state.view_history = True
    st.rerun()

#Button và giao diện xem lịch sử dự đoán
if st.session_state.view_history:
    st.subheader("Lịch sử dự đoán")

    history = get_history(st.session_state.username)

    if len(history) == 0:
        st.info("Bạn chưa có lịch sử dự đoán nào.")
    else:
        import pandas as pd
        df = pd.DataFrame(history, columns=[
            "Số giờ học", "Điểm bài tập trên lớp", "Điểm bài tập về nhà", 
            "Điểm dự đoán", "Thời gian"
        ])
        st.dataframe(df)

    # Nút quay lại trang dự đoán
    if st.button("⬅ Quay lại trang dự đoán"):
        st.session_state.view_history = False
        st.rerun()

    st.stop()


st.write(
    "Dự đoán điểm thi dựa trên **số giờ học**, "
    "**điểm bài tập trên lớp**, và **điểm bài tập về nhà**."
)

# Input người dùng
hours = st.number_input("Số giờ học", min_value=0.0, max_value=20.0, step=0.5)
classwork = st.number_input("Điểm bài tập trên lớp (0-10)", min_value=0.0, max_value=10.0, step=0.5)
homework = st.number_input("Điểm bài tập về nhà (0-10)", min_value=0.0, max_value=10.0, step=0.5)

feature_names = ['Số giờ học', 'Bài tập trên lớp', 'Bài tập về nhà']

if st.button("Dự đoán điểm thi"):
    predicted_score, user_input = predict_score(model, hours, classwork, homework)
    st.success(f"Điểm thi dự đoán: **{predicted_score:.2f}**")

    # Lưu vào lịch sử
    save_prediction(
        st.session_state.username,
        hours,
        classwork,
        homework,
        predicted_score
    )

    shap_values, base_value = get_shap_info(model, user_input)
    display_shap(shap_values, base_value, user_input, feature_names)

# Nếu đã đăng nhập
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    
    # Hiển thị sidebar
    st.sidebar.subheader("Tài khoản")
    st.sidebar.write(f" {st.session_state['username']} ({st.session_state['role']})")

    # Nút đăng xuất
    if st.sidebar.button("Đăng xuất"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
