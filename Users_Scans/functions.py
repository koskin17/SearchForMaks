import os
import pandas as pd
from prettytable import PrettyTable as pt
from datetime import datetime, date, timedelta
import time

''' Столбцы в DataFrame по сканам
'UF_PERIOD',
'UF_TYPE',
'UF_POINTS',
'UF_CODE',
'Дилер+Монтажник',
'UF_USER_ID',
'UF_PROVIDED',
'Монтажник',
'UF_CREATED_AT',
'UF_IN_EVENT',
'UF_EVENT_STATUS',
'UF_EVENT_DATE',
'Дата',
'Страна',
'Месяц',
'Год',
'Сам себе',
'Монтажник.1',
'Комментарий' '''

''' Шаблон наименований столбцов '''
columns_name = ['ID',
                'Баллы',
                'Последняя авторизация в приложении',
                'Количество сеансов',
                'Город работы',
                'Страна',
                'Логин',
                'Тип пользователя',
                'Активность',
                'Дата регистрации',
                'Фамилия',
                'Имя',
                'Отчество',
                'E-Mail',
                'Последняя авторизация',
                'Дата изменения',
                'Город проживания',
                'Личный телефон',
                'Компания',
                'Назва дилера',
                'СПК 1',
                'СПК 2',
                'СПК 3',
                'СПК 4',
                'СПК 5']

exclude_list = []  # список исключаемых аккаунтов из подсчёта: тестовые, аксоровские и т.д.
countries = []  # список стран в базе

''' Список признаков аккаунтов, которые добавляются в exclude_list и которые исключаются из подсчёта '''
exclude_users = ['kazah89', 'sanin, ''samoilov', 'axorindustry', 'kreknina', 'zeykin', 'berdnikova', 'ostashenko',
                 'skalar', 'test', 'malyigor', 'ihormaly', 'axor']

months = ['Январь',
          'Февраль',
          'Март',
          'Апрель',
          'Май',
          'Июнь',
          'Июль',
          'Август',
          'Сентябрь',
          'Октябрь',
          'Ноябрь',
          'Декабрь']

df_users = pd.DataFrame(pd.read_excel('user_admin.xlsx'))
df_users = df_users.fillna('')  # замена значений NaN, получившихся из пустых ячеек в excel, на пустую строку

df_scans = pd.DataFrame(pd.read_excel('Данные по пользователям и сканам 2022.xlsx', index_col='ID'))

surname = {}  # список фамилий по ID пользователя
countries = []  # список стран
type_of_products = []  # список видов продукции


def check_file():
    """
    Проверка доступа к файлу.
    """
    if os.listdir('..'):
        print('Доступ к папке: OK')
    else:
        print('Нет доступа к папке с файлом!')
        return False

    ''' Проверяем наименования столбцов на листе с данными '''
    for column_name, df_column in zip(columns_name, df_users.columns):
        if column_name != df_column:
            print('Порядок и/или наименование столбцов не совпадает.')
            print('Должен быть столбец "', column_name, '", а в файле на этом месте столбец "', df_column, '"')
            print()
            print('Порядок и наименование столбцов в файле должен быть следующий:')
            print(columns_name)
            return False

    print('Наименование и порядок столбцов: ОК')

    if df_scans.shape[0] > 0:
        print('Данные успешно загружены. В истории сканирований', df_scans.shape[0], 'записей')

    return True


def exclude():
    """
    Формирование списка исключаемых из подсчёта пользователей.
    """

    for email in df_users['E-Mail']:
        if email == '':
            continue
        else:
            for i in exclude_users:
                if email not in exclude_list and i in email:
                    exclude_list.append(email)

    print('Список исключаемых аккаунтов сформирован.')


def countries_list():
    """
    Формирование списка стран в базе.
    """

    for country in df_users['Страна']:
        if country == '':
            continue
        else:
            if country not in countries:
                countries.append(country)


def total_stat():
    """
    Формирование польной статистики по пользователям.

    : return: вывод итоговой таблицы
    """

    total_amount_of_dealers = 0
    for country in countries:
        total_amount_of_dealers += amount_users_by_type(country, 'Дилер')

    total_amount_of_adjusters = 0
    for country in countries:
        total_amount_of_adjusters += amount_users_by_type(country, 'Монтажник')

    table = pt()
    table.field_names = ['Страна', 'Всего пользователей', 'Дилеры', 'Монтажники']
    for country in countries:
        table.add_rows([[country, total_amount_users(country), amount_users_by_type(country, 'Дилер'),
                         amount_users_by_type(country, 'Монтажник')]])

    table.add_rows([['Всего', '', total_amount_of_dealers, total_amount_of_adjusters]])
    print(table)


