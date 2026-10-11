import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import sqlite3
import serial
import time
from PIL import Image, ImageTk  # For logo image (pip install pillow)
from datetime import datetime, timedelta
import pytz  # make sure it's installed (pip install pytz)
import smtplib
from email.mime.text import MIMEText
import os
from tkinter import Tk, Label, filedialog, messagebox
from PIL import Image, ImageTk
from shutil import copyfile
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tkinter import filedialog, messagebox


#Timezone / IST
ist = pytz.timezone('Asia/Kolkata')
def now_ist():
    return datetime.now(ist)

def fmt_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

#SMTP SETTINGS
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "yash68225@gmail.com"
SENDER_APP_PASSWORD = "tzxu eyvk ixgg hava"

def send_email(to_email, subject, body):
    if not to_email:
        print("No recipient email provided — skipping email.")
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False

def send_welcome_email(student_name, student_email):
    subject = "Welcome to SmartShelf – Account Registered"
    body = f"""Dear {student_name},

Welcome! Your student account has been registered with SmartShelf.

You can now borrow books using your RFID card.

Regards,
SmartShelf Team
"""
    return send_email(student_email, subject, body)

from urllib.parse import urlencode

def send_issue_email(student_name, student_email, book_title, issue_dt, return_dt):
    subject = "SmartShelf — Book Issue Confirmation"

    # --- Create Google Calendar link ---
    details = {
        "action": "TEMPLATE",
        "text": f"Return '{book_title}' to SmartShelf Library",
        "dates": f"{issue_dt.strftime('%Y%m%dT%H%M%S')}/{return_dt.strftime('%Y%m%dT%H%M%S')}",
        "details": f"Reminder to return the book '{book_title}' issued from SmartShelf.",
        "location": "SmartShelf Library"
    }
    google_calendar_url = "https://www.google.com/calendar/render?" + urlencode(details)

    # --- Email body ---
    body = f"""Dear {student_name},

Your book "{book_title}" has been issued.

Issue Date: {issue_dt.strftime('%d %b %Y, %I:%M %p')}
Return Date: {return_dt.strftime('%d %b %Y, %I:%M %p')}

Please return the book by the due date.

📅 Add to your calendar:
{google_calendar_url}

Regards,
SmartShelf Team
"""

    # Send using your existing send_email() function
    return send_email(student_email, subject, body)


#shettycr52@gmail.com

# ---- Arduino Setup ----
# Change this if Arduino IDE shows a different COM port.
ARDUINO_PORT = "COM3"
ARDUINO_BAUD = 9600

arduino = None


def connect_arduino():
    global arduino

    try:
        arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        time.sleep(2)  # Give Arduino time to reset after opening Serial
        print(f"Arduino connected on {ARDUINO_PORT}")
    except serial.SerialException as e:
        arduino = None
        print(f"Arduino not connected on {ARDUINO_PORT}: {e}")


connect_arduino()


# ---- Database Setup ----
conn = sqlite3.connect("smartshelf.db")
cursor = conn.cursor()

# Create books table (unchanged)
cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT UNIQUE,
    title TEXT,
    status TEXT DEFAULT 'available'
)
""")

# ---- Students table: ensure column 'email' exists (we will add it safely if missing) ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    ien_no TEXT PRIMARY KEY,
    uid TEXT UNIQUE,
    name TEXT,
    phone TEXT,
    email TEXT UNIQUE
)
""")
# If email column missing in older DB, ALTER to add it (safe)
cursor.execute("PRAGMA table_info(students)")
existing_columns = {col[1] for col in cursor.fetchall()}
if 'email' not in existing_columns:
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
        conn.commit()
        print("Added 'email' column to students table.")
    except Exception as e:
        print("Could not add email column:", e)

