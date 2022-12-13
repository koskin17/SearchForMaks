# Группировка данных
import pandas as pd

data = pd.read_csv("https://video.ittensive.com/python-advanced/data-5283-2019-10-04.utf.csv",
                   delimiter=";", na_values="NA")
print("Смотрим на данные")
print(data.head())
# Чистим данные от NaN
data.fillna(0, axis=1, inplace=True)
print("Данные после чистки от Nan")
print(data.head())
# Для того, чтобы сгуппировать данные, мы