def total_amount_users(country):
    """
    Подсчёт общего кол-ва пользователей по стране.

    : param country: Страна
    : type country: str
    : return: общее кол-во пользователей
    : type return: int
    """

    total_amount = 0
    for df_email, df_user_type, df_country in zip(df_users['E-Mail'], df_users['Тип пользователя'], df_users['Страна']):
        if df_email not in exclude_list:
            if df_country == country and (df_user_type == 'Дилер' or df_user_type == 'Монтажник'):
                total_amount += 1

    return total_amount


def amount_users_by_country(users_type):
    """
    Вывод информации о кол-ве дилеров и монтажников по странам.
    Параметр передаётся при вызове функциями dealers или adjusters.

    : param users_type: Тип пользователя (дилер или монтажник)
    : type users_type: str
    : return: вывод итоговой таблицы
    """

    print()
    if users_type == 'Дилер':
        print('Количество дилеров по странам:')
        summ = 0
        table = pt()
        table.field_names = ['Страна', 'Дилеров']
        for country in countries:
            table.add_rows([[country, amount_users_by_type(country, users_type)]])
            summ += amount_users_by_type(country, users_type)

        table.add_rows([['Всего:', summ]])
        print(table)
    elif users_type == 'Монтажник':
        print()
        print('Количество монтажников по странам:')
        summ = 0
        table = pt()
        table.field_names = ['Страна', 'Монтажников']
        for country in countries:
            table.add_rows([[country, amount_users_by_type(country, users_type)]])
            summ += amount_users_by_type(country, users_type)

        table.add_rows([['Всего:', summ]])
        print(table)


def amount_users_by_type(country, user_type):
    """
    Подсчёт кол-ва дилеров / монтажников в стране.
    Параметры передаются при вызове функцией amount_users_by_country.

    : param country: Страна
    : type country: str
    : param user_type: Тип пользователя (дилер / монтажник)
    : type user_type: str
    : return: кол-во пользователей
    : type return: int
    """

    amount_of_users = 0
    for df_email, df_user_type, df_country in zip(df_users['E-Mail'], df_users['Тип пользователя'], df_users['Страна']):
        if df_email not in exclude_list:
            if df_user_type == user_type and df_country == country:
                amount_of_users += 1

    return amount_of_users


def last_authorization(year, user_type, country):
    """
    Подсчёт кол-ва пользователей, последний раз авторизировавшихся в приложении за конкретный год.
    Параметры передаются при вызове функцией last_authorization_in_app.

    : param year: int
    : type year: str
    : param user_type: Тип пользователя (дилер или монтажник)
    : type user_type: str
    : param country: Страна
    : type country: str
    : return: кол-во последний раз авторизовавщихся по стране и году
    : type return: int
    """

    last = 0
    if year == None:
        for email, df_last_authorization, df_user_type, df_country in zip(df_users['E-Mail'], df_users[
            'Последняя авторизация в приложении'], df_users['Тип пользователя'], df_users['Страна']):
            if email not in exclude_list:
                if df_last_authorization == '' and df_user_type == user_type and df_country == country:
                    last += 1
    else:
        for email, df_last_authorization, df_user_type, df_country in zip(df_users['E-Mail'], df_users[
            'Последняя авторизация в приложении'], df_users['Тип пользователя'], df_users['Страна']):
            if email not in exclude_list:
                if df_last_authorization == '':
                    continue
                elif int(df_last_authorization[6:10]) == year and df_user_type == user_type and df_country == country:
                    last += 1

    return last


