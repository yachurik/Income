import sqlite3
from datetime import datetime
from config import DATABASE

# Категории доходов и расходов
income_categories = [("Зарплата",), ("Аванс",), ("Премия",), ("Другое",)]
expense_categories = [("Аренда",), ("Продукты",), ("Транспорт",), ("Развлечения",), ("Другое",)]

class DB_Manager:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute('''DROP TABLE IF EXISTS income''')
        self.cursor.execute('''DROP TABLE IF EXISTS expense''')
        self.cursor.execute('''DROP TABLE IF EXISTS income_categories''')
        self.cursor.execute('''DROP TABLE IF EXISTS expense_categories''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS income (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                amount REAL NOT NULL,
                                description TEXT,
                                date TEXT
                              )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS expense (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                amount REAL NOT NULL,
                                category TEXT,
                                description TEXT,
                                date TEXT
                              )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS income_categories (
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL
                              )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS expense_categories (
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL
                              )''')
        self.conn.commit()

    def insert_income(self, data):
        try:
            sql = '''INSERT INTO income (user_id, amount, description, date) VALUES (?, ?, ?, ?)'''
            self.cursor.executemany(sql, data)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting income: {e}")
            return False

    def insert_expense(self, data):
        try:
            sql = '''INSERT INTO expense (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)'''
            self.cursor.executemany(sql, data)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting expense: {e}")
            return False

    def get_records(self, user_id):
        try:
            sql = '''
                SELECT id, user_id, amount, description, date, 'income' as type FROM income WHERE user_id=?
                UNION ALL
                SELECT id, user_id, amount, category || ' - ' || description as description, date, 'expense' as type FROM expense WHERE user_id=?
            '''
            self.cursor.execute(sql, (user_id, user_id))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching records: {e}")
            return []

    def delete_record(self, record_id):
        try:
            sql_income = '''DELETE FROM income WHERE id=?'''
            sql_expense = '''DELETE FROM expense WHERE id=?'''
            self.cursor.execute(sql_income, (record_id,))
            self.cursor.execute(sql_expense, (record_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting record: {e}")
            return False

    def get_expense_categories(self):
        try:
            sql = '''SELECT DISTINCT category FROM expense'''
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching expense categories: {e}")
            return []

    def update_income(self, data, income_id):
        try:
            sql = '''UPDATE income SET user_id=?, amount=?, description=? WHERE id=?'''
            self.cursor.execute(sql, (data[0], data[1], data[2], income_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating income: {e}")
            return False

    def update_expense(self, data, expense_id):
        try:
            sql = '''UPDATE expense SET user_id=?, amount=?, category=?, description=? WHERE id=?'''
            self.cursor.execute(sql, (data[0], data[1], data[2], data[3], expense_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating expense: {e}")
            return False

    def default_insert(self):
        try:
            self.cursor.executemany('INSERT INTO income_categories (name) VALUES (?)', income_categories)
            self.cursor.executemany('INSERT INTO expense_categories (name) VALUES (?)', expense_categories)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error inserting default categories: {e}")

# Example of usage
if __name__ == "__main__":
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