# Transactions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT,
    student_name TEXT,
    ien_no TEXT,
    phone TEXT,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    return_date TEXT
)
""")
cursor.execute("PRAGMA table_info(transactions)")
tcols = {col[1] for col in cursor.fetchall()}
if 'return_date' not in tcols:
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN return_date TEXT")
        conn.commit()
        print("Added 'return_date' column to transactions table.")
    except Exception as e:
        print("Could not add return_date column:", e)

conn.commit()

# ---- Tkinter Root ----
root = tk.Tk()
root.title("SmartShelf")
root.geometry("1000x700")
root.configure(bg="#F0F4F8")
root.eval('tk::PlaceWindow . center')

# ---- Styles (keep existing treeview style but restyle later) ----
base_style = ttk.Style(root)
base_style.theme_use('clam')
base_style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="#2E8B57", foreground="white")
base_style.configure("Treeview", font=("Helvetica", 10), rowheight=25)
base_style.map("Treeview", background=[('selected', '#81C784')])

# --------------------------------------
# All functions (logic preserved, extended where necessary)
# --------------------------------------
def load_books():
    for row in book_table.get_children():
        book_table.delete(row)
    cursor.execute("SELECT id, title, uid, status FROM books")
    for i, book in enumerate(cursor.fetchall()):
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        book_table.insert("", tk.END, values=book, tags=(tag,))
    book_table.tag_configure('evenrow', background='#FFFFFF')
    book_table.tag_configure('oddrow', background='#F7FBF9')

def animate_status(label, msg, color="green", duration=2000):
    label.config(text=msg, fg=color)
    label.after(duration, lambda: label.config(text=""))

# ---- Add Student (with RFID scan) -- now asks for email and offers to send welcome mail ----
def add_student():
    win = tk.Toplevel(root)
    win.title("Add Student")
    win.geometry("460x480")
    win.configure(bg="#F0F4F8")

    tk.Label(win, text="Scan Student RFID Card:", bg="#F0F4F8").pack(pady=5)
    uid_entry = tk.Entry(win, font=("Helvetica", 12))
    uid_entry.pack(pady=5)

    tk.Label(win, text="Name:", bg="#F0F4F8").pack(pady=5)
    name_entry = tk.Entry(win, font=("Helvetica", 12))
    name_entry.pack(pady=5)

    tk.Label(win, text="IEN No (unique):", bg="#F0F4F8").pack(pady=5)
    ien_entry = tk.Entry(win, font=("Helvetica", 12))
    ien_entry.pack(pady=5)

    tk.Label(win, text="Phone:", bg="#F0F4F8").pack(pady=5)
    phone_entry = tk.Entry(win, font=("Helvetica", 12))
    phone_entry.pack(pady=5)

    tk.Label(win, text="Email:", bg="#F0F4F8").pack(pady=5)
    email_entry = tk.Entry(win, font=("Helvetica", 12))
    email_entry.pack(pady=5)

    status_lbl = tk.Label(win, text="Waiting for student tag scan...", bg="#F0F4F8", fg="blue")
    status_lbl.pack(pady=10)

    if arduino is None:
        messagebox.showerror(
            "Arduino Not Connected",
            f"Could not connect to Arduino on {ARDUINO_PORT}.\\n"
            "Check Arduino IDE > Tools > Port and update ARDUINO_PORT."
        )
        win.destroy()
        return

    if arduino is None:
        messagebox.showerror(
            "Arduino Not Connected",
            f"Could not connect to Arduino on {ARDUINO_PORT}.\\n"
            "Check Arduino IDE > Tools > Port and update ARDUINO_PORT."
        )
        reg_win.destroy()
        return

    arduino.reset_input_buffer()

    def scan_uid():
        try:
            if arduino.in_waiting > 0:
                uid = arduino.readline().decode('utf-8', errors='ignore').strip()
                if uid:
                    uid_entry.delete(0, tk.END)
                    uid_entry.insert(0, uid)
                    cursor.execute("SELECT name FROM students WHERE uid=?", (uid,))
                    result = cursor.fetchone()
                    if result:
                        status_lbl.config(text=f"UID already registered to '{result[0]}'", fg="red")
                    else:
                        status_lbl.config(text=f"Scanned UID ready: {uid}", fg="green")
        except Exception:
            pass
        win.after(150, scan_uid)

    scan_uid()

    def save():
        uid = uid_entry.get().strip()
        name = name_entry.get().strip()
        ien = ien_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if not (uid and name and ien):
            messagebox.showwarning("Warning", "All fields required (UID, Name, IEN).")
            return
        try:
            cursor.execute("INSERT INTO students (ien_no, uid, name, phone, email) VALUES (?, ?, ?, ?, ?)",
                           (ien, uid, name, phone, email))
            conn.commit()
            # Ask to send welcome email if email provided
            if email:
                if messagebox.askyesno("Send Welcome Email?", f"Send a welcome email to {email}?"):
                    success = send_welcome_email(name, email)
                    if success:
                        messagebox.showinfo("Email sent", f"Welcome email sent to {email}.")
                    else:
                        messagebox.showwarning("Email failed", f"Could not send email to {email}. Check SMTP settings.")
            messagebox.showinfo("Success", f"Student {name} added with UID {uid} and IEN {ien}.")
            win.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "UID or IEN already exists!")

    tk.Button(win, text="Save", bg="#2E8B57", fg="white", command=save).pack(pady=10)

# ---- View Students (list + edit + delete) including email ----
def view_students():
    vwin = tk.Toplevel(root)
    vwin.title("Students")
    vwin.geometry("750x420")
    vwin.configure(bg="#F0F4F8")

    cols = ("IEN No", "UID", "Name", "Phone", "Email")
    st_tree = ttk.Treeview(vwin, columns=cols, show="headings")
    for col in cols:
        st_tree.heading(col, text=col)
        st_tree.column(col, width=150)
    st_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_students():
        for r in st_tree.get_children():
            st_tree.delete(r)
        cursor.execute("SELECT ien_no, uid, name, phone, email FROM students ORDER BY name")
        for row in cursor.fetchall():
            st_tree.insert("", tk.END, values=row)

    def edit_student():
        sel = st_tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a student to edit.")
            return
        ien, uid, name, phone, email = st_tree.item(sel)["values"]
        ew = tk.Toplevel(vwin)
        ew.title("Edit Student")
        ew.geometry("460x360")
        ew.configure(bg="#F0F4F8")

        tk.Label(ew, text="UID:", bg="#F0F4F8").pack(pady=5)
        uid_e = tk.Entry(ew, font=("Helvetica", 12)); uid_e.pack(pady=5); uid_e.insert(0, uid)
        tk.Label(ew, text="Name:", bg="#F0F4F8").pack(pady=5)
        name_e = tk.Entry(ew, font=("Helvetica", 12)); name_e.pack(pady=5); name_e.insert(0, name)
        tk.Label(ew, text="IEN No:", bg="#F0F4F8").pack(pady=5)
        ien_e = tk.Entry(ew, font=("Helvetica", 12)); ien_e.pack(pady=5); ien_e.insert(0, ien)
        tk.Label(ew, text="Phone:", bg="#F0F4F8").pack(pady=5)
        phone_e = tk.Entry(ew, font=("Helvetica", 12)); phone_e.pack(pady=5); phone_e.insert(0, phone)
        tk.Label(ew, text="Email:", bg="#F0F4F8").pack(pady=5)
        email_e = tk.Entry(ew, font=("Helvetica", 12)); email_e.pack(pady=5); email_e.insert(0, email)

        def save_edit():
            new_uid = uid_e.get().strip()
            new_name = name_e.get().strip()
            new_ien = ien_e.get().strip()
            new_phone = phone_e.get().strip()
            new_email = email_e.get().strip()
            if not (new_name and new_ien):
                messagebox.showwarning("Missing", "Name and IEN required.")
                return
            try:
                cursor.execute("UPDATE students SET uid=?, name=?, phone=?, email=? WHERE ien_no=?",
                               (new_uid, new_name, new_phone, new_email, ien))
                # If user changed the primary key (ien_no), attempt safe replace
                if new_ien != ien:
                    cursor.execute("INSERT OR REPLACE INTO students (ien_no, uid, name, phone, email) VALUES (?, ?, ?, ?, ?)",
                                   (new_ien, new_uid, new_name, new_phone, new_email))
                    cursor.execute("DELETE FROM students WHERE ien_no=?", (ien,))
                conn.commit()
                messagebox.showinfo("Saved", "Student updated.")
                ew.destroy()
                load_students()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "UID or IEN must be unique. Conflict encountered.")

        tk.Button(ew, text="Save", bg="#2E8B57", fg="white", command=save_edit).pack(pady=10)

    def delete_student():
        sel = st_tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a student to delete.")
            return
        ien, uid, name, phone, email = st_tree.item(sel)["values"]
        if messagebox.askyesno("Confirm", f"Delete student {name} ({ien})?"):
            cursor.execute("DELETE FROM students WHERE ien_no=?", (ien,))
            conn.commit()
            load_students()

    btnf = tk.Frame(vwin, bg="#F0F4F8")
    btnf.pack(pady=5)
    tk.Button(btnf, text="Edit", bg="#2E8B57", fg="white", width=12, command=edit_student).grid(row=0, column=0, padx=5)
    tk.Button(btnf, text="Delete", bg="#E53935", fg="white", width=12, command=delete_student).grid(row=0, column=1, padx=5)
    tk.Button(btnf, text="Close", bg="#BDBDBD", fg="black", width=12, command=vwin.destroy).grid(row=0, column=2, padx=5)

    load_students()

def open_feature_window():
    feature_win = tk.Toplevel(root)
    feature_win.title("Menu")
    feature_win.geometry("400x480")
    feature_win.configure(bg="#F0F4F8")

    tk.Label(
        feature_win,
        text="📚 Options",
        font=("Poppins", 16, "bold"),
        bg="#F0F4F8",
        fg="#0F172A"
    ).pack(pady=20)

    # Buttons for all features
    # make_button(feature_win, "Register Book", register_book, bg="#059669").pack(pady=6)
    # make_button(feature_win, "Checkout Book", checkout_book, bg="#0ea5a4").pack(pady=6)
    # make_button(feature_win, "Return Book", return_book, bg="#047857").pack(pady=6)
    # make_button(feature_win, "Delete Book", delete_book, bg="#DC2626").pack(pady=6)
    make_button_for(feature_win, "View Transactions", view_transactions, bg="#0F172A").pack(pady=6)
    # make_button(feature_win, "Add Student", add_student, bg="#2563EB").pack(pady=6)
    make_button_for(feature_win, "View Students", view_students, bg="#2563EB").pack(pady=6)
    make_button_for(feature_win, "Pending Returns", view_pending_returns, bg="#EAB308").pack(pady=6)
    make_button_for(feature_win,"Configure Return Duration", configure_return_duration, bg="#7C3AED").pack(pady=6)
    # make_button(feature_win, "Close", feature_win.destroy, bg="#BDBDBD").pack(pady=20)
    make_button_for(feature_win, "Download Transactions", download_transactions_pdf, bg="#059669").pack(pady=6)

    tk.Button(
        feature_win, text="Close", bg="#BDBDBD", fg="black",
        font=("Poppins", 10, "bold"), width=15,
        command=feature_win.destroy
    ).pack(pady=20)


from datetime import datetime

def view_pending_returns():
    # Get all issued books that haven't been marked as returned
    cursor.execute("""
        SELECT t.student_name, t.ien_no, t.phone, b.title, t.timestamp, t.return_date
        FROM transactions t
        JOIN books b ON t.uid = b.uid
        WHERE t.action = 'issued'
        AND t.uid NOT IN (
            SELECT uid FROM transactions WHERE action = 'returned'
        )
    """)
    pending = cursor.fetchall()

    if not pending:
        messagebox.showinfo("No Pending Returns", "🎉 All books have been returned.")
        return

    # Create a new window to show results
    pending_window = tk.Toplevel(root)
    pending_window.title("Pending Book Returns")
    pending_window.geometry("900x400")
    pending_window.configure(bg="#F8FAFC")

    tk.Label(pending_window, text="📚 Students Who Haven’t Returned Books", font=("Poppins", 14, "bold"), bg="#F8FAFC").pack(pady=10)

    cols = ("Student Name", "IEN No", "Phone", "Book Title", "Issued On", "Return Due Date")
    tree = ttk.Treeview(pending_window, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center")
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Add rows
    for s_name, ien, phone, book, issued, due in pending:
        issued_str = issued if isinstance(issued, str) else issued.strftime("%d-%m-%Y %I:%M %p")
        due_str = due if due else "N/A"
        tree.insert("", "end", values=(s_name, ien, phone, book, issued_str, due_str))

# ---- Register Book (unchanged) ----
def register_book(prefill_uid=""):
    reg_win = tk.Toplevel(root)
    reg_win.title("Register Book")
    reg_win.geometry("400x250")
    reg_win.configure(bg="#F0F4F8")

    tk.Label(reg_win, text="UID (Scan RFID Tag):", bg="#F0F4F8").pack(pady=5)
    uid_entry = tk.Entry(reg_win, font=("Helvetica", 12))
    uid_entry.pack(pady=5)
    uid_entry.insert(0, prefill_uid)

    tk.Label(reg_win, text="Title:", bg="#F0F4F8").pack(pady=5)
    title_entry = tk.Entry(reg_win, font=("Helvetica", 12))
    title_entry.pack(pady=5)

    status_label = tk.Label(reg_win, text="Waiting for tag scan...", bg="#F0F4F8", fg="blue")
    status_label.pack(pady=10)

    arduino.reset_input_buffer()

    def scan_uid():
        try:
            if arduino.in_waiting > 0:
                uid = arduino.readline().decode('utf-8', errors='ignore').strip()
                if uid:
                    uid_entry.delete(0, tk.END)
                    uid_entry.insert(0, uid)
                    cursor.execute("SELECT title FROM books WHERE uid=?", (uid,))
                    result = cursor.fetchone()
                    if result:
                        status_label.config(text=f"UID already registered to '{result[0]}'", fg="red")
                    else:
                        status_label.config(text=f"UID ready to register: {uid}", fg="green")
        except Exception:
            pass
        reg_win.after(100, scan_uid)

    scan_uid()

    def submit():
        uid = uid_entry.get().strip()
        title = title_entry.get().strip()
        if uid and title:
            try:
                cursor.execute("INSERT INTO books (uid, title) VALUES (?, ?)", (uid, title))
                conn.commit()
                animate_status(status_label, f"Book '{title}' registered.", "green")
                reg_win.destroy()
                load_books()
            except sqlite3.IntegrityError:
                status_label.config(text="This UID is already registered!", fg="red")
        else:
            animate_status(status_label, "Please fill all fields.", "orange")

    tk.Button(reg_win, text="Register", bg="#2E8B57", fg="white", command=submit).pack(pady=10)

# ---- Checkout (Auto: student card + book card) ----
def checkout_book():
    win = tk.Toplevel(root)
    win.title("Checkout Book (Auto Mode)")
    win.geometry("520x360")
    win.configure(bg="#F0F4F8")

    tk.Label(win, text="Step 1: Scan Student Card, then Step 2: Scan Book Card", bg="#F0F4F8", font=("Helvetica", 12)).pack(pady=8)
    status_label = tk.Label(win, text="", bg="#F0F4F8", font=("Helvetica", 12))
    status_label.pack(pady=6)

    scanned = {"student": None, "book": None}

    scanned_label = tk.Label(win, text="No student scanned yet.", bg="#F0F4F8", font=("Helvetica", 11))
    scanned_label.pack(pady=6)

    if arduino is None:
        messagebox.showerror(
            "Arduino Not Connected",
            f"Could not connect to Arduino on {ARDUINO_PORT}.\\n"
            "Check Arduino IDE > Tools > Port and update ARDUINO_PORT."
        )
        win.destroy()
        return

    if arduino is None:
        messagebox.showerror(
            "Arduino Not Connected",
            f"Could not connect to Arduino on {ARDUINO_PORT}.\\n"
            "Check Arduino IDE > Tools > Port and update ARDUINO_PORT."
        )
        win.destroy()
        return

    arduino.reset_input_buffer()

    def scan_loop():
        try:
            if arduino.in_waiting > 0:
                uid = arduino.readline().decode('utf-8', errors='ignore').strip()
                if uid:
                    # If student not scanned, check students table (include email)
                    if not scanned["student"]:
                        cursor.execute("SELECT ien_no, uid, name, phone, email FROM students WHERE uid=?", (uid,))
                        stu = cursor.fetchone()
                        if stu:
                            scanned["student"] = stu  # tuple (ien_no, uid, name, phone, email)
                            scanned_label.config(text=f"Student scanned: {stu[2]} ({stu[0]})")
                            animate_status(status_label, f"Student {stu[2]} scanned. Now scan book.", "green")
                        else:
                            animate_status(status_label, "Unknown student card. Please register student first.", "red")
                    # If student scanned and book not scanned yet
                    elif not scanned["book"]:
                        cursor.execute("SELECT id, uid, title, status FROM books WHERE uid=?", (uid,))
                        book = cursor.fetchone()
                        if book:
                            if book[3] == "issued":
                                animate_status(status_label, f"Book '{book[2]}' already issued.", "red")
                            else:
                                scanned["book"] = book  # tuple (id, uid, title, status)
                                animate_status(status_label, f"Book '{book[2]}' scanned successfully!", "green")
                                win.after(700, confirm_checkout)
                        else:
                            # prompt to register
                            if messagebox.askyesno("Not Found", f"Book UID {uid} not found. Register it?"):
                                win.destroy()
                                register_book(prefill_uid=uid)
                                return
        except Exception:
            pass
        win.after(200, scan_loop)

    def confirm_checkout():
        stu = scanned["student"]
        book = scanned["book"]
        if not stu or not book:
            return
        ien_no, s_uid, s_name, s_phone, s_email = stu
        b_id, b_uid, b_title, b_status = book

        # Update book status
        cursor.execute("UPDATE books SET status=? WHERE uid=?", ("issued", b_uid))

        # Read return duration (in days) from config file
        try:
            with open("return_config.txt", "r") as f:
                return_days = int(f.read().strip())
        except Exception:
            return_days = 7  # default 7 days

        issue_dt = now_ist()
        return_dt = issue_dt + timedelta(days=return_days)

        # Insert transaction with IST timestamp and return_date
        cursor.execute(
            "INSERT INTO transactions (uid, student_name, ien_no, phone, action, timestamp, return_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (b_uid, s_name, ien_no, s_phone, "issued", fmt_dt(issue_dt), fmt_dt(return_dt))
        )
        conn.commit()

        # Send issue email (if student email exists)
        if s_email:
            sent = send_issue_email(s_name, s_email, b_title, issue_dt, return_dt)
            if not sent:
                print("Failed to send issue email — check SMTP settings.")

        animate_status(status_label, f"Book '{b_title}' issued to {s_name}.", "green")
        scanned["student"] = None
        scanned["book"] = None
        scanned_label.config(text="No student scanned yet.")
        load_books()

    tk.Button(win, text="Cancel/Reset", bg="#BDBDBD", fg="black", width=18, command=lambda: (scanned.clear(), win.destroy())).pack(pady=8)
    scan_loop()

from tkinter import filedialog
import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tkinter import filedialog, messagebox

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tkinter import filedialog, messagebox

def download_transactions_pdf():
    try:
        # Ask where to save the PDF
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Transactions Report"
        )
        if not file_path:
            return

        # Fetch data from the transactions table
        cursor.execute("""
            SELECT student_name, ien_no, uid, action, timestamp, return_date
            FROM transactions
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()

        # Create PDF document
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("📚 SmartShelf — Transaction Report", styles["Title"]))
        elements.append(Spacer(1, 12))

        # Table header + data
        data = [["Student Name", "IEN No", "Book UID", "Action", "Issued On", "Return Date"]]
        for r in rows:
            data.append(list(r))

        # Table style
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#059669")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ]))

        elements.append(table)
        doc.build(elements)

        messagebox.showinfo("Success", f"Transactions saved successfully!\nFile: {file_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Could not export PDF.\n{e}")