def last_authorization_in_app():
    """
    Вывод информации о кол-ве пользователей, последний раз авторизировавшихся в приложении по годам.
    """

    print()
    print('Последний раз авторизировались в приложении:')
    total_amount = 0
    authorization2019 = 0
    authorization2020 = 0
    authorization2021 = 0
    authorization2022 = 0
    noneauthorization = 0
    table = pt()
    table.field_names = ['Страна', 'Тип пользователей', 'Всего в базе', 'в 2019 году', 'в 2020 году', 'в 2021 году',
                         'в 2022 году', 'Не авторизировались']
    for country in countries:
        table.add_rows([[country, 'Дилеры', amount_users_by_type(country, 'Дилер'),
                         last_authorization(2019, 'Дилер', country), last_authorization(2020, 'Дилер', country),
                         last_authorization(2021, 'Дилер', country), last_authorization(2022, 'Дилер', country),
                         last_authorization(None, 'Дилер', country)]])
        total_amount += amount_users_by_type(country, 'Дилер')
        authorization2019 += last_authorization(2019, 'Дилер', country)
        authorization2020 += last_authorization(2020, 'Дилер', country)
        authorization2021 += last_authorization(2021, 'Дилер', country)
        authorization2022 += last_authorization(2022, 'Дилер', country)
        noneauthorization += last_authorization(None, 'Дилер', country)

    table.add_rows([['Всего:', 'Дилеры', total_amount, authorization2019, authorization2020, authorization2021,
                     authorization2022, noneauthorization]])
    table.add_rows([['', '', '', '', '', '', '', '', ]])

    total_amount = 0
    authorization2019 = 0
    authorization2020 = 0
    authorization2021 = 0
    authorization2022 = 0
    noneauthorization = 0
    for country in countries:
        table.add_rows([[country, 'Монтажники', amount_users_by_type(country, 'Монтажник'),
                         last_authorization(2019, 'Монтажник', country), last_authorization(2020, 'Монтажник', country),
                         last_authorization(2021, 'Монтажник', country), last_authorization(2022, 'Монтажник', country),
                         last_authorization(None, 'Монтажник', country)]])
        total_amount += amount_users_by_type(country, 'Монтажник')
        authorization2019 += last_authorization(2019, 'Монтажник', country)
        authorization2020 += last_authorization(2020, 'Монтажник', country)
        authorization2021 += last_authorization(2021, 'Монтажник', country)
        authorization2022 += last_authorization(2022, 'Монтажник', country)
        noneauthorization += last_authorization(None, 'Монтажник', country)

    table.add_rows([['Всего:', 'Монтажники', total_amount, authorization2019, authorization2020, authorization2021,
                     authorization2022, noneauthorization]])

    print(table)


def period_data(start_date, end_date, user_type, country):
    """
    Подсчёт кол-ва пользователей, последний раз авторизировавшихся в приложении в течение конкретного периода.
    Параметры передаются при вызове функцией authorization_during_period.

    : param start_date: Дата начала периода
    : type start_date: str
    : param end_date: Дата конца периода
    : type end_date: str
    : param user_type: Тип пользователя (дилер или монтажник)
    : type user_type: str
    : param country: Страна
    : type country: str
    : return: кол-во авторизовавшихся за период
    : type return: int
    """

    authorization = 0
    start = datetime(int(start_date[6:]), int(start_date[3:5]), int(start_date[:2]))
    end = datetime(int(end_date[6:]), int(end_date[3:5]), int(end_date[:2]))

    for df_country, df_user_type, email, df_last_authorization in zip(df_users['Страна'], df_users['Тип пользователя'],
                                                                      df_users['E-Mail'],
                                                                      df_users['Последняя авторизация в приложении']):
        if df_last_authorization == '':
            continue
        else:
            row_struct_date = time.strptime(df_last_authorization, '%d.%m.%Y %H:%M:%S')
            row_date = time.strftime('%d.%m.%Y', row_struct_date)
            row_date = datetime(int(row_date[6:]), int(row_date[3:5]), int(row_date[:2]))
            if row_date >= start and row_date <= end:
                if email not in exclude_list:
                    if df_user_type == user_type and df_country == country:
                        authorization += 1

    return authorization


def authorization_during_period(start_date, end_date):
    """
    Вывод информации о кол-ве пользователей, последний раз авторизировавшихся в приложении в течение периода по странам.
    Параметры передаются при вызове функцией main в файле start c телом основной программы.

    : param start_date: Дата начала периода
    : type start_date: str
    : param end_date: Дата конца периода
    : type end_date: str
    : return: вывод итоговой таблицы
    """

    print()
    print('В течение указанного периода в приложении авторизировалось:')
    total_amount = 0
    table = pt()
    table.field_names = ['Страна', 'Тип пользователей', 'Авторизировалось пользователей']
    for country in countries:
        table.add_rows([[country, 'Дилеры', period_data(start_date, end_date, 'Дилер', country)]])
        total_amount += period_data(start_date, end_date, 'Дилер', country)
        table.add_rows([[country, 'Монтажники', period_data(start_date, end_date, 'Монтажник', country)]])
        total_amount += period_data(start_date, end_date, 'Монтажник', country)
        table.add_rows([['', '', '']])
    table.add_rows([['', '', '']])
    table.add_rows([['Всего:', '', total_amount]])

    print(table)


def sum_of_points(type_of_user, country):
    """
    Подсчёт кол-ва баллов у пользователей по странам.
    Параметры передаются при вызове функцией points_by_users_and_counties.

    : param type_of_user: Тип пользователя (дилер ии монтажник)
    : type type_of_user: str
    : param country: Страна
    : type country: str
    : return: кол-во пользователей в стране
    : type return: int
    """

    points = 0

    for points_by_scans, df_country, df_user_type, email, df_last_authorization in zip(df_users['Баллы'],
                                                                                       df_users['Страна'],
                                                                                       df_users['Тип пользователя'],
                                                                                       df_users['E-Mail'], df_users[
                                                                                           'Последняя авторизация в приложении']):
        if email not in exclude_list and points_by_scans != '':
            if df_user_type == type_of_user and df_country == country:
                points += int(points_by_scans)

    return points


