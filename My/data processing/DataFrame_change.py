# Изменение данных в DataFrame, если, к примеру, данные пришли в неверном виде

import pandas as pd
data = pd.read_csv("https://video.ittensive.com/python-advanced/internet-2018.raw.csv",
                   na_values="NA", names=["Регион", "int", "frac"])
print(data.head())