# ---- Return Book (Auto scan book) ----
def return_book():
    win = tk.Toplevel(root)
    win.title("Return Book")
    win.geometry("420x260")
    win.configure(bg="#F0F4F8")

    tk.Label(win, text="Scan the Book to Return...", bg="#F0F4F8", font=("Helvetica", 12)).pack(pady=10)
    status_label = tk.Label(win, text="", bg="#F0F4F8", font=("Helvetica", 12))
    status_label.pack(pady=10)

    arduino.reset_input_buffer()

    def scan_loop():
        try:
            if arduino.in_waiting > 0:
                uid = arduino.readline().decode('utf-8', errors='ignore').strip()
                if uid:
                    cursor.execute("SELECT id, uid, title, status FROM books WHERE uid=?", (uid,))
                    book = cursor.fetchone()
                    if book:
                        if book[3] == "available":
                            animate_status(status_label, f"Book '{book[2]}' is not issued.", "red")
                        else:
                            cursor.execute("UPDATE books SET status=? WHERE uid=?", ("available", uid))
                            cursor.execute("INSERT INTO transactions (uid, student_name, ien_no, phone, action, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                                           (uid, "Returned", "", "", "returned", fmt_dt(now_ist())))
                            conn.commit()
                            animate_status(status_label, f"Book '{book[2]}' returned.", "green")
                            load_books()
                    else:
                        animate_status(status_label, f"Book UID {uid} not found.", "red")
        except Exception:
            pass
        win.after(200, scan_loop)

    scan_loop()

# ---- Delete Book ----
def delete_book():
    selected = book_table.focus()
    if not selected:
        messagebox.showwarning("Warning", "Select a book from the list to delete.")
        return
    book_data = book_table.item(selected)["values"]
    uid = book_data[2]
    title = book_data[1]
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}'?")
    if confirm:
        cursor.execute("DELETE FROM books WHERE uid=?", (uid,))
        conn.commit()
        load_books()