def points_by_users_and_counties():
    """
    Вывод информации о кол-ве баллов у пользователей по странам.
    """

    print()
    print('Всего баллов на данный момент:')
    table = pt()
    table.field_names = ['Страна', 'Тип пользователей', 'Сумма баллов']
    for country in countries:
        total_points = 0
        table.add_rows([[country, 'Дилеры', sum_of_points('Дилер', country)]])
        total_points += sum_of_points('Дилер', country)
        table.add_rows([[country, 'Монтажники', sum_of_points('Монтажник', country)]])
        total_points += sum_of_points('Монтажник', country)
        table.add_rows([['Всего баллов:', '', total_points]])
        table.add_rows([['', '', '']])

    print(table)


def table_total_info():
    """
    Вывод данных о кол-ве сканировавших пользователей в текущем году.
    """

    print()
    print('В текущем году QR-коды сканировали:')
    table = pt()
    table.field_names = ['Страна', 'Тип пользователей', 'Сканировали', 'Кол-во пользователей']
    for country in countries:
        table.add_rows([[country, 'Дилеры', 'Сами себе', scanned_users(country, 'Дилер')],
                        ['', 'Монтажники', 'Сами себе', scanned_users(country, 'Монтажник')],
                        ['', 'Монтажники', 'Сканировали дилеру', scanned_users(country, 'Монтажник', False)],
                        ['', '', 'Итого:', scanned_users(country, 'Дилер') +
                         scanned_users(country, 'Монтажник') +
                         scanned_users(country, 'Монтажник', False)],
                        ['', '', '', '']])

    print(table)


def scanned_users(country, user_type, himself=True):
    """
    Подсчёт общего кол-ва сканировавших пользователей в текущем году.
    Функция вызывается при построении таблицы функцией table_total_info.
    Параметры передаются фукцией table_total_info.

    : param county: Страна
    : type country: str
    : param user_type: тип пользователя (дилер или монтажник)
    : type user_type: str
    : return: кол-во пользователей по ID
    : type return: int
    """

    count = set()
    if himself == True:
        if user_type == 'Дилер':
            for df_ID, df_country, df_user, df_adjuster_1 in zip(df_scans['UF_USER_ID'], df_scans['Страна'],
                                                                 df_scans['Сам себе'], df_scans['Монтажник.1']):
                if country == df_country and user_type == df_user and df_adjuster_1 != 'Монтажник':
                    count.add(df_ID)
        elif user_type == 'Монтажник':
            for df_ID, df_country, df_user in zip(df_scans['UF_USER_ID'], df_scans['Страна'], df_scans['Сам себе']):
                if country == df_country and user_type == df_user:
                    count.add(df_ID)
    else:
        for df_ID, df_country, df_adjuster_1 in zip(df_scans['Монтажник'], df_scans['Страна'], df_scans['Монтажник.1']):
            if country == df_country and df_adjuster_1 == 'Монтажник':
                count.add(df_ID)

    return len(count)


def total_amount_of_points_for_year(country, user_type):
    """
    Подсчёт общей суммы насканированных баллов за год.
    Параметры передаются при вызове функцией table_data_about_points.

    : param county: Страна
    : type country: str
    : param user_type: тип пользователя (дилер или монтажник)
    : type user_type: str
    : return: кол-во баллов
    : type return: int
    """

    amount_of_points = 0

    if user_type == 'Дилер':
        for df_country, df_points, df_user, df_adjuster_1 in zip(df_scans['Страна'], df_scans['UF_POINTS'],
                                                                 df_scans['Сам себе'], df_scans['Монтажник.1']):
            if df_country == country and df_user == user_type and df_adjuster_1 != 'Монтажник':
                amount_of_points += int(df_points)
        for df_country, df_points, df_user, df_adjuster_1 in zip(df_scans['Страна'], df_scans['UF_POINTS'],
                                                                 df_scans['Сам себе'], df_scans['Монтажник.1']):
            if country == df_country and user_type == df_user and df_adjuster_1 == 'Монтажник':
                amount_of_points += int(df_points)

    elif user_type == 'Монтажник':
        for df_country, df_points, df_user in zip(df_scans['Страна'], df_scans['UF_POINTS'], df_scans['Сам себе']):
            if df_country == country and df_user == user_type:
                amount_of_points += int(df_points)
        for df_country, df_points, df_adjuster_1 in zip(df_scans['Страна'], df_scans['UF_POINTS'],
                                                        df_scans['Монтажник.1']):
            if country == df_country and df_adjuster_1 == 'Монтажник':
                amount_of_points += int(df_points)

    return amount_of_points


