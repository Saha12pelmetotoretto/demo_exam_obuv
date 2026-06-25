import pandas as pd
import sqlite3
import os

DB_NAME = 'database.db'
DATA_DIR = 'data'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS pickup_points (id INTEGER PRIMARY KEY AUTOINCREMENT, address TEXT);
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, full_name TEXT, login TEXT, password TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, article TEXT, name TEXT, unit TEXT, price REAL, supplier TEXT, manufacturer TEXT, category TEXT, discount INTEGER, stock INTEGER, description TEXT, image_path TEXT);
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_date TEXT, delivery_date TEXT, pickup_point_id INTEGER, client_name TEXT, pickup_code TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, article TEXT, quantity INTEGER);
    ''')
    conn.commit()
    return conn


def parse_order_items(items_str):
    parts = [p.strip() for p in str(items_str).split(',')]
    return [(parts[i], int(parts[i + 1])) for i in range(0, len(parts), 2) if i + 1 < len(parts)]


def import_data():
    conn = init_db()
    cursor = conn.cursor()

    # 1. Пункты выдачи
    df_points = pd.read_excel(os.path.join(DATA_DIR, 'Пункты выдачи_import.xlsx'))
    for _, row in df_points.iterrows():
        cursor.execute("INSERT INTO pickup_points (address) VALUES (?)", (row.iloc[0],))

    # 2. Пользователи
    df_users = pd.read_excel(os.path.join(DATA_DIR, 'user_import.xlsx'))
    for _, row in df_users.iterrows():
        cursor.execute("INSERT INTO users (role, full_name, login, password) VALUES (?, ?, ?, ?)",
                       (row['Роль сотрудника'], row['ФИО'], row['Логин'], row['Пароль']))

    # 3. Товары
    df_products = pd.read_excel(os.path.join(DATA_DIR, 'Tovar.xlsx'))
    for _, row in df_products.iterrows():
        cursor.execute('''INSERT INTO products 
            (article, name, unit, price, supplier, manufacturer, category, discount, stock, description, image_path) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (row['Артикул'], row['Наименование товара'], row['Единица измерения'], row['Цена'],
                        row['Поставщик'], row['Производитель'], row['Категория товара'], row['Действующая скидка'],
                        row['Кол-во на складе'], row['Описание товара'], str(row['Фото'])))

    # 4. Заказы и состав заказов
    df_orders = pd.read_excel(os.path.join(DATA_DIR, 'Заказ_import.xlsx'))
    for _, row in df_orders.iterrows():
        cursor.execute('''INSERT INTO orders 
            (id, order_date, delivery_date, pickup_point_id, client_name, pickup_code, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (row['Номер заказа'], str(row['Дата заказа']), str(row['Дата доставки']),
                        int(row['Адрес пункта выдачи']), row['ФИО авторизированного клиента'],
                        row['Код для получения'], row['Статус заказа']))

        for article, qty in parse_order_items(row['Артикул заказа']):
            cursor.execute("INSERT INTO order_items (order_id, article, quantity) VALUES (?, ?, ?)",
                           (row['Номер заказа'], article, qty))

    conn.commit()
    conn.close()
    print("База данных успешно создана и заполнена!")


if __name__ == "__main__":
    import_data()