# ---- View Transactions (unchanged but now shows return_date if present) ----
def view_transactions():
    win = tk.Toplevel(root)
    win.title("Transaction History")
    win.geometry("1000x420")
    win.configure(bg="#F0F4F8")

    cols = ("ID", "UID", "Title", "Student Name", "IEN No", "Phone", "Action", "Timestamp", "Return Date")
    trans_tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        trans_tree.heading(col, text=col)
        trans_tree.column(col, width=110)
    trans_tree.pack(fill=tk.BOTH, expand=True)

    cursor.execute("""
        SELECT t.id, t.uid, b.title, t.student_name, t.ien_no, t.phone, t.action, t.timestamp, t.return_date
        FROM transactions t
        LEFT JOIN books b ON t.uid = b.uid
        ORDER BY t.timestamp DESC
    """)
    for row in cursor.fetchall():
        trans_tree.insert("", tk.END, values=row)

# --------------------------------------
# UI (Premium header + card + hover effects)
# --------------------------------------

# Header (logo + title) - UI enhancement
header_frame = tk.Frame(root, bg="#F0F4F8")
header_frame.pack(fill="x", pady=(12, 6))

try:
    logo_img = Image.open("nhitm.jpeg")
    logo_img = logo_img.resize((100, 100))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_lbl = tk.Label(header_frame, image=logo_photo, bg="#F0F4F8")
    logo_lbl.image = logo_photo
    logo_lbl.pack(side="left", padx=(20, 10))