def sum_of_points_per_period(country, user_type, start_date, end_date, himself=True):
    """
    Подсчёт суммы насканированных баллов за период.
    Параметры передаются при вызове функцией data_about_scans_during_period.

    : param country: Страна
    : type country: str
    : param user_type: Тип пользователя (дилер или монтажник)
    : type user_type: str
    : param start_date: Дата начала периода
    : type start_date: str
    : param end_date: Дата конца периода
    : type: end_date: str
    : param himself: Пользователь сканирует QR-код сам себе
    : type himself: boolean
    : return: кол-во баллов за периода
    : type return: int
    """

    amount_of_points_per_period = 0
    start = datetime(int(start_date[6:]), int(start_date[3:5]), int(start_date[:2]))
    end = datetime(int(end_date[6:]), int(end_date[3:5]), int(end_date[:2]))

    if himself == True:
        if user_type == 'Дилер':
            for day_of_scan, df_country, df_points, df_user, df_adjuster_1 in zip(df_scans['UF_CREATED_AT'],
                                                                                  df_scans['Страна'],
                                                                                  df_scans['UF_POINTS'],
                                                                                  df_scans['Сам себе'],
                                                                                  df_scans['Монтажник.1']):
                df_scan_struct_date = time.strptime(day_of_scan, '%d.%m.%Y %H:%M:%S')
                df_scan_date = time.strftime('%d.%m.%Y', df_scan_struct_date)
                df_scan_date = datetime(int(df_scan_date[6:]), int(df_scan_date[3:5]), int(df_scan_date[:2]))
                if df_scan_date >= start and df_scan_date <= end:
                    if df_country == country and df_user == user_type and df_adjuster_1 != 'Монтажник':
                        amount_of_points_per_period += int(df_points)

        elif user_type == 'Монтажник':
            for day_of_scan, df_country, df_points, df_user in zip(df_scans['UF_CREATED_AT'], df_scans['Страна'],
                                                                   df_scans['UF_POINTS'], df_scans['Сам себе']):
                df_scan_struct_date = time.strptime(day_of_scan, '%d.%m.%Y %H:%M:%S')
                df_scan_date = time.strftime('%d.%m.%Y', df_scan_struct_date)
                df_scan_date = datetime(int(df_scan_date[6:]), int(df_scan_date[3:5]), int(df_scan_date[:2]))
                if df_scan_date >= start and df_scan_date <= end:
                    if df_country == country and df_user == user_type:
                        amount_of_points_per_period += int(df_points)

    elif himself == False:
        for day_of_scan, df_country, df_points, df_adjuster_1 in zip(df_scans['UF_CREATED_AT'], df_scans['Страна'],
                                                                     df_scans['UF_POINTS'], df_scans['Монтажник.1']):
            df_scan_struct_date = time.strptime(day_of_scan, '%d.%m.%Y %H:%M:%S')
            df_scan_date = time.strftime('%d.%m.%Y', df_scan_struct_date)
            df_scan_date = datetime(int(df_scan_date[6:]), int(df_scan_date[3:5]), int(df_scan_date[:2]))
            if df_scan_date >= start and df_scan_date <= end:
                if country == df_country and df_adjuster_1 == 'Монтажник':
                    amount_of_points_per_period += int(df_points)

    return amount_of_points_per_period


def table_data_about_points():
    """
    Вывод данных по насканированным баллам.
    """

    print()
    print('В текущем году насканировано баллов:')
    table = pt()
    table.field_names = ['Страна', 'Тип пользователей', 'Насканировано баллов']
    for country in countries:
        table.add_rows([[country, 'Дилеры', total_amount_of_points_for_year(country, 'Дилер')],
                        ['', 'Монтажники', total_amount_of_points_for_year(country, 'Монтажник')],
                        ['', 'Итого:',
                         total_amount_of_points_for_year(country, 'Дилер') + total_amount_of_points_for_year(country,
                                                                                                             'Монтажник')],
                        ['', '', '']])

    print(table)


