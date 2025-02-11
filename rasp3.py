import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox

class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расписание")

        self.group_buttons_frame = tk.Frame(root)
        self.group_buttons_frame.pack()

        self.load_group_buttons()

        self.tree = ttk.Treeview(root, columns=("Время начала", "Время окончания", "Преподаватель", "Дисциплина", "День недели"), show="headings")
        self.tree.heading("Время начала", text="Время начала")
        self.tree.heading("Время окончания", text="Время окончания")
        self.tree.heading("Преподаватель", text="Преподаватель")
        self.tree.heading("Дисциплина", text="Дисциплина")
        self.tree.heading("День недели", text="День недели")
        self.tree.pack()

        # Add some styling for better readability (optional)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        style.configure("Treeview", font=('Arial', 9))


    def load_group_buttons(self):
        try:
            conn = sqlite3.connect('schedule.db')
            cursor = conn.cursor()

            # Assuming you have a table named 'groups' with a column named 'group_name'
            cursor.execute("SELECT id, group_name FROM groups ORDER BY group_name")  # Modified query
            groups = cursor.fetchall()

            if not groups:
                messagebox.showinfo("Информация", "Группы не найдены в базе данных.")
                return

            for group in groups:
                group_id = group[0]
                group_name = group[1]  # Extract the group name from the tuple
                button = tk.Button(self.group_buttons_frame, text=group_name, command=lambda num=group_id: self.show_schedule(num))  # Use lambda to capture the value
                button.pack(side=tk.LEFT, padx=5, pady=5)  # Arrange buttons horizontally

            conn.close()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            messagebox.showerror("Ошибка", f"Ошибка чтения групп из базы данных: {e}")


    def show_schedule(self, group_id):
        self.populate_schedule(group_id)


    def populate_schedule(self, group_id):
        # Clear previous schedule
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = sqlite3.connect('schedule.db')
            cursor = conn.cursor()

            # SQL Query (using the database schema provided)
            query = """
            SELECT time_start, time_end, name, disc_name, dow
            FROM timing
            INNER JOIN prepods ON timing.prep_id = prepods.id
            INNER JOIN disciplines ON timing.disc_id = disciplines.id
            INNER JOIN week ON timing.dow_id = week.id
            WHERE group_id=?
            ORDER BY timing.dow_id
            """

            cursor.execute(query, (group_id,))
            rows = cursor.fetchall()

            if not rows:
                messagebox.showinfo("Информация", "Расписание для данной группы не найдено.")
                conn.close()
                return

            for row in rows:
                self.tree.insert("", tk.END, values=row)

            conn.close()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            messagebox.showerror("Ошибка", f"Ошибка чтения расписания из базы данных: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleApp(root)
    root.mainloop()