except Exception as e:
    print("Logo not loaded:", e)

# Title next to logo - UI enhancement
title_lbl = tk.Label(header_frame, text="SmartShelf", font=("Poppins", 26, "bold"), fg="#0F172A", bg="#F0F4F8")
title_lbl.pack(side="left", padx=(5, 20))

# Thin separator - UI enhancement
sep = ttk.Separator(root, orient='horizontal')
sep.pack(fill='x', padx=20, pady=(6, 12))

# Content card (white background) to simulate a card with subtle border - UI enhancement
content_card = tk.Frame(root, bg="white", bd=0, highlightthickness=1, highlightbackground="#E6EEF7")
content_card.pack(fill="both", expand=False, padx=20, pady=(0,12))

# Search area inside card - UI enhancement
search_frame = tk.Frame(content_card, bg="white")
search_frame.pack(fill="x", padx=16, pady=12)

tk.Label(search_frame, text="🔍 Search Book:", bg="white", fg="#0F172A", font=("Poppins", 12)).pack(side=tk.LEFT, padx=(4,8))
book_search_var = tk.StringVar()
book_search_entry = tk.Entry(search_frame, textvariable=book_search_var, font=("Poppins", 12), width=40, bd=1, relief="solid")
book_search_entry.pack(side=tk.LEFT, padx=(0,10))