def top_users_by_scans(country, user_type):
    """
    ТОП дилеров / монтажников по сканам.

    : param country: Страна
    : type country: str
    : param user_type: Тип пользователя (дилер или монтажник)
    : type user_type: str
    : return: вывод таблицы
    """

    ''' Заполнение словаря-справочника "ID : Фамилия" '''
    for df_users_ID, df_users_surname in zip(df_users['ID'], df_users['Фамилия']):
        surname[df_users_ID] = df_users_surname

    top_users = {}  # словарь для ТОП пользователей
    print()
    if user_type == 'Дилер':
        print(country, ': ТОП дилеров по насканированным баллам: ')
        for df_ID, df_points, df_country, df_user_type in zip(df_scans['UF_USER_ID'], df_scans['UF_POINTS'],
                                                              df_scans['Страна'], df_scans['Сам себе']):
            if df_country == country and df_user_type == user_type:
                if df_ID not in top_users.keys():
                    top_users[df_ID] = int(df_points)
                else:
                    top_users[df_ID] += int(df_points)

        table = pt()
        table.field_names = ['ID пользователя', 'Фамилия', 'Сумма насканированных баллов']
        for row in sorted(top_users.items(), key=lambda x: x[1], reverse=True):
            table.add_rows([[row[0], surname.get(row[0]), row[1]]])

    elif user_type == 'Монтажник':
        print(country, ': ТОП монтажников по насканированным баллам: ')
        for df_ID, df_points, df_country, df_user_type in zip(df_scans['UF_USER_ID'], df_scans['UF_POINTS'],
                                                              df_scans['Страна'], df_scans['Сам себе']):
            if df_country == country and df_user_type == user_type:
                if df_ID not in top_users.keys():
                    top_users[df_ID] = int(df_points)
                else:
                    top_users[df_ID] += int(df_points)

        for df_ID, df_points, df_country, df_user_type in zip(df_scans['Монтажник'], df_scans['UF_POINTS'],
                                                              df_scans['Страна'], df_scans['Монтажник.1']):
            if df_country == country and df_user_type == 'Монтажник':
                if df_ID not in top_users.keys():
                    top_users[df_ID] = int(df_points)
                else:
                    top_users[df_ID] += int(df_points)

        table = pt()
        table.field_names = ['ID пользователя', 'Фамилия', 'Сумма насканированных баллов']
        for row in sorted(top_users.items(), key=lambda x: x[1], reverse=True):
            table.add_rows([[int(row[0]), surname.get(row[0]), row[1]]])

    table.add_rows([['Итого:', '', sum(top_users.values())]])
    print(table)


def scanned_users_per_period(country, user_type, start_date, end_date, himself=True):
    """
    Подсчёт общего кол-ва сканировавших пользователей за период.
    Параметры передаются при вызове функцией data_about_scans_during_period.

    : param country: Страна
    : type country: str
    : param user_type: Тип пользователя (дилер или монтажник)
    : type user_type: str
    : param start_date: Дата начала периода
    : type start_date: str
    : param end_date: Дата конца периода
    : type end_date: str
    : param himself: Пользователь сканирует QR-коды са себе
    : type hiself: boolean
    : return: кол-во пользователей за период
    : type return: int
    """

    count = set()
    start = datetime(int(start_date[6:]), int(start_date[3:5]), int(start_date[:2]))
    end = datetime(int(end_date[6:]), int(end_date[3:5]), int(end_date[:2]))
    if himself == True:
        if user_type == 'Дилер':
            for day_of_scan, df_ID, df_country, df_user, df_adjuster_1 in zip(df_scans['UF_CREATED_AT'],
                                                                              df_scans['UF_USER_ID'],
                                                                              df_scans['Страна'], df_scans['Сам себе'],
                                                                              df_scans['Монтажник.1']):
                df_scan_struct_date = time.strptime(day_of_scan, '%d.%m.%Y %H:%M:%S')
                df_scan_date = time.strftime('%d.%m.%Y', df_scan_struct_date)
                df_scan_date = datetime(int(df_scan_date[6:]), int(df_scan_date[3:5]), int(df_scan_date[:2]))
                if df_scan_date >= start and df_scan_date <= end:
                    if country == df_country and user_type == df_user and df_adjuster_1 != 'Монтажник':
                        count.add(df_ID)

        elif user_type == 'Монтажник':
            for day_of_scan, df_ID, df_country, df_user in zip(df_scans['UF_CREATED_AT'], df_scans['UF_USER_ID'],
                                                               df_scans['Страна'], df_scans['Сам себе']):
                df_scan_struct_date = time.strptime(day_of_scan, '%d.%m.%Y %H:%M:%S')
                df_scan_date = time.strftime('%d.%m.%Y', df_scan_struct_date)
                df_scan_date = datetime(int(df_scan_date[6:]), int(df_scan_date[3:5]), int(df_scan_date[:2]))
                if df_scan_date >= start and df_scan_date <= end:
                    if country == df_country and user_type == df_user:
                        count.add(df_ID)
    else:
        for day_of_scan, df_ID, df_country, df_adjuster_1 in zip(df_scans['UF_CREATED_AT'], df_scans['Монтажник'],
                                                                 df_scans['Страна'], df_scans['Монтажник.1']):
            df_scan_struct_date = time.strptime(day_of_scan, '%d.%m.%Y %H:%M:%S')
            df_scan_date = time.strftime('%d.%m.%Y', df_scan_struct_date)
            df_scan_date = datetime(int(df_scan_date[6:]), int(df_scan_date[3:5]), int(df_scan_date[:2]))
            if df_scan_date >= start and df_scan_date <= end:
                if country == df_country and df_adjuster_1 == 'Монтажник':
                    count.add(df_ID)

    return len(count)


