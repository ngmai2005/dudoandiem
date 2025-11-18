import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import pickle

# Tạo dataset 500 dòng với Hours > 10 và noise để mô phỏng may mắn / áp lực
np.random.seed(42)
n_samples = 500

# Hours từ 0 đến 20 (mở rộng)
hours = np.random.uniform(0, 20, n_samples)
classwork = np.random.uniform(0, 10, n_samples)
homework = np.random.uniform(0, 10, n_samples)

# Giả lập: 30% Hours + 40% Classwork + 30% Homework + noise
noise = np.random.normal(0, 1.5, n_samples)  # ±1.5 điểm
score = 0.3*hours + 0.4*classwork + 0.3*homework + noise

# Giới hạn điểm từ 0 đến 10
score = np.clip(score, 0, 10)

# Tạo DataFrame
data = pd.DataFrame({
    'Hours': hours.round(2),
    'Classwork': classwork.round(2),
    'Homework': homework.round(2),
    'Score': score.round(2)
})

# --- Lưu dataset (tùy chọn) ---
data.to_csv("dataset_500_extended.csv", index=False)
print("Dataset 500 dòng đã được tạo và mở rộng:", data.shape)

# --- Xác định biến độc lập và phụ thuộc ---
X = data[['Hours', 'Classwork', 'Homework']]
y = data['Score']

# --- Chia dữ liệu train/test ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- Huấn luyện mô hình Random Forest ---
model = RandomForestRegressor(
    n_estimators=100,  # số cây trong rừng
    max_depth=10,      # độ sâu tối đa để học được nhiều chi tiết
    random_state=42
)
model.fit(X_train, y_train)

# --- Đánh giá mô hình ---
score_r2 = model.score(X_test, y_test)
print(f"Độ chính xác mô hình (R²): {score_r2:.3f}")

# --- Lưu mô hình vào file ---
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Đã huấn luyện xong mô hình Random Forest và lưu vào model.pkl!")

