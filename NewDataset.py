import numpy as np
import pandas as pd

np.random.seed(42)

n_samples = 500

hours = np.random.uniform(0, 10, n_samples)
classwork = np.random.uniform(0, 10, n_samples)
homework = np.random.uniform(0, 10, n_samples)

noise = np.random.normal(0, 1.5, n_samples)
score = 0.3*hours + 0.4*classwork + 0.3*homework + noise
score = np.clip(score, 0, 10)

df = pd.DataFrame({
    'Hours': hours.round(2),
    'Classwork': classwork.round(2),
    'Homework': homework.round(2),
    'Score': score.round(2)
})

df.to_csv("dataset_500.csv", index=False)
print("Dataset 500 dòng đã được tạo:", df.shape)