def data_about_scans_during_period(start_date, end_date):
    """
    Вывод данных по пользователям и сканам за период.

    : param start_date: Дата начала периода
    : type start_date: str
    : param end_date: Дата конца периода
    : type end_date: str
    : return: вывод таблицы
    """

    ''' Расчёт дат предыдущего периода '''
    previous_start_struct = time.strftime('%d.%m.%Y', time.strptime(start_date, '%d.%m.%Y'))
    previous_start = datetime(int(previous_start_struct[6:]), int(previous_start_struct[3:5]),
                              int(previous_start_struct[:2]))
    previous_end_struct = time.strftime('%d.%m.%Y', time.strptime(end_date, '%d.%m.%Y'))
    previous_end = datetime(int(previous_end_struct[6:]), int(previous_end_struct[3:5]), int(previous_end_struct[:2]))
    time_delta = previous_end - previous_start + timedelta(days=1)
    previous_start = previous_start - time_delta
    previous_start = str(previous_start)[8:10] + '.' + str(previous_start)[5:7] + '.' + str(previous_start)[:4]
    previous_end = previous_end - time_delta
    previous_end = str(previous_end)[8:10] + '.' + str(previous_end)[5:7] + '.' + str(previous_end)[:4]

    print()
    print('За период с', start_date, 'по', end_date, 'сканировали:')

    table = pt()
    table.field_names = ['Страна',
                         'Пользователи',
                         'Сканировали:',
                         'Кол-во пользователей',
                         'Пользователей за предыдущий аналогичный период',
                         'Насканировали баллов']
    for country in countries:
        table.add_rows([[country,
                         'Дилеры',
                         'Сами себе',
                         scanned_users_per_period(country, 'Дилер', start_date, end_date, True),
                         scanned_users_per_period(country, 'Дилер', previous_start, previous_end, himself=True),
                         sum_of_points_per_period(country, 'Дилер', start_date, end_date) + sum_of_points_per_period(
                             country, 'Монтажник', start_date, end_date, himself=False)],
                        ['',
                         'Монтажники',
                         'Сами себе',
                         scanned_users_per_period(country, 'Монтажник', start_date, end_date, True),
                         scanned_users_per_period(country, 'Монтажник', previous_start, previous_end, himself=True),
                         sum_of_points_per_period(country, 'Монтажник', start_date, end_date)],
                        ['',
                         'Монтажники',
                         'Сканировали дилеру',
                         scanned_users_per_period(country, 'Монтажник', start_date, end_date, False),
                         scanned_users_per_period(country, 'Монтажник', previous_start, previous_end, False),
                         sum_of_points_per_period(country, 'Монтажник', start_date, end_date, himself=False)],
                        ['',
                         '',
                         'Итого:',
                         scanned_users_per_period(country, 'Дилер', start_date, end_date, True) +
                         scanned_users_per_period(country, 'Монтажник', start_date, end_date, True) +
                         scanned_users_per_period(country, 'Монтажник', start_date, end_date, False),
                         scanned_users_per_period(country, 'Дилер', previous_start, previous_end, True) +
                         scanned_users_per_period(country, 'Монтажник', previous_start, previous_end, True) +
                         scanned_users_per_period(country, 'Монтажник', previous_start, previous_end, False),
                         sum_of_points_per_period(country, 'Дилер', start_date, end_date) + sum_of_points_per_period(
                             country, 'Монтажник', start_date, end_date, himself=False) +
                         sum_of_points_per_period(country, 'Монтажник', start_date, end_date) +
                         sum_of_points_per_period(country, 'Монтажник', start_date, end_date, himself=False)],
                        ['',
                         '',
                         '',
                         '',
                         '',
                         '']])

    print(table)


