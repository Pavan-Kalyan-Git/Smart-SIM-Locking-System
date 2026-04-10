# smart_sim_lock.py

import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import time

# Hardware imports
from pyfingerprint.pyfingerprint import PyFingerprint
import RPi.GPIO as GPIO

# ---------------- GPIO SETUP ----------------
GPIO.setmode(GPIO.BCM)
IN1, IN2, IN3, IN4 = 17, 18, 27, 22

for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)

halfstep_seq = [
    [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
    [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
]

motor_running = False

# ---------------- MOTOR CONTROL ----------------
def motor_open():
    global motor_running
    if motor_running:
        return
    motor_running = True
    try:
        for _ in range(512):
            for step in range(8):
                for pin in range(4):
                    GPIO.output([IN1, IN2, IN3, IN4][pin], halfstep_seq[step][pin])
                time.sleep(0.001)
    finally:
        motor_running = False

def motor_close():
    global motor_running
    if motor_running:
        return
    motor_running = True
    try:
        for _ in range(512):
            for step in range(7, -1, -1):
                for pin in range(4):
                    GPIO.output([IN1, IN2, IN3, IN4][pin], halfstep_seq[step][pin])
                time.sleep(0.001)
    finally:
        motor_running = False

# ---------------- FINGERPRINT ----------------
try:
    finger = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)
    if not finger.verifyPassword():
        raise Exception("Sensor error")
except:
    finger = None

# ---------------- DATABASE ----------------
conn = sqlite3.connect('smart_lock.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (pwd TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS fingerprints (id INTEGER)''')
conn.commit()

# ---------------- FUNCTIONS ----------------
def enroll_fingerprint():
    if not finger:
        messagebox.showerror("Error", "Sensor not connected")
        return

    messagebox.showinfo("Enroll", "Place finger twice")

    while finger.readImage(): pass
    finger.convertImage(0x01)
    finger.createTemplate()

    messagebox.showinfo("Scan Again", "Place same finger again")
    time.sleep(2)

    while finger.readImage(): pass
    finger.convertImage(0x02)
    finger.createTemplate()

    pos = simpledialog.askinteger("ID", "Enter ID (1-10):")
    if finger.storeTemplate(pos) == 0:
        cursor.execute("INSERT INTO fingerprints VALUES (?)", (pos,))
        conn.commit()
        messagebox.showinfo("Success", "Fingerprint stored")

def delete_fingerprint():
    pos = simpledialog.askinteger("Delete", "Enter ID:")
    if pos and finger:
        finger.deleteTemplate(pos)
        cursor.execute("DELETE FROM fingerprints WHERE id=?", (pos,))
        conn.commit()
        messagebox.showinfo("Deleted", "Fingerprint removed")

def set_password():
    pwd = simpledialog.askstring("Password", "Enter new:", show='*')
    if pwd:
        cursor.execute("DELETE FROM passwords")
        cursor.execute("INSERT INTO passwords VALUES (?)", (pwd,))
        conn.commit()

def change_password():
    cursor.execute("SELECT pwd FROM passwords LIMIT 1")
    row = cursor.fetchone()
    if row:
        old = simpledialog.askstring("Old", "Enter old:", show='*')
        if old == row[0]:
            set_password()
        else:
            messagebox.showerror("Error", "Wrong password")
    else:
        set_password()

def delete_password():
    cursor.execute("DELETE FROM passwords")
    conn.commit()

def auth_open():
    if finger:
        if not finger.readImage():
            if finger.convertImage(0x01) == 0:
                if finger.searchTemplate() == 0:
                    motor_open()
                    messagebox.showinfo("Access", "Fingerprint OK")
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
root.title("Smart SIM Lock")
root.geometry("400x500")

tk.Label(root, text="Smart SIM Lock", font=('Arial', 18)).pack(pady=20)

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
GPIO.cleanup()