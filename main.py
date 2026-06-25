import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os

# --- НАСТРОЙКИ СТИЛЕЙ ---
COLORS = {
    'main_bg': '#FFFFFF',
    'sec_bg': '#7FFF00',
    'accent': '#00FA9A',
    'discount_bg': '#2E8B57',
    'text': '#000000'
}
FONT_FAMILY = 'Times New Roman'
FONT = (FONT_FAMILY, 12)
FONT_BOLD = (FONT_FAMILY, 12, 'bold')
DB_NAME = 'database.db'


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()

    def get_products(self, search="", category=""):
        query = "SELECT article, name, price, discount, stock, category FROM products WHERE 1=1"
        params = []
        if search:
            query += " AND (name LIKE ? OR article LIKE ?)"
            params.extend([f"%{search}%"] * 2)
        if category:
            query += " AND category = ?"
            params.append(category)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_orders(self):
        self.cursor.execute('''SELECT o.id, o.order_date, o.status, o.client_name, p.address 
                               FROM orders o JOIN pickup_points p ON o.pickup_point_id = p.id''')
        return self.cursor.fetchall()

    def auth_user(self, login, password):
        self.cursor.execute("SELECT role, full_name FROM users WHERE login=? AND password=?", (login, password))
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()


db = Database()


# --- ОКНО АВТОРИЗАЦИИ ---
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Авторизация | ООО «Обувь»")
        self.geometry("400x300")
        self.configure(bg=COLORS['main_bg'])
        self._set_icon()

        tk.Label(self, text="Вход в систему", font=FONT_BOLD, bg=COLORS['main_bg']).pack(pady=20)

        self.frame = tk.Frame(self, bg=COLORS['sec_bg'], padx=20, pady=20)
        self.frame.pack(padx=30, pady=10, fill='x')

        tk.Label(self.frame, text="Логин:", bg=COLORS['sec_bg'], font=FONT).pack(anchor='w')
        self.entry_login = tk.Entry(self.frame, font=FONT)
        self.entry_login.pack(fill='x', pady=5)

        tk.Label(self.frame, text="Пароль:", bg=COLORS['sec_bg'], font=FONT).pack(anchor='w')
        self.entry_pass = tk.Entry(self.frame, show="*", font=FONT)
        self.entry_pass.pack(fill='x', pady=5)

        tk.Button(self.frame, text="Войти", bg=COLORS['accent'], font=FONT_BOLD, command=self.login).pack(fill='x',
                                                                                                          pady=10)
        tk.Button(self, text="Просмотр товаров (Гость)", bg=COLORS['main_bg'], font=FONT, relief='flat',
                  command=self.guest_mode).pack(pady=10)

    def _set_icon(self):
        if os.path.exists('resources/icon.ico'):
            self.iconbitmap('resources/icon.ico')

    def login(self):
        res = db.auth_user(self.entry_login.get(), self.entry_pass.get())
        if res:
            self.destroy()
            MainWindow(res[0], res[1])
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def guest_mode(self):
        self.destroy()
        MainWindow("Гость", "Гость")


# --- ГЛАВНОЕ ОКНО ---
class MainWindow(tk.Tk):
    def __init__(self, role, full_name):
        super().__init__()
        self.role = role
        self.full_name = full_name
        self.title(f"ООО «Обувь» - {self.role}")
        self.geometry("1000x600")
        self.configure(bg=COLORS['main_bg'])

        if os.path.exists('resources/icon.ico'): self.iconbitmap('resources/icon.ico')

        self._build_header()
        self._build_navigation()

        # По умолчанию открываем товары
        self.show_products()

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS['sec_bg'], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        if os.path.exists('resources/logo.png'):
            self.logo_img = tk.PhotoImage(file='resources/logo.png')
            tk.Label(header, image=self.logo_img, bg=COLORS['sec_bg']).pack(side='left', padx=10)

        tk.Label(header, text=f"Пользователь: {self.full_name} | Роль: {self.role}",
                 font=FONT_BOLD, bg=COLORS['sec_bg']).pack(side='right', padx=20)

    def _build_navigation(self):
        nav = tk.Frame(self, bg=COLORS['main_bg'])
        nav.pack(fill='x', pady=5)

        tk.Button(nav, text="Товары", bg=COLORS['accent'], font=FONT, command=self.show_products).pack(side='left',
                                                                                                       padx=5)

        if self.role in ["Менеджер", "Администратор"]:
            tk.Button(nav, text="Заказы", bg=COLORS['accent'], font=FONT, command=self.show_orders).pack(side='left',
                                                                                                         padx=5)

    def clear_content(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame) and widget != self.winfo_children()[0] and widget != self.winfo_children()[
                1]:
                widget.destroy()

    def show_products(self):
        self.clear_content()
        ProductsFrame(self, self.role)

    def show_orders(self):
        self.clear_content()
        OrdersFrame(self, self.role)