def data_scanned_users_by_month(country, month, user_type, himself=True):
    """
    Пдсчёт кол-ва сканировавших пользователей по месяцам.
    Параметры передаются при вызове функцией table_scanned_users_by_months.

    : param country: Страна
    : type counry: str
    : param month: месяц
    : type month: str
    : param user_type: Тип пользователя (диле или монтажник)
    : type user_type: str
    : param himself: Пользователь сканировал QR-код сам себе
    : type himself: boolean
    : return: кол-во пользователей за месяц
    : type return: int
    """

    count = set()
    if himself == True:
        if user_type == 'Дилер':
            for df_month_of_scan, df_ID, df_country, df_user, df_adjuster_1 in zip(df_scans['Месяц'],
                                                                                   df_scans['UF_USER_ID'],
                                                                                   df_scans['Страна'],
                                                                                   df_scans['Сам себе'],
                                                                                   df_scans['Монтажник.1']):
                if df_month_of_scan == month:
                    if country == df_country and user_type == df_user and df_adjuster_1 != 'Монтажник':
                        count.add(df_ID)

        elif user_type == 'Монтажник':
            for df_month_of_scan, df_ID, df_country, df_user in zip(df_scans['Месяц'], df_scans['UF_USER_ID'],
                                                                    df_scans['Страна'], df_scans['Сам себе']):
                if df_month_of_scan == month:
                    if country == df_country and user_type == df_user:
                        count.add(df_ID)
    else:
        for df_month_of_scan, df_ID, df_country, df_adjuster_1 in zip(df_scans['Месяц'], df_scans['Монтажник'],
                                                                      df_scans['Страна'], df_scans['Монтажник.1']):
            if df_month_of_scan == month:
                if country == df_country and df_adjuster_1 == 'Монтажник':
                    count.add(df_ID)

    return len(count)


def table_scanned_users_by_months():
    """
    Вывод таблицы по кол-ву сканировавших пользователей по странам и месяцам.
    """

    print()
    print('В текущем году сканировало пользователей:')
    table = pt()
    table.field_names = ['Страна', 'Тип пользователей', 'Сканировали']
    for country in countries:
        table.add_row([country, 'Дилеры', 'Сами себе'])
        table.add_row(['', 'Монтажники', 'Сами себе'])
        table.add_row(['', 'Монтажники', 'Сканировали дилеру'])
        table.add_row(['', '', 'Итого:'])
        table.add_row(['', '', ''])

    for month in months:
        table.add_column(month, [data_scanned_users_by_month('Россия', month, 'Дилер', himself=True),
                                 data_scanned_users_by_month('Россия', month, 'Монтажник', himself=True),
                                 data_scanned_users_by_month('Россия', month, 'Монтажник', himself=False),
                                 data_scanned_users_by_month('Россия', month, 'Дилер',
                                                             himself=True) + data_scanned_users_by_month('Россия',
                                                                                                         month,
                                                                                                         'Монтажник',
                                                                                                         himself=True) + data_scanned_users_by_month(
                                     'Россия', month, 'Монтажник', himself=False),
                                 '',
                                 data_scanned_users_by_month('Украина', month, 'Дилер', himself=True),
                                 data_scanned_users_by_month('Украина', month, 'Монтажник', himself=True),
                                 data_scanned_users_by_month('Украина', month, 'Монтажник', himself=False),
                                 data_scanned_users_by_month('Украина', month, 'Дилер',
                                                             himself=True) + data_scanned_users_by_month('Украина',
                                                                                                         month,
                                                                                                         'Монтажник',
                                                                                                         himself=True) + data_scanned_users_by_month(
                                     'Украина', month, 'Монтажник', himself=False),
                                 '',
                                 data_scanned_users_by_month('Казахстан', month, 'Дилер', himself=True),
                                 data_scanned_users_by_month('Казахстан', month, 'Монтажник', himself=True),
                                 data_scanned_users_by_month('Казахстан', month, 'Монтажник', himself=False),
                                 data_scanned_users_by_month('Казахстан', month, 'Дилер',
                                                             himself=True) + data_scanned_users_by_month('Казахстан',
                                                                                                         month,
                                                                                                         'Монтажник',
                                                                                                         himself=True) + data_scanned_users_by_month(
                                     'Казахстан', month, 'Монтажник', himself=False),
                                 '',
                                 data_scanned_users_by_month('Беларусь', month, 'Дилер', himself=True),
                                 data_scanned_users_by_month('Беларусь', month, 'Монтажник', himself=True),
                                 data_scanned_users_by_month('Беларусь', month, 'Монтажник', himself=False),
                                 data_scanned_users_by_month('Беларусь', month, 'Дилер',
                                                             himself=True) + data_scanned_users_by_month('Беларусь',
                                                                                                         month,
                                                                                                         'Монтажник',
                                                                                                         himself=True) + data_scanned_users_by_month(
                                     'Беларусь', month, 'Монтажник', himself=False),
                                 ''])

    print(table)


def finish():
    print('Всего хорошего!')
    pass