def search_books_ui():
    query = book_search_var.get().strip().lower()
    for row in book_table.get_children():
        book_table.delete(row)
    if not query:
        cursor.execute("SELECT id, title, uid, status FROM books")
    else:
        cursor.execute("SELECT id, title, uid, status FROM books WHERE LOWER(uid) LIKE ? OR LOWER(title) LIKE ?",
                       (f"%{query}%", f"%{query}%"))
    for book in cursor.fetchall():
        book_table.insert("", tk.END, values=book)

# Create styled buttons with hover effect - UI enhancement
def make_button(parent, text, command, bg="#2E8B57", fg="white", width=15):
    b = tk.Button(parent, text=text, bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                  relief="flat", bd=0, font=("Poppins", 10, "bold"), width=width, cursor="hand2", command=command)
    # Hover effects
    def on_enter(e):
        try:
            b['bg'] = _lighten_color(bg, 0.08)
        except Exception:
            b['bg'] = bg
    def on_leave(e):
        b['bg'] = bg
    b.bind("<Enter>", on_enter)
    b.bind("<Leave>", on_leave)
    return b

def make_button_for(parent, text, command, bg="#2E8B57", fg="white", width=22):
    b = tk.Button(parent, text=text, bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                  relief="flat", bd=0, font=("Poppins", 10, "bold"), width=width, cursor="hand2", command=command)
    # Hover effects
    def on_enter(e):
        try:
            b['bg'] = _lighten_color(bg, 0.08)
        except Exception:
            b['bg'] = bg
    def on_leave(e):
        b['bg'] = bg
    b.bind("<Enter>", on_enter)
    b.bind("<Leave>", on_leave)
    return b

