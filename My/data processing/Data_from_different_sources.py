"""Инструкции к заданию
20 минут на выполнение
Получите данные по безработице в Москве:
https://video.ittensive.com/python-advanced/data-9753-2019-07-25.utf.csv
Объедините эти данные индексами (Месяц/Год) с данными из предыдущего задания (вызовы пожарных)
для Центральный административный округ:
https://video.ittensive.com/python-advanced/data-5283-2019-10-04.utf.csv
Найдите значение поля UnemployedMen в том месяце, когда было меньше всего вызовов в
Центральном административном округе.
Вопросы к этому заданию
Значение поля UnemployedMen
---
Пример решения:
загрузка и объединения данных по индексу.
Значение поля UnemployedMen
13465"""
import pandas as pd

data1 = pd.read_csv("https://video.ittensive.com/python-advanced/data-9753-2019-07-25.utf.csv",
                    delimiter=";")
# Установка индекса по году и месяцу. Т.е. разные колонки необходимо привести к одному индексу
data1 = data1.set_index(["Year", "Period"])
# Смотрим, что данные загрузились
print(data1.head())
data2 = pd.read_csv("https://video.ittensive.com/python-advanced/data-5283-2019-10-04.utf.csv",
                    delimiter=";")
# Смотрим, что данные загрузились
print(data2.head())
