import tkinter as tk
from tkinter import ttk,messagebox
import pyodbc

def get_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=Exam;"
        "Trusted_connection=yes;"
    )


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Обувной магазин")
        
        try:
            self.iconphoto(True, tk.PhotoImage(file="Icon.png"))
        except Exception:
            pass

        self.user = "Гость"
        self.role = "Гость"
        self.sort_dir = "ASC"
        self.show_login()
    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear()
        self.title("Авторизация")
        self.geometry("300x200")
        self.state("normal")

        tk.Label(self,text="Обувной магазин").pack(pady=10)

        tk.Label(self,text="Логин").pack()
        self.login_entry = tk.Entry(self)
        self.login_entry.pack()

        tk.Label(self,text="Пароль").pack()
        self.password_entry = tk.Entry(self)
        self.password_entry.pack()

        tk.Button(self,text="Войти",command=self.do_login).pack(pady=5)
        tk.Button(self,text="Войти как гость",command=self.do_guest).pack()

    def do_guest(self):
        self.user = "Гость"
        self.role = "Гость"
        self.show_product()
    
    def do_login(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not login or not password:
            messagebox.showerror("Ошибка","введите логин и пароль")
            return
        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                select u.Name + ' ' + u.Surname, r.Name
                           from dbo.[User] u
                           join dbo.Role r on u.RoleId = r.Id
                           where login = ? and password = ?
                           """, (login,password))
            row = cursor.fetchone()
            conn.close()

            if row:
                self.user,self.role = row
                self.show_product()
            else:
                messagebox.showerror("Ошибка","неправвильный логин или пароль")
        except Exception as e:
            messagebox.showerror("Ошибка бд", str(e))

    def show_product(self):
        self.clear()
        self.title("Список продуктов")
        self.state("zoomed")

        top = tk.Frame(self)
        top.pack(fill="x", pady=3)

        tk.Label(top,text="Список товаров").pack(padx=3,pady=3)

        tk.Button(top,text="Выйти",command=self.show_login).pack(side="right")
        tk.Label(top, text= f"{self.role} {self.user}").pack(side="right")


        if self.role in ("Администратор","Менеджер"):
            filt = tk.Frame(self)
            filt.pack()

            tk.Label(filt,text="Поиск").pack()
            self.search_entry = tk.Entry(filt)
            self.search_entry.bind("<KeyRelease>", lambda e: self.load_product())
            self.search_entry.pack()

            tk.Button(filt,text="Сортировака по цене",command=self.toggle_sort).pack()

            tk.Button(filt,text="удалить").pack()

        cols = ("Id", "Article", "Name", "Categoru", "Producer", "Provider", "Price", "Amount", "discount")
        self.product_tree = ttk.Treeview(self, columns=cols, show="headings")

        for c in cols:
            self.product_tree.column(c, width=130)
            self.product_tree.heading(c, text=c)

        self.product_tree.pack(fill="both", expand=True, padx=5,pady=5)
        self.load_product()

    def load_product(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        query = """
            SELECT p.Id, p.Article, p.Name, c.Name, pr.Name, pv.Name, p.Price, p.AmountInStock, p.Discount
            FROM dbo.Product p
            JOIN dbo.Category c ON p.CategoryId = c.Id
            JOIN dbo.Producer pr ON p.ProducerId = pr.Id
            JOIN dbo.Provider pv ON p.ProviderId = pv.Id
        """
        params = []

        if self.role in ("Администратор", "Менеджер"):
            text = self.search_entry.get().strip()
            if text:
                m = "%" + text + "%"
                query += """
                    WHERE p.Article LIKE ?
                    OR p.Name LIKE ?
                    OR c.Name LIKE ?
                    OR pr.Name LIKE ?
                    OR pv.Name LIKE ?
                """
                params = [m, m, m, m, m]
            query += f" ORDER BY p.Price {self.sort_dir}"
        else:
            query += " ORDER BY p.Name"

        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                pid, article, name, category, producer, provider, price, amount, discount = row
                discount = discount or 0
                price = round(float(price), 2)

                if discount > 0:
                    new_price = round(price * (1 - discount / 100), 2)
                    price_str = f"{price} -> {new_price}"
                else:
                    price_str = str(price)

                tag = ""
                if amount == 0:
                    tag = "empty"
                elif discount > 15:
                    tag = "discount"

                self.product_tree.insert(
                    "",
                    "end",
                    values=(pid, article, name, category, producer, provider, price_str, amount, f"{discount}%"),
                    tags=(tag,)
                )

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def toggle_sort(self):
        self.sort_dir = "DESC" if self.sort_dir == "ASC" else "ASC"
        self.load_product()



if __name__ == "__main__":
    App().mainloop()