# Helper to slightly lighten a hex color
def _lighten_color(hexcolor, amount=0.1):
    hexcolor = hexcolor.lstrip('#')
    r = int(hexcolor[0:2], 16)
    g = int(hexcolor[2:4], 16)
    b = int(hexcolor[4:6], 16)
    r = int(min(255, r + 255 * amount))
    g = int(min(255, g + 255 * amount))
    b = int(min(255, b + 255 * amount))
    return f"#{r:02x}{g:02x}{b:02x}"

# Buttons area inside card - UI enhancement
btn_frame_card = tk.Frame(content_card, bg="white")
btn_frame_card.pack(fill="x", padx=16, pady=(0,12))

search_btn = make_button(btn_frame_card, "Search", search_books_ui, bg="#2563EB", width=12)
search_btn.pack(side="left", padx=(0,8))

clear_btn = make_button(btn_frame_card, "Clear", lambda: (book_search_var.set(""), search_books_ui()), bg="#94A3B8", width=12)
clear_btn.pack(side="left", padx=(0,8))

# ---- Treeview to show books inside content card (styled) ----
tree_frame = tk.Frame(content_card, bg="white")
tree_frame.pack(fill="both", padx=16, pady=(0,12))

columns = ("ID", "Title", "UID", "Status")
book_table = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
for col in columns:
    book_table.heading(col, text=col)
    book_table.column(col, width=210, anchor="center")