# --- ФРЕЙМ ТОВАРОВ ---
class ProductsFrame(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=COLORS['main_bg'])
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.role = role

        if self.role in ["Менеджер", "Администратор"]:
            self._build_filters()

        if self.role == "Администратор":
            self._build_crud_buttons()

        self._build_tree()
        self.load_data()

    def _build_filters(self):
        f = tk.Frame(self, bg=COLORS['main_bg'])
        f.pack(fill='x', pady=5)

        tk.Label(f, text="Поиск:", bg=COLORS['main_bg'], font=FONT).pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda name, index, mode: self.load_data())
        tk.Entry(f, textvariable=self.search_var, font=FONT).pack(side='left', padx=5)

        tk.Label(f, text="Категория:", bg=COLORS['main_bg'], font=FONT).pack(side='left', padx=(20, 0))
        self.cat_var = tk.StringVar()
        self.cat_var.set("Все")
        self.cat_var.trace('w', lambda name, index, mode: self.load_data())
        ttk.Combobox(f, textvariable=self.cat_var, values=["Все", "Мужская обувь", "Женская обувь"], font=FONT,
                     state='readonly').pack(side='left', padx=5)

    def _build_crud_buttons(self):
        f = tk.Frame(self, bg=COLORS['main_bg'])
        f.pack(fill='x', pady=5)
        tk.Button(f, text="Добавить", bg=COLORS['accent'], font=FONT).pack(side='left', padx=5)
        tk.Button(f, text="Редактировать", bg=COLORS['accent'], font=FONT).pack(side='left', padx=5)
        tk.Button(f, text="Удалить", bg=COLORS['accent'], font=FONT, command=self.delete_product).pack(side='left',
                                                                                                       padx=5)

    def _build_tree(self):
        cols = ("article", "name", "price", "discount", "stock", "category")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=15)

        style = ttk.Style()
        style.configure("Treeview", font=FONT, rowheight=25, background=COLORS['main_bg'])
        style.configure("Treeview.Heading", font=FONT_BOLD)
        style.map('Treeview', background=[('selected', COLORS['accent'])])

        # Тег для скидки > 15%
        self.tree.tag_configure('high_discount', background=COLORS['discount_bg'], foreground='white')

        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=120)

        self.tree.pack(fill='both', expand=True)

    def load_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)

        search = self.search_var.get() if self.role in ["Менеджер", "Администратор"] else ""
        cat = self.cat_var.get() if self.role in ["Менеджер", "Администратор"] and self.cat_var.get() != "Все" else ""

        data = db.get_products(search, cat)
        for row in data:
            tags = ('high_discount',) if row[3] > 15 else ()
            self.tree.insert('', 'end', values=row, tags=tags)

    def delete_product(self):
        selected = self.tree.selection()
        if not selected: return
        article = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить товар {article}?"):
            db.cursor.execute("DELETE FROM products WHERE article=?", (article,))
            db.conn.commit()
            self.load_data()


# --- ФРЕЙМ ЗАКАЗОВ ---
class OrdersFrame(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=COLORS['main_bg'])
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.role = role

        if self.role == "Администратор":
            f = tk.Frame(self, bg=COLORS['main_bg'])
            f.pack(fill='x', pady=5)
            tk.Button(f, text="Добавить заказ", bg=COLORS['accent'], font=FONT).pack(side='left', padx=5)

        cols = ("id", "date", "status", "client", "address")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=15)
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=150)
        self.tree.pack(fill='both', expand=True)

        self.load_data()

    def load_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for row in db.get_orders():
            self.tree.insert('', 'end', values=row)


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
    db.close()