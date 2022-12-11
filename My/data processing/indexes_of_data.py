"""Индексы - это последовательность заголовком и наименований строк.
Индекс - это указать на одну из строк в сериях (столбцах) данных.
"""
import pandas as pd
"""При помощи skiprows=1 пропускается заголовок"""
data = pd.read_csv("https://video.ittensive.com/python-advanced/internet-2017.csv",
                   na_values="NA", decimal=",", skiprows=1, names=["Регион", "2017"])
print(data)
"""Создаём индекс сложным путём"""
data_indexed = pd.Series(data["2017"].values, index=data["Регион"].values)
print()
print("В данном DataFrame индексом стал регион.")
print(data_indexed)
"""Можно посмотреть, какой именно у нас индекс в конкретном DataFrame.
Индекс - это не серия данных в DataFrame. Это отдельный набор значений, которые указывают на конкретные
кортежи и т.д.
В DataFrame есть индексы и есть серии данных - это разные наборы данных.
"""
print(data_indexed.index)
"""Индексы можно назначить проще - сразу при импорте."""
data = pd.read_csv("https://video.ittensive.com/python-advanced/internet-2017.csv",
                   na_values="NA", decimal=",", skiprows=1, names=["Регион", "2017"], index_col="Регион")
print(data)
"""Индекс - это отдельный набор данных и его можно переименовать"""
data.index.name = "РЕГИОН"
print(data)
"""Индекс можно сбросить.
Это нужно, когда индекс надо вынести или наоборот внести в данные, чтобы из заново обработать и потом
как-то использовать"""
data = data.reset_index()
print(data)