book_table.pack(fill="x")

# Apply alternate row colors and style
book_table.tag_configure('evenrow', background='#FFFFFF')
book_table.tag_configure('oddrow', background='#F7FBF9')

# Buttons below the table (kept identical functionality, only visual) - UI enhancement
controls_frame = tk.Frame(root, bg="#F0F4F8")
controls_frame.pack(pady=(8,12))

# Create real action buttons using make_button, map to existing commands (no logic changed)
make_button(controls_frame, "Register Book", register_book, bg="#059669").grid(row=0, column=0, padx=6)
make_button(controls_frame, "Checkout Book", checkout_book, bg="#0ea5a4").grid(row=0, column=1, padx=6)
make_button(controls_frame, "Return Book", return_book, bg="#047857").grid(row=0, column=2, padx=6)
make_button(controls_frame, "Delete Book", delete_book, bg="#DC2626").grid(row=0, column=3, padx=6)
# make_button(controls_frame, "View Transactions", view_transactions, bg="#0F172A").grid(row=0, column=4, padx=6)
make_button(controls_frame, "Add Student", add_student, bg="#2563EB").grid(row=0, column=5, padx=6)
# make_button(controls_frame, "View Students", view_students, bg="#2563EB").grid(row=0, column=6, padx=6)

# ---- Configure Return Duration button (new) ----
def configure_return_duration():
    duration = simpledialog.askinteger("Set Return Duration", "Enter return duration in days:", minvalue=1, maxvalue=60)
    if duration:
        with open("return_config.txt", "w") as f:
            f.write(str(duration))
        messagebox.showinfo("Saved", f"Return duration set to {duration} days for all issues.")

# make_button(controls_frame, "Configure Return Duration", configure_return_duration, bg="#1E3A8A").grid(row=0, column=7, padx=6)

# make_button(controls_frame, "View Pending Returns", view_pending_returns, bg="#B91C1C").grid(row=0, column=8, padx=8)

make_button(controls_frame, "Menu", open_feature_window, bg="#9333EA").grid(row=0, column=7, padx=6)

# Footer - UI enhancement
footer = tk.Label(root, text="© 2025 SmartShelf | Powered by NexGen", font=("Poppins", 9), fg="#64748B", bg="#F0F4F8")
footer.pack(side="bottom", pady=10)

# ---- Initial population ----
load_books()

# ---- Run Tkinter loop ----
root.mainloop()

# ---- Close DB and Arduino ----
conn.close()

if arduino is not None and arduino.is_open:
    arduino.close()