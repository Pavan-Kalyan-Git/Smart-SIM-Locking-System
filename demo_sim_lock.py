# demo_sim_lock.py

import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import time
import random

# ---------------- DATABASE ----------------
conn = sqlite3.connect('demo_lock.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (pwd TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS fingerprints (id INTEGER)''')
conn.commit()

# ---------------- SIMULATION ----------------
def motor_open():
    status.config(text="🔓 Opening...", fg="green")
    root.update()
    time.sleep(1)
    status.config(text="✅ OPENED", fg="green")

def motor_close():
    status.config(text="🔒 Closing...", fg="red")
    root.update()
    time.sleep(1)
    status.config(text="🔒 LOCKED", fg="red")

def fake_fingerprint():
    return random.choice([True, False, True])

# ---------------- FUNCTIONS ----------------
def enroll_fingerprint():
    pos = simpledialog.askinteger("Enroll", "Enter ID:")
    if pos:
        cursor.execute("INSERT INTO fingerprints VALUES (?)", (pos,))
        conn.commit()
        messagebox.showinfo("Success", "Fingerprint stored (Demo)")

def delete_fingerprint():
    pos = simpledialog.askinteger("Delete", "Enter ID:")
    if pos:
        cursor.execute("DELETE FROM fingerprints WHERE id=?", (pos,))
        conn.commit()

def set_password():
    pwd = simpledialog.askstring("Set", "Enter:", show='*')
    if pwd:
        cursor.execute("DELETE FROM passwords")
        cursor.execute("INSERT INTO passwords VALUES (?)", (pwd,))
        conn.commit()

def change_password():
    set_password()

def delete_password():
    cursor.execute("DELETE FROM passwords")
    conn.commit()

def auth_open():
    if fake_fingerprint():
        motor_open()
        messagebox.showinfo("Access", "Fingerprint OK (Demo)")
        return

    cursor.execute("SELECT pwd FROM passwords LIMIT 1")
    row = cursor.fetchone()
    if row:
        pwd = simpledialog.askstring("Password", "Enter:", show='*')
        if pwd == row[0]:
            motor_open()
        else:
            messagebox.showerror("Error", "Wrong password")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Smart SIM Lock (Demo)")
root.geometry("400x500")

tk.Label(root, text="Smart SIM Lock - Demo", font=('Arial', 18)).pack(pady=20)

status = tk.Label(root, text="🔒 LOCKED", font=('Arial', 12))
status.pack(pady=10)

tk.Button(root, text="OPEN", command=auth_open,
          bg="green", fg="white", height=2, width=15).pack(pady=10)

tk.Button(root, text="CLOSE", command=motor_close,
          bg="red", fg="white", height=2, width=15).pack(pady=10)

tk.Button(root, text="Enroll Fingerprint", command=enroll_fingerprint).pack(pady=5)
tk.Button(root, text="Delete Fingerprint", command=delete_fingerprint).pack(pady=5)

tk.Button(root, text="Change Password", command=change_password).pack(pady=5)
tk.Button(root, text="Delete Password", command=delete_password).pack(pady=5)

root.mainloop()

conn.close()