# auth.py
import sqlite3
import bcrypt

DB_FILE = "users.db"

# ======================
#   KHỞI TẠO DATABASE
# ======================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Bảng user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    # Bảng lịch sử dự đoán
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            hours REAL,
            classwork REAL,
            homework REAL,
            predicted_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    conn.commit()

    # Tạo tài khoản admin mặc định (nếu chưa có)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, ("admin", hashed, "admin"))
        conn.commit()
        print("Admin mặc định đã được tạo: admin / admin123")

    conn.close()


# Gọi tự động khi import
init_db()


# ======================
#   ĐĂNG KÝ USER
# ======================
def register(username, password, role="user"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Kiểm tra username tồn tại
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Tên đăng nhập đã tồn tại!"

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed_pw, role))
        conn.commit()
        conn.close()
        return True, "Đăng ký thành công!"
    except Exception as e:
        conn.close()
        return False, f"Lỗi khi tạo tài khoản: {e}"


# ======================
#   ĐĂNG NHẬP
# ======================
def login(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "Tên đăng nhập không tồn tại!", None

    stored_pw = row[0].encode()
    role = row[1]

    if bcrypt.checkpw(password.encode(), stored_pw):
        return True, "Đăng nhập thành công!", role

    return False, "Sai mật khẩu!", None


# ======================
#   LƯU LỊCH SỬ DỰ ĐOÁN
# ======================
def save_prediction(username, hours, classwork, homework, predicted_score):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions (username, hours, classwork, homework, predicted_score)
        VALUES (?, ?, ?, ?, ?)
    """, (username, hours, classwork, homework, predicted_score))

    conn.commit()
    conn.close()


# ======================
#   LẤY LỊCH SỬ DỰ ĐOÁN
# ======================
def get_history(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hours, classwork, homework, predicted_score, created_at
        FROM predictions
        WHERE username = ?
        ORDER BY id DESC
    """, (username,))

    rows = cursor.fetchall()
    conn.close()
    return rows


# ======================
#   ADMIN: LẤY DANH SÁCH USER
# ======================
def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Trả đúng 3 cột: id, username, role
    cursor.execute("SELECT id, username, role FROM users ORDER BY id ASC")
    rows = cursor.fetchall()

    conn.close()
    return rows  # [(1, "admin", "admin"), (2, "user1", "user"), ...]


# ======================
#   ADMIN: XOÁ USER
# ======================
def delete_user(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if username == "admin":
        conn.close()
        return False, "Không thể xoá tài khoản admin mặc định."

    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        conn.close()
        return False, "User không tồn tại."

    # Xóa lịch sử dự đoán trước
    cursor.execute("DELETE FROM predictions WHERE username = ?", (username,))
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))

    conn.commit()
    conn.close()
    return True, f"Đã xoá user '{username}' và toàn bộ lịch sử."


# ======================
#   ADMIN: RESET PASSWORD
# ======================
def reset_password(username, new_password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        conn.close()
        return False, "User không tồn tại."

    hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))

    conn.commit()
    conn.close()
    return True, f"Mật khẩu cho '{username}' đã được đặt lại."
