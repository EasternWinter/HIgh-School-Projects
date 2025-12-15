import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os
import hashlib
import base64
import secrets
#py -m pip install tkcalendar
import tkcalendar
from tkcalendar import DateEntry
from datetime import date
import random
import string

DATA_FILE = "data.json"

CONFIG_FILE = "config.json"

def save_bg_color(color):
    data = {"bg_color": color}
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_bg_color():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("bg_color", "light grey")
    return "light grey"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"users": {}, "student_data": {}, "bg_color": "#f0f4f7"}, f)
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    #Ensure bg_color exists:
    if "bg_color" not in data:
        data["bg_color"] = "#f0f4f7"
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

#Password Hashing Helpers (PBKDF2-HMAC-SHA256)
def hash_password(password: str, iterations: int = 100_000) -> dict:
    if isinstance(password, str):
        password = password.encode("utf-8")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password, salt, iterations)
    return {
        "alg": "pbkdf2_sha256",
        "iterations": iterations,
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(dk).decode("ascii")
    }

def verify_password(stored: dict, password: str) -> bool:
    if stored is None or not isinstance(stored, dict):
        return False
    try:
        salt = base64.b64decode(stored["salt"])
        expected = base64.b64decode(stored["hash"])
        iterations = int(stored.get("iterations", 100_000))
    except Exception:
        return False

    if isinstance(password, str):
        password = password.encode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", password, salt, iterations)
    return secrets.compare_digest(dk, expected)

#Data Classes
class Student:
    def __init__(self, roll_no, name, class_code, contact, address, gender, dob, courses=None):
        self.roll_no = roll_no
        self.name = name
        self.class_code = class_code
        self.contact = contact
        self.address = address
        self.gender = gender
        self.dob = dob
        self.courses = courses if courses is not None else []

    def to_dict(self):
        return {
            "roll_no": self.roll_no,
            "name": self.name,
            "class": self.class_code,
            "contact": self.contact,
            "address": self.address,
            "gender": self.gender,
            "dob": self.dob,
            "courses": self.courses,
        }

    @staticmethod
    def from_dict(data):
        return Student(
            roll_no=data["roll_no"],
            name=data["name"],
            class_code=data["class"],
            contact=data["contact"],
            address=data["address"],
            gender=data["gender"],
            dob=data.get("dob"),
            courses=data.get("courses", [])
        )

#User
class User:
    DATA_FILE = "data.json"

    #CORE LOAD/SAVE    
    @staticmethod
    def load_all():
        if not os.path.exists(DATA_FILE):
            return {"users": {}, "students": {}, "sessions": {}}

        with open(DATA_FILE, "r") as f:
            return json.load(f)

    @staticmethod
    def save_all(data):
        temp = "data_temp.json"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp, DATA_FILE)

    #Utility
    @staticmethod
    def generate_class_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    #User Management
    @staticmethod
    def register(username, password, role, created_by="system"):
        data = User.load_all()

        if username in data["users"]:
            return False, "Username already exists!"

        hashed = hash_password(password)
        hashed.update({
            "role": role,
            "bg_color": "#f0f4f7",
            "created_by": created_by,
        })

        if role == "Staff":
            hashed["class_code"] = User.generate_class_code()

        data["users"][username] = hashed
        User.save_all(data)

        return True, f"Account '{username}' created successfully!"

    @staticmethod
    def get_role(username):
        data = User.load_all()
        return data["users"].get(username, {}).get("role", "Staff")

    @staticmethod
    def login(username, password):
        data = User.load_all()
        stored = data["users"].get(username)
        if stored is None:
            return False, "Invalid username or password!"

        if verify_password(stored, password):
            return True, stored["role"]

        return False, "Invalid username or password!"

    #Theme
    @staticmethod
    def get_theme(username):
        data = User.load_all()
        return data["users"].get(username, {}).get("theme", "light")

    @staticmethod
    def set_theme(username, theme):
        data = User.load_all()
        if username in data["users"]:
            data["users"][username]["theme"] = theme
            User.save_all(data)

    #Staff / Class Code
    @staticmethod
    def get_staff_by_class_code(class_code):
        data = User.load_all()
        for username, udata in data["users"].items():
            if udata.get("role") == "Staff" and udata.get("class_code") == class_code:
                return username
        return None

    #Student Data
    @staticmethod
    def get_students(staff_username):
        data = User.load_all()
        students = data["students"].get(staff_username, {})
        return {roll: Student.from_dict(s) for roll, s in students.items()}

    @staticmethod
    def get_student_record(username):
        data = User.load_all()
        for staff, students in data["students"].items():
            for roll_no, s in students.items():
                if roll_no == username:
                    s["birthday"] = s.get("dob")
                    return Student.from_dict(s), staff
        return None, None

    @staticmethod
    def save_students(staff_username, students):
        data = User.load_all()

        #Convert Student objects → dicts
        data["students"][staff_username] = {
            r: s.to_dict() for r, s in students.items()
        }

        User.save_all(data)

    #Session Logic
    @staticmethod
    def get_sessions(staff):
        data = User.load_all()
        return data["sessions"].get(staff, [])

    @staticmethod
    def is_slot_available(staff, date, time):
        for s in User.get_sessions(staff):
            if s["date"] == date and s["time"] == time:
                return False
        return True

    @staticmethod
    def book_session(staff, student, date, time):
        data = User.load_all()
        data["sessions"].setdefault(staff, [])

        data["sessions"][staff].append({
            "student": student,
            "date": date,
            "time": time,
            "status": "Pending"
        })

        User.save_all(data)

    @staticmethod
    def get_student_bookings(student):
        data = User.load_all()
        results = []
        for staff, sessions in data["sessions"].items():
            for s in sessions:
                if s["student"] == student:
                    results.append(s)
        return results

#ENTRANCE WINDOWS
#Register Student Window
class StudentRegisterWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Student Registration")
        self.geometry("450x600")
        self.resizable(False, False)
        self.configure(bg="#f0f4f7")

        # CARD FRAME
        card = tk.Frame(self, bg="white", bd=2, relief="groove")
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=550)

        title = tk.Label(
            card, text="Student Registration",
            bg="white", fg="#333", font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=(15, 10))

        form = tk.Frame(card, bg="white")
        form.pack(pady=5)

        labels = [
            "Class Code", "Password", "Confirm Password",
            "Roll No", "Name", "Contact", "Address", "Gender", "Birthday"
        ]
        self.entries = {}

        # Flags for toggles
        self.show_password = False
        self.show_confirm_password = False

        for i, label in enumerate(labels):
            tk.Label(
                form, text=label + ":", bg="white", fg="#555",
                font=("Segoe UI", 11)
            ).grid(row=i, column=0, sticky="e", pady=5, padx=5)

            # FIELD CREATION
            if label == "Gender":
                entry = ttk.Combobox(form, values=["Male", "Female", "Others"], state="readonly")

            elif label == "Birthday":
                entry = DateEntry(
                    form, date_pattern="yyyy-mm-dd",
                    background="blue", foreground="white"
                )

            elif "Password" in label:
                entry = tk.Entry(form, show="*", font=("Segoe UI", 11), width=15, bd=2, relief="groove")
                entry.grid(row=1, column=1, sticky="w", pady=5)

            else:
                entry = tk.Entry(form, font=("Segoe UI", 11), width=22, bd=2, relief="groove")

            entry.grid(row=i, column=1, pady=5)
            key = label.replace(" ", "_").lower()
            self.entries[key] = entry

            #Add password toggle buttons
            if label == "Password":
                toggle_btn = tk.Button(
                    form, text="Show", width=5,
                    font=("Segoe UI", 9),
                    command=self.toggle_password
                )
                toggle_btn.grid(row=i, column=1, sticky="e", padx=(0, 5))
                self.toggle_password_btn = toggle_btn

            if label == "Confirm Password":
                toggle_btn2 = tk.Button(
                    form, text="Show", width=5,
                    font=("Segoe UI", 9),
                    command=self.toggle_confirm_password
                )
                toggle_btn2.grid(row=i, column=1, sticky="e", padx=(0, 5))
                self.toggle_confirm_btn = toggle_btn2

        #Register Button
        tk.Button(
            card, text="Register Student",
            command=self.register_student,
            bg="#0078D7", fg="white",
            font=("Segoe UI", 11, "bold"),
            activebackground="#005A9E",
            relief="flat", bd=0, width=20
        ).pack(pady=(15, 10))

    # TOGGLE PASSWORD VISIBILITY
    def toggle_password(self):
        if self.show_password:
            self.entries["password"].config(show="*")
            self.toggle_password_btn.config(text="Show")
        else:
            self.entries["password"].config(show="")
            self.toggle_password_btn.config(text="Hide")
        self.show_password = not self.show_password

    def toggle_confirm_password(self):
        if self.show_confirm_password:
            self.entries["confirm_password"].config(show="*")
            self.toggle_confirm_btn.config(text="Show")
        else:
            self.entries["confirm_password"].config(show="")
            self.toggle_confirm_btn.config(text="Hide")
        self.show_confirm_password = not self.show_confirm_password

    # REGISTER LOGIC
    def register_student(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}

        # Validate class code
        staff_user = User.get_staff_by_class_code(data["class_code"])
        if not staff_user:
            messagebox.showerror("Error", "Invalid Class Code!")
            return

        # Validate passwords match
        if data["password"] != data["confirm_password"]:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        roll_no = data["roll_no"]

        # Create login
        success, msg = User.register(
            username=roll_no,
            password=data["password"],
            role="Student"
        )

        if not success:
            messagebox.showerror("Error", msg)
            return

        # Save student data
        student_class = data["users"][staff_user].get("class_code", "N/A")
        student = Student(
            roll_no=roll_no,
            name=data["name"],
            class_code=student_class,
            contact=data["contact"],
            address=data["address"],
            gender=data["gender"],
            dob=data["birthday"]
        )

        student.username = roll_no
        students = User.get_students(staff_user)
        students[roll_no] = student
        User.save_students(staff_user, students)

        messagebox.showinfo("Success", "Student registered successfully!")
        self.destroy()

#Registration Window for Staff/Admin
class RegistrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Register - Student Management System")
        self.geometry("420x380")
        self.resizable(False, False)
        self.configure(bg="#f0f4f7")

        #Main Frame
        card = tk.Frame(self, bg="white", bd=2, relief="groove")
        card.place(relx=0.5, rely=0.5, anchor="center", width=360, height=320)

        title = tk.Label(card, text="Create Account", bg="white", fg="#333", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(15, 10))

        form = tk.Frame(card, bg="white")
        form.pack(pady=5)

        #Username
        tk.Label(form, text="Username:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.username_ent = tk.Entry(form, font=("Segoe UI", 11), width=22, bd=2, relief="groove")
        self.username_ent.grid(row=0, column=1, pady=5)

        #Password
        tk.Label(form, text="Password:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.password_ent = tk.Entry(form, font=("Segoe UI", 11), show="*", width=15, bd=2, relief="groove")
        self.password_ent.grid(row=1, column=1, sticky="w", pady=5)

        self.show_password = False
        self.toggle_password_btn = tk.Button(form, text="Show", font=("Segoe UI", 9), width=5,
                                             command=self.toggle_password)
        self.toggle_password_btn.grid(row=1, column=1, sticky="e", pady=5, padx=(0, 5))

        #Confirm Password
        tk.Label(form, text="Confirm:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.confirm_password_ent = tk.Entry(form, font=("Segoe UI", 11), show="*", width=15, bd=2, relief="groove")
        self.confirm_password_ent.grid(row=2, column=1, sticky="w", pady=5)

        self.show_confirm_password = False
        self.toggle_confirm_btn = tk.Button(form, text="Show", font=("Segoe UI", 9), width=5,
                                            command=self.toggle_confirm_password)
        self.toggle_confirm_btn.grid(row=2, column=1, sticky="e", pady=5, padx=(0, 5))

        #Role Selection (Admin / Staff)
        tk.Label(form, text="Role:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=3, column=0, sticky="e", pady=5, padx=5)
        self.role_var = tk.StringVar(value="Staff")
        self.role_menu = ttk.Combobox(form, textvariable=self.role_var,
                                      values=["Admin", "Staff"], state="readonly", font=("Segoe UI", 11), width=19)
        self.role_menu.grid(row=3, column=1, pady=5)

        #Register Button
        register_btn = tk.Button(
            card, text="Register", command=self.register,
            bg="#0078D7", fg="white", font=("Segoe UI", 11, "bold"),
            activebackground="#005A9E", relief="flat", bd=0, width=20
        )
        register_btn.pack(pady=(10, 10))

    #Toggle visibility functions
    def toggle_password(self):
        if self.show_password:
            self.password_ent.config(show="*")
            self.toggle_password_btn.config(text="Show")
        else:
            self.password_ent.config(show="")
            self.toggle_password_btn.config(text="Hide")
        self.show_password = not self.show_password

    def toggle_confirm_password(self):
        if self.show_confirm_password:
            self.confirm_password_ent.config(show="*")
            self.toggle_confirm_btn.config(text="Show")
        else:
            self.confirm_password_ent.config(show="")
            self.toggle_confirm_btn.config(text="Hide")
        self.show_confirm_password = not self.show_confirm_password

    def register(self):
        username = self.username_ent.get().strip()
        password = self.password_ent.get()
        confirm_password = self.confirm_password_ent.get()
        role = self.role_var.get()

        if not username or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        success, msg = User.register(username, password, role)
        if success:
            messagebox.showinfo("Success", f"{msg}\nRole: {role}")
            self.destroy()
        else:
            messagebox.showerror("Error", msg)

#Login Window
class LoginRegister(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login - Student Management System")
        self.geometry("420x420")
        self.resizable(False, False)
        self.configure(bg="#f0f4f7")

        #Container
        card = tk.Frame(self, bg="white", bd=2, relief="groove")
        card.place(relx=0.5, rely=0.5, anchor="center", width=360, height=360)

        title = tk.Label(card, text="Welcome Back 👋", bg="white",
                         fg="#333", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(15, 10))

        form = tk.Frame(card, bg="white")
        form.pack(pady=5)

        #Form Fields
        tk.Label(form, text="Username:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.username_ent = tk.Entry(form, font=("Segoe UI", 11), width=22, bd=2, relief="groove")
        self.username_ent.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Password:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.password_ent = tk.Entry(form, font=("Segoe UI", 11), show="*", width=15, bd=2, relief="groove")
        self.password_ent.grid(row=1, column=1, pady=5, sticky="w")

        self.show_password = False
        self.toggle_btn = tk.Button(form, text="Show", font=("Segoe UI", 9), width=5,
                                    command=self.toggle_password)
        self.toggle_btn.grid(row=1, column=1, sticky="e", pady=5, padx=(0, 5))

        # Buttons
        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=(10, 5))

        login_btn = tk.Button(
            btn_frame, text="Login", width=12,
            bg="#0078D7", fg="white", font=("Segoe UI", 11, "bold"),
            activebackground="#005A9E", relief="flat", bd=0,
            command=self.login
        )
        login_btn.grid(row=0, column=0, padx=5)

        register_btn = tk.Button(
            btn_frame, text="Staff Register", width=12,
            bg="#E5E5E5", fg="#333", font=("Segoe UI", 11, "bold"),
            activebackground="#D0D0D0", relief="flat", bd=0,
            command=self.open_registration
        )
        register_btn.grid(row=0, column=1, padx=5)

        student_reg_btn = tk.Button(
            btn_frame, text="Student Register", width=26,
            bg="#F0F0F0", fg="#333", font=("Segoe UI", 11, "bold"),
            activebackground="#D0D0D0", relief="flat", bd=0,
            command=self.open_student_registration
        )
        student_reg_btn.grid(row=1, column=0, columnspan=2, pady=5)

        forgot_btn = tk.Button(
            btn_frame, text="Forgot Password?", width=26,
            bg="#E5E5E5", fg="#333", font=("Segoe UI", 11, "bold"),
            activebackground="#D0D0D0", relief="flat", bd=0,
            command=self.open_forgot_password
        )
        forgot_btn.grid(row=2, column=0, columnspan=2, pady=5)

    def toggle_password(self):
        if self.show_password:
            self.password_ent.config(show="*")
            self.toggle_btn.config(text="Show")
        else:
            self.password_ent.config(show="")
            self.toggle_btn.config(text="Hide")
        self.show_password = not self.show_password

    def login(self):
        username = self.username_ent.get().strip()
        password = self.password_ent.get()
        success, msg = User.login(username, password)
        if success:
            self.destroy()
            if User.get_role(username) == "Admin":
                AdminPage(username)
            elif User.get_role(username) == "Staff":
                StaffPage(username)
            else:
                StudentPage(username)
        else:
            messagebox.showerror("Error", msg)

    def open_registration(self):
        RegistrationWindow(self)
    
    def open_student_registration(self):
        StudentRegisterWindow(self)
    
    def open_forgot_password(self):
        ForgotPasswordWindow(self)

#Forgot Password Window
class ForgotPasswordWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Forgot Password - Student Management System")
        self.geometry("420x280")
        self.resizable(False, False)
        self.configure(bg="#f0f4f7")

        card = tk.Frame(self, bg="white", bd=2, relief="groove")
        card.place(relx=0.5, rely=0.5, anchor="center", width=360, height=220)

        title = tk.Label(card, text="Reset Password", bg="white",
                         fg="#333", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(15, 10))

        form = tk.Frame(card, bg="white")
        form.pack(pady=5)

        #Username
        tk.Label(form, text="Username:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.username_ent = tk.Entry(form, font=("Segoe UI", 11), width=22, bd=2, relief="groove")
        self.username_ent.grid(row=0, column=1, pady=5)

        #New Password
        tk.Label(form, text="New Password:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.password_ent = tk.Entry(form, font=("Segoe UI", 11), show="*", width=15, bd=2, relief="groove")
        self.password_ent.grid(row=1, column=1, sticky="w", pady=5)

        self.show_new_password = False
        self.toggle_new_btn = tk.Button(form, text="Show", font=("Segoe UI", 9), width=5,
                                        command=self.toggle_new_password)
        self.toggle_new_btn.grid(row=1, column=1, sticky="e", pady=5, padx=(0, 5))

        #Confirm Password
        tk.Label(form, text="Confirm Password:", bg="white", fg="#555",
                 font=("Segoe UI", 11)).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.confirm_password_ent = tk.Entry(form, font=("Segoe UI", 11), show="*", width=15, bd=2, relief="groove")
        self.confirm_password_ent.grid(row=2, column=1, sticky="w", pady=5)

        self.show_confirm_password = False
        self.toggle_confirm_btn = tk.Button(form, text="Show", font=("Segoe UI", 9), width=5,
                                            command=self.toggle_confirm_password)
        self.toggle_confirm_btn.grid(row=2, column=1, sticky="e", pady=5, padx=(0, 5))

        #Reset Button
        reset_btn = tk.Button(
            card, text="Reset Password", command=self.reset_password,
            bg="#0078D7", fg="white", font=("Segoe UI", 11, "bold"),
            activebackground="#005A9E", relief="flat", bd=0, width=20
        )
        reset_btn.pack(pady=(10, 0))

    def toggle_new_password(self):
        if self.show_new_password:
            self.password_ent.config(show="*")
            self.toggle_new_btn.config(text="Show")
        else:
            self.password_ent.config(show="")
            self.toggle_new_btn.config(text="Hide")
        self.show_new_password = not self.show_new_password

    def toggle_confirm_password(self):
        if self.show_confirm_password:
            self.confirm_password_ent.config(show="*")
            self.toggle_confirm_btn.config(text="Show")
        else:
            self.confirm_password_ent.config(show="")
            self.toggle_confirm_btn.config(text="Hide")
        self.show_confirm_password = not self.show_confirm_password

    def reset_password(self):
        data = User.load_all()
        username = self.username_ent.get().strip()
        password = self.password_ent.get()
        confirm_password = self.confirm_password_ent.get()

        if not username or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        if username not in data["users"]:
            messagebox.showerror("Error", "Username does not exist!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        data["users"][username].update(hash_password(password))
        User.save_all(data)
        messagebox.showinfo("Success", "Password reset successful!")
        self.destroy()

#PAGES
#Student Page
class StudentPage(tk.Tk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title(f"Student Dashboard - {username}")
        self.geometry("650x675")

        #Load student + staff owner reference
        self.student, self.staff_owner = User.get_student_record(username)

        if self.student is None:
            messagebox.showerror("Error", f"Student record not found for {username}")
            self.destroy()
            return

        tk.Label(self, text="Student Dashboard", font=("Segoe UI", 20, "bold")).pack(pady=10)

        #Profile
        profile_frame = tk.LabelFrame(self, text="Profile", padx=10, pady=10)
        profile_frame.pack(fill="x", padx=10, pady=10)

        self.fields = {}
        labels = ["Roll No", "Name", "Class", "Contact", "Address", "Gender", "Birthday"]
        editable = ["contact", "address", "gender", "birthday"]

        for i, label in enumerate(labels):
            tk.Label(profile_frame, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=4)

            key = label.lower().replace(" ", "_")
            state = "normal" if key in editable else "readonly"

            if label == "Gender":
                entry = ttk.Combobox(profile_frame, values=["Male", "Female", "Others"], state=state)
            else:
                entry = tk.Entry(profile_frame, state=state)

            entry.grid(row=i, column=1, pady=4)

            attr = key
            if key == "class":
                attr = "class_code"
            elif key == "birthday":
                attr = "dob"

            entry.insert(0, getattr(self.student, attr))

            self.fields[key] = entry

        tk.Button(profile_frame, text="Update Profile", command=self.update_profile,
                  bg="#0078D7", fg="white").grid(row=len(labels), columnspan=2, pady=10)

        #Course management
        course_frame = tk.LabelFrame(self, text="Courses", padx=10, pady=10)
        course_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(course_frame, text="Add Course:").grid(row=0, column=0, pady=4)
        self.course_entry = tk.Entry(course_frame)
        self.course_entry.grid(row=0, column=1, pady=4)

        tk.Button(course_frame, text="Add", command=self.add_course,
                  bg="green", fg="white").grid(row=0, column=2, padx=5)

        self.course_listbox = tk.Listbox(course_frame, width=40, height=5)
        self.course_listbox.grid(row=1, column=0, columnspan=3, pady=5)
        self.load_courses()

        tk.Button(course_frame, text="Remove Selected", command=self.remove_course,
                  bg="red", fg="white").grid(row=2, columnspan=3, pady=5)

        tk.Button(self, text="Book a Session", command=self.book_session_window,
                  bg="purple", fg="white").pack(pady=5)

        tk.Button(self, text="View My Bookings", command=self.view_bookings_window,
                  bg="darkblue", fg="white").pack(pady=5)
        self.create_menubar()

    def update_profile(self):
        self.student.contact = self.fields["contact"].get()
        self.student.address = self.fields["address"].get()
        self.student.gender = self.fields["gender"].get()
        self.student.birthday = self.fields["birthday"].get()

        students = User.get_students(self.staff_owner)
        students[self.student.roll_no] = self.student
        User.save_students(self.staff_owner, students)

        messagebox.showinfo("Success", "Profile Updated!")

    #Couses
    def load_courses(self):
        self.course_listbox.delete(0, tk.END)
        for c in self.student.courses:
            self.course_listbox.insert(tk.END, c)

    def add_course(self):
        course = self.course_entry.get().strip()
        if course:
            self.student.courses.append(course)
            self.course_entry.delete(0, tk.END)
            self.load_courses()
            User.save_students(self.staff_owner, User.get_students(self.staff_owner))

    def remove_course(self):
        sel = self.course_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        del self.student.courses[index]
        self.load_courses()
        User.save_students(self.staff_owner, User.get_students(self.staff_owner))

    #Booking
    def book_session_window(self):
        win = tk.Toplevel(self)
        win.title("Book Session")
        win.geometry("350x300")

        tk.Label(win, text="Select Date:").pack(pady=5)
        date_entry = DateEntry(win, date_pattern="yyyy-mm-dd")
        date_entry.pack()

        tk.Label(win, text="Select Time (HH:MM):").pack(pady=5)
        time_entry = tk.Entry(win)
        time_entry.pack()

        def book():
            date = date_entry.get()
            time = time_entry.get()

            # Check availability
            if not User.is_slot_available(self.staff_owner, date, time):
                messagebox.showerror("Unavailable", "This time slot is already booked!")
                return

            # Book slot
            User.book_session(self.staff_owner, self.username, date, time)
            messagebox.showinfo("Success", "Session booked!")
            win.destroy()

        tk.Button(win, text="Submit", command=book, bg="blue", fg="white").pack(pady=10)

    #View bookings
    def view_bookings_window(self):
        win = tk.Toplevel(self)
        win.title("My Bookings")
        win.geometry("350x300")

        bookings = User.get_student_bookings(self.username)

        lb = tk.Listbox(win, width=40, height=12)
        lb.pack(pady=10)

        for b in bookings:
            lb.insert(tk.END, f"{b['date']} - {b['time']}")
    
    def logout(self):
        self.destroy()
        LoginRegister()
    
    def create_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        admin_menu = tk.Menu(menubar, tearoff=0)
        admin_menu.add_command(label="Logout", command=self.logout)
        menubar.add_cascade(label="Student", menu=admin_menu)

#Staff Page
class StaffPage(tk.Tk):
    def __init__(self, username):
        data = User.load_all()
        self.bg_color = load_bg_color()
        super().__init__()
        self.username = username
        self.title(f"Student Management System - {username}")
        self.geometry("1350x700+0+0")

        self.title_frame = tk.Frame(self, bg=self.bg_color)
        self.title_frame.pack(side=tk.TOP, fill=tk.X)

        self.title_label = tk.Label(self.title_frame,
                             text=f"Student Management System ({username})",
                             font=("Times New Roman", 25), border=12,
                             relief=tk.GROOVE, bg=self.bg_color)
        self.title_label.pack(side=tk.TOP, fill=tk.X)

        code = tk.Label(self.title_frame, text=f"Class Code: {data['users'][username].get('class_code', 'N/A')}",
                        font=("Times New Roman", 13), bg=self.bg_color)
        code.pack(side=tk.LEFT, padx=10, pady=10)

        session_btn = tk.Button(self.title_frame, text="View Sessions", font=("Times New Roman", 13), command=self.open_sessions_window)
        session_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        logout_btn = tk.Button(self.title_frame, text="Logout", font=("Times New Roman", 13), command=self.logout)
        logout_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        color_btn = tk.Button(self.title_frame, text="Change BG Color", font=("Times New Roman", 13), command=self.change_bg_color)
        color_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.students = User.get_students(username)

        self.detail_frame = tk.LabelFrame(self, text="Enter Details", font=("Times New Roman", 25),
                                        bg=self.bg_color, bd=12, relief=tk.GROOVE)
        self.detail_frame.place(x=20, y=107, width=420, height=575)

        self.data_frame = tk.LabelFrame(self, text="Student List", font=("Times New Roman", 25),
                                        bg=self.bg_color, bd=12, relief=tk.GROOVE)
        self.data_frame.place(x=460, y=107, width=860, height=575)

        search_frame = tk.Frame(self.data_frame, bg=self.bg_color)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(search_frame, text="Search:", bg=self.bg_color, font=("Times New Roman", 12)).pack(side=tk.LEFT, padx=5)
        self.student_search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.student_search_var, font=("Times New Roman", 12), width=25)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.search_students)

        self.create_entry_widgets()
        self.create_buttons()
        self.create_treeview()
        self.refresh_treeview()

        self.mainloop()
    
    def open_sessions_window(self):
        win = tk.Toplevel(self)
        win.title("Session Bookings")
        win.geometry("800x400")

        filename = f"data.json"

        sessions = User.get_sessions(self.username)

        #Treeview
        columns = ("student", "date", "time", "status")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        
        tree.heading("student", text="Student")
        tree.heading("date", text="Date")
        tree.heading("time", text="Time")
        tree.heading("status", text="Status")
        tree.pack(fill=tk.BOTH, expand=True)

        #Insert sessions
        for s in sessions:
            tree.insert("", "end", values=(s["student"], s["date"], s["time"], s["status"]))

        #Buttons for Accept / Decline
        def accept():
            selected = tree.selection()
            if not selected:
                return
            student, date, time, _ = tree.item(selected[0])["values"]
            self.update_session_status(student, date, time, "Accepted")
            tree.item(selected[0], values=(student, date, time, "Accepted"))

        def decline():
            selected = tree.selection()
            if not selected:
                return
            item = tree.item(selected[0])
            student, date, time, _ = item["values"]
            self.update_session_status(filename, student, date, time, "Declined")
            tree.item(selected[0], values=(student, date, time, "Declined"))

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Accept", bg="green", fg="white", width=12, command=accept).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Decline", bg="red", fg="white", width=12, command=decline).pack(side=tk.LEFT, padx=5)

    def update_session_status(self, student, date, time, new_status):
        data = User.load_all()

        student = str(student).strip()
        date = str(date).strip()
        time = str(time).strip()

        for s in data.get("sessions", {}).get(self.username, []):
            if (
                str(s["student"]).strip() == student and
                str(s["date"]).strip() == date and
                str(s["time"]).strip() == time
            ):
                s["status"] = new_status
                break

        User.save_all(data)
    
    def search_students(self, event=None):
        query = self.student_search_var.get().strip().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for s in self.students.values():
            if (query in s.roll_no.lower() or 
                query in s.name.lower() or 
                query in s.class_code.lower()):
                self.tree.insert("", "end", values=(s.roll_no, s.name, s.class_code,
                                                    s.contact, s.address, s.gender, s.dob))

    def logout(self):
        self.destroy()
        LoginRegister()

    def create_entry_widgets(self):
        labels = ["Roll No", "Name", "Class", "Contact", "Address", "Gender", "Birthday", "Password"]
        self.entries = {}
        self.entry_labels = {}

        for i, label in enumerate(labels):
            lbl = tk.Label(self.detail_frame, text=label,
                        font=("Times New Roman", 17), bg=self.bg_color)
            lbl.grid(row=i, column=0, padx=2, pady=2)
            self.entry_labels[label.lower().replace(" ", "_")] = lbl

            if label == "Gender":
                entry = ttk.Combobox(self.detail_frame, font=("Times New Roman", 15), state='readonly')
                entry["values"] = ("Male", "Female", "Others")

            elif label == "Birthday":
                entry = DateEntry(
                    self.detail_frame,
                    font=("Times New Roman", 15),
                    width=15,
                    date_pattern='yyyy-mm-dd',
                    maxdate=date.today()
                )

            elif label == "Password":
                entry = tk.Entry(self.detail_frame, bd=7,
                                font=("Times New Roman", 17),
                                width=12, show="*")

            else:
                entry = tk.Entry(self.detail_frame, bd=7,
                                font=("Times New Roman", 17), width=12)

            entry.grid(row=i, column=1, padx=2, pady=2)
            self.entries[label.lower().replace(" ", "_")] = entry

    def create_buttons(self):
        self.btn_frame = tk.Frame(self.detail_frame, bg=self.bg_color, bd=10, relief=tk.GROOVE)
        self.btn_frame.place(x=20, y=400, width=338, height=77)

        tk.Button(self.btn_frame, text="Add", command=self.add_student, width=21).grid(row=0, column=0, padx=2, pady=2)
        tk.Button(self.btn_frame, text="Update", command=self.update_student, width=21).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(self.btn_frame, text="Delete", command=self.delete_student, width=21).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(self.btn_frame, text="Clear", command=self.clear_entries, width=21).grid(row=1, column=1, padx=2, pady=2)

    def create_treeview(self):
        columns = ("roll_no", "name", "class", "contact", "address", "gender", "birthday")
        self.tree = ttk.Treeview(self.data_frame, columns=columns, show="headings", height=25)
        for col in columns:
            self.tree.heading(
                col,
                text=col.replace("_", " ").title(),
                command=lambda _col=col: self.sort_treeview(self.tree, _col, False)
            )
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def refresh_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in self.students.values():
            self.tree.insert("", "end", values=(s.roll_no, s.name, s.class_code,
                                                s.contact, s.address, s.gender, s.dob))
        self.sort_treeview(self.tree, "roll_no", False)

    def add_student(self):
        roll_no = self.entries['roll_no'].get().strip()
        password = self.entries['password'].get().strip()

        if not roll_no or not password:
            messagebox.showerror("Error", "Roll No and Password are required")
            return

        if roll_no in self.students:
            messagebox.showerror("Error", "Student already exists")
            return

        # Create student profile
        student = Student(
            roll_no,
            self.entries['name'].get().strip(),
            self.entries['class'].get().strip(),
            self.entries['contact'].get().strip(),
            self.entries['address'].get().strip(),
            self.entries['gender'].get().strip(),
            self.entries['birthday'].get().strip()
        )

        self.students[roll_no] = student
        User.save_students(self.username, self.students)

        #Create encrypted student account
        data = User.load_all()
        if "users" not in data:
            data["users"] = {}

        password_data = hash_password(password)

        data["users"][roll_no] = {
            **password_data,
            "role": "Student",
            "class_code": self.entries['class'].get().strip(),
            "created_by": self.username
        }

        User.save_all(data)

        self.refresh_treeview()
        self.clear_entries()

        messagebox.showinfo(
            "Success",
            f"Student account created!\nUsername: {roll_no}"
        )

    def update_student(self):
        roll_no = self.entries['roll_no'].get().strip()
        if roll_no not in self.students:
            messagebox.showerror("Error", "Student not found")
            return
        s = self.students[roll_no]
        s.name = self.entries['name'].get().strip()
        s.class_code = self.entries['class'].get().strip()
        s.contact = self.entries['contact'].get().strip()
        s.address = self.entries['address'].get().strip()
        s.gender = self.entries['gender'].get().strip()
        s.dob = self.entries['birthday'].get().strip()

        User.save_students(self.username, self.students)
        self.refresh_treeview()
        self.clear_entries()
        messagebox.showinfo("Success", f"Student {s.name} updated!")

    def delete_student(self):
        roll_no = self.entries['roll_no'].get().strip()
        if roll_no in self.students:
            del self.students[roll_no]
            User.save_students(self.username, self.students)
            self.refresh_treeview()
            self.clear_entries()
            messagebox.showinfo("Success", "Student deleted!")
        else:
            messagebox.showerror("Error", "Student not found!")

    def clear_entries(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Combobox):
                entry.set('')
            else:
                entry.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            keys = ["roll_no", "name", "class", "contact", "address", "gender", "birthday"]
            for key, value in zip(keys, values):
                entry = self.entries[key]
                if isinstance(entry, ttk.Combobox):
                    entry.set(value)
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, value)
    
    def sort_treeview(self, tree, col, reverse=False):
        #Fetch and sort data
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]) if t[0].replace('.', '', 1).isdigit() else t[0].lower(), reverse=reverse)
        except Exception:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

        #Reinsert in sorted order
        for index, (val, child) in enumerate(data):
            tree.move(child, '', index)

        #Update heading arrows
        for c in tree["columns"]:
            text = c.replace("_", " ").title()
            if c == col:
                text += " ▲" if not reverse else " ▼"
            tree.heading(c, text=text,
                        command=lambda _col=c, _rev=not reverse: self.sort_treeview(tree, _col, _rev))
    
    def change_bg_color(self):
        color_code = colorchooser.askcolor(title="Choose Background Color")
        if color_code and color_code[1]:
            new_color = color_code[1]
            self.bg_color = new_color

            #Update frames
            self.configure(bg=new_color)
            self.detail_frame.configure(bg=new_color)
            self.data_frame.configure(bg=new_color)
            self.title_frame.configure(bg=new_color)
            self.btn_frame.configure(bg=new_color)

            #Update labels
            self.title_label.configure(bg=new_color)
            for lbl in self.entry_labels.values():
                lbl.configure(bg=new_color)

            for child in self.btn_frame.winfo_children():
                if isinstance(child, tk.Button):
                    child.configure(bg=new_color)

            save_bg_color(new_color)

#Admin Page
class AdminPage(tk.Tk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.role = "Admin"

        self.theme = User.get_theme(username)
        self.apply_theme()
        self.configure_ttk_styles()

        self.title(f"Student Management System - {self.username} (Admin)")
        self.geometry("1350x700")

        self.create_title_frame()
        self.create_menubar()
        self.setup_admin_ui()
        self.mainloop()
    
    def configure_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("default")

        if self.theme == "dark":
            field_bg = "#3a3a3a"
            fg = "white"
            bg = "#2b2b2b"
        else:
            field_bg = "white"
            fg = "black"
            bg = "#f0f0f0"

        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=bg,
            foreground=fg,
            arrowcolor=fg
        )
        style.configure(
            "TButton",
            background=bg,
            foreground=fg
        )

    def apply_theme(self):
        if self.theme == "dark":
            self.bg_color = "#2b2b2b"
            self.fg_color = "white"
        else:
            self.bg_color = "#f0f0f0"
            self.fg_color = "black"

        self.configure(bg=self.bg_color)
        self.apply_bg_color(self, self.bg_color)

    def create_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        admin_menu = tk.Menu(menubar, tearoff=0)
        admin_menu.add_command(label="Toggle Light/Dark Mode", command=self.toggle_theme)
        admin_menu.add_separator()
        admin_menu.add_command(label="Logout", command=self.logout)
        menubar.add_cascade(label="Admin", menu=admin_menu)

    def toggle_theme(self):
        """Switch between light and dark themes"""
        self.theme = "dark" if self.theme == "light" else "light"
        User.set_theme(self.username, self.theme)
        self.apply_theme()

    def create_title_frame(self):
        self.title_frame = tk.Frame(self, bg=self.bg_color)
        self.title_frame.pack(side=tk.TOP, fill=tk.X)

        title_label = tk.Label(self.title_frame,
                               text=f"Student Management System ({self.username} - Admin)",
                               font=("Times New Roman", 25),
                               relief=tk.GROOVE, bd=12)
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def logout(self):
        self.destroy()
        LoginRegister()

    def apply_bg_color(self, widget, color):
        try:
            #Skip problematic widgets
            if isinstance(widget, (tkcalendar.Calendar,)):
                return

            #Special handling for DateEntry
            if isinstance(widget, tkcalendar.DateEntry):
                widget.configure(
                    background=color,
                    foreground=self.fg_color,
                    selectbackground=self.fg_color,
                    selectforeground=color
                )
                return

            #LabelFrame special handling
            if isinstance(widget, tk.LabelFrame):
                widget.configure(
                    bg=color,
                    fg=self.fg_color,
                    highlightbackground=self.fg_color,
                    highlightcolor=self.fg_color
                )

            #Frame or Toplevel windows
            elif isinstance(widget, (tk.Frame, tk.Toplevel)):
                widget.configure(bg=color)

            #Label text
            elif isinstance(widget, tk.Label):
                widget.configure(bg=color, fg=self.fg_color)

            #Buttons
            elif isinstance(widget, tk.Button):
                widget.configure(bg=color, fg=self.fg_color, activebackground=color)

            #Entry boxes
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    bg="white" if self.theme == "light" else "#3a3a3a",
                    fg=self.fg_color,
                    insertbackground=self.fg_color
                )

            #ComboBoxes (ttk)
            elif isinstance(widget, ttk.Combobox):
                style = ttk.Style()
                style.theme_use("default")
                style.configure(
                    "TCombobox",
                    fieldbackground="white" if self.theme == "light" else "#3a3a3a",
                    background=color,
                    foreground=self.fg_color
                )

            else:
                #Fallback
                widget.configure(bg=color)

        except Exception:
            pass

        #Recurse into children
        for child in widget.winfo_children():
            self.apply_bg_color(child, color)

    def setup_admin_ui(self):
        #STAFF MANAGEMENT
        staff_frame = tk.LabelFrame(self, text="Staff Accounts", font=("Segoe UI", 14, "bold"), bg=self.bg_color)
        staff_frame.place(x=20, y=70, width=600, height=600)

        staff_search_frame = tk.Frame(staff_frame, bg=self.bg_color)
        staff_search_frame.pack(fill=tk.X, padx=5, pady=(0,5))

        tk.Label(staff_search_frame, text="Search Staff:", bg=self.bg_color).pack(side=tk.LEFT, padx=5)
        self.staff_search_var = tk.StringVar()
        staff_search_entry = tk.Entry(staff_search_frame, textvariable=self.staff_search_var, width=25)
        staff_search_entry.pack(side=tk.LEFT, padx=5)
        staff_search_entry.bind("<KeyRelease>", self.search_staff)

        staff_columns = ("username", "role", "created_by")
        self.staff_tree = ttk.Treeview(staff_frame, columns=staff_columns, show="headings", height=25)
        for col in staff_columns:
            self.staff_tree.heading(col, text=col.title())
            self.staff_tree.column(col, width=180)
        self.staff_tree.pack(fill=tk.BOTH, expand=True)
        self.staff_tree.bind("<<TreeviewSelect>>", lambda e: self.show_staff_students())

        btn_frame = tk.Frame(staff_frame, bg=self.bg_color)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add Staff", command=lambda: self.open_add_staff_window(self)).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Edit Selected Staff", command=lambda: self.open_edit_staff_window(self)).grid(row=0, column=1, padx=5)

        #STUDENT MANAGEMENT
        student_frame = tk.LabelFrame(self, text="Selected Staff's Students",
                                        font=("Segoe UI", 14, "bold"), bg=self.bg_color)
        student_frame.place(x=640, y=70, width=680, height=600)

        #Create a frame for Treeview + scrollbar with fixed height
        tree_frame = tk.Frame(student_frame, bg=self.bg_color)
        tree_frame.pack(fill=tk.X, padx=5, pady=5, ipadx=5, ipady=5)

        student_columns = ("roll_no", "name", "class", "contact", "address", "gender", "birthday")
        self.staff_student_tree = ttk.Treeview(tree_frame, columns=student_columns, show="headings", height=15)

        #Horizontal scrollbar
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.staff_student_tree.xview)
        self.staff_student_tree.configure(xscrollcommand=h_scroll.set)

        #Vertical scrollbar
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.staff_student_tree.yview)
        self.staff_student_tree.configure(yscrollcommand=v_scroll.set)

        #Configure columns
        for col in student_columns:
            self.staff_student_tree.heading(
                col,
                text=col.title(),
                command=lambda _col=col: self.sort_treeview(self.staff_student_tree, _col, False)
            )
            self.staff_student_tree.column(col, width=150, anchor="center")

        student_search_frame = tk.Frame(student_frame, bg=self.bg_color)
        student_search_frame.pack(fill=tk.X, padx=5, pady=(0,5))

        tk.Label(student_search_frame, text="Search Students:", bg=self.bg_color).pack(side=tk.LEFT, padx=5)
        self.admin_student_search_var = tk.StringVar()
        student_search_entry = tk.Entry(student_search_frame, textvariable=self.admin_student_search_var, width=25)
        student_search_entry.pack(side=tk.LEFT, padx=5)
        student_search_entry.bind("<KeyRelease>", self.search_staff_students)
        
        self.staff_student_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.staff_student_tree.bind("<<TreeviewSelect>>", lambda e: self.populate_student_form())

        #Add/Edit student form (fixed height, always visible)
        add_frame = tk.LabelFrame(student_frame, text="Add/Edit Student",
                                bg=self.bg_color, font=("Segoe UI", 12, "bold"))
        add_frame.pack(fill=tk.X, padx=10, pady=5)

        labels = ["Roll No", "Name", "Class", "Contact", "Address", "Gender", "Birthday", "Password"]
        self.admin_student_entries = {}

        #Two-column layout: first 4 fields in left column, remaining 3 in right column
        for i, lbl in enumerate(labels):
            col = 0 if i < 4 else 2
            row = i if i < 4 else i - 4
            tk.Label(add_frame, text=lbl + ":", bg=self.bg_color, font=("Segoe UI", 11)) \
                .grid(row=row, column=col, sticky="e", padx=5, pady=3)
            
            if lbl == "Gender":
                entry = ttk.Combobox(add_frame, values=["Male", "Female", "Others"], state="readonly", width=17)
            elif lbl == "Birthday":
                entry = DateEntry(add_frame, date_pattern="yyyy-mm-dd", width=15, maxdate=date.today())
            elif lbl == "Password":
                entry = tk.Entry(add_frame, show="*", width=20)
            else:
                entry = tk.Entry(add_frame, width=20)
            
            entry.grid(row=row, column=col+1, padx=5, pady=3)
            self.admin_student_entries[lbl.lower().replace(" ", "_")] = entry

        student_btn_frame = tk.Frame(add_frame, bg=self.bg_color)
        student_btn_frame.grid(row=0, column=4, rowspan=4, padx=10, sticky="n")

        tk.Button(student_btn_frame, text="Add Student", bg=self.bg_color, width=15,
                command=lambda: self.admin_add_student(self)).pack(pady=5)
        tk.Button(student_btn_frame, text="Update Selected Student", bg=self.bg_color, width=20,
                command=lambda: self.admin_update_student(self)).pack(pady=5)

        self.refresh_staff_list()
    
    def search_staff(self, event=None):
        data = User.load_all()
        query = self.staff_search_var.get().strip().lower()
        for item in self.staff_tree.get_children():
            self.staff_tree.delete(item)
        for username, info in data["users"].items():
            if info.get("role") == "Staff":
                if (query in username.lower() or query in info.get("created_by", "").lower()):
                    self.staff_tree.insert("", "end", values=(username, info.get("role", "Staff"), info.get("created_by", "system")))
    
    def search_staff_students(self, event=None):
        selected = self.staff_tree.selection()
        if not selected:
            return
        staff_username = self.staff_tree.item(selected[0])["values"][0]

        query = self.admin_student_search_var.get().strip().lower()
        students = User.get_students(staff_username)

        #Clear treeview
        for item in self.staff_student_tree.get_children():
            self.staff_student_tree.delete(item)

        #Insert matching students
        for s in students.values():
            if (query in s.roll_no.lower() or 
                query in s.name.lower() or 
                query in s.class_code.lower()):
                self.staff_student_tree.insert("", "end", values=(s.roll_no, s.name, s.class_code,
                                                                s.contact, s.address, s.gender, s.dob))
        self.sort_treeview(self.staff_student_tree, "roll_no", False)
        
    def sort_treeview(self, tree, col, reverse=False):
        #Fetch and sort data
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]) if t[0].replace('.', '', 1).isdigit() else t[0].lower(), reverse=reverse)
        except Exception:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

        #Reinsert in sorted order
        for index, (val, child) in enumerate(data):
            tree.move(child, '', index)

        #Update heading arrows
        for c in tree["columns"]:
            text = c.replace("_", " ").title()
            if c == col:
                text += " ▲" if not reverse else " ▼"
            tree.heading(c, text=text,
                        command=lambda _col=c, _rev=not reverse: self.sort_treeview(tree, _col, _rev))
    
    def show_staff_students(self):
        selected = self.staff_tree.selection()
        if not selected:
            return
        staff_username = self.staff_tree.item(selected[0])["values"][0]

        #Clear current rows
        for item in self.staff_student_tree.get_children():
            self.staff_student_tree.delete(item)

        students = User.get_students(staff_username)
        for s in students.values():
            self.staff_student_tree.insert(
                "",
                "end",
                values=(
                    s.roll_no,
                    s.name,
                    s.class_code,
                    s.contact,
                    s.address,
                    s.gender,
                    s.dob
                )
            )
        self.sort_treeview(self.staff_student_tree, "roll_no", False)

    #STAFF METHODS
    def delete_staff(self, parent):
        data = User.load_all()
        selected = self.staff_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a staff member to delete.", parent=parent)
            return
        username = self.staff_tree.item(selected[0])["values"][0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete staff '{username}' and all their students?", parent=parent)
        if not confirm:
            return

        #Remove staff and their students
        if username in data["users"]:
            data["users"].pop(username)
            data["students"].pop(username, None)
            save_data()
            messagebox.showinfo("Deleted", f"Staff '{username}' and all their students have been deleted.", parent=parent)
            self.refresh_staff_list()
            for item in self.staff_student_tree.get_children():
                self.staff_student_tree.delete(item)
            self.clear_student_form()
    
    def refresh_staff_list(self):
        data = User.load_all()
        for item in self.staff_tree.get_children():
            self.staff_tree.delete(item)
        for username, info in data["users"].items():
            if info.get("role") == "Staff":
                self.staff_tree.insert("", "end", values=(username, info.get("role", "Staff"), info.get("created_by", "system")))

    def open_add_staff_window(self, parent):
        win = tk.Toplevel(parent)
        win.title("Add New Staff")
        win.geometry("350x250")
        win.configure(bg="white")

        tk.Label(win, text="Username:", bg="white").pack(pady=5)
        username_ent = tk.Entry(win, width=25)
        username_ent.pack(pady=5)

        tk.Label(win, text="Password:", bg="white").pack(pady=5)
        password_ent = tk.Entry(win, show="*", width=25)
        password_ent.pack(pady=5)

        def submit():
            username = username_ent.get().strip()
            password = password_ent.get()
            if not username or not password:
                messagebox.showerror("Error", "All fields are required!", parent=win)
                return
            success, msg = User.register(username, password, "Staff", created_by=self.username)
            if success:
                messagebox.showinfo("Success", msg, parent=win)
                self.refresh_staff_list()
                win.destroy()
            else:
                messagebox.showerror("Error", msg, parent=win)

        tk.Button(win, text="Create", command=submit, bg="#0078D7", fg="white", width=15).pack(pady=20)

    def open_edit_staff_window(self, parent):
        selected = self.staff_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a staff to edit.", parent=parent)
            return
        username = self.staff_tree.item(selected[0])["values"][0]
        win = tk.Toplevel(parent)
        win.title(f"Edit Staff: {username}")
        win.geometry("300x200")
        win.configure(bg="white")

        tk.Label(win, text=f"Change Password for {username}:", bg="white").pack(pady=10)
        password_ent = tk.Entry(win, show="*", width=25)
        password_ent.pack(pady=5)

        def submit():
            data = User.load_all()
            new_pass = password_ent.get().strip()
            if not new_pass:
                messagebox.showerror("Error", "Password cannot be empty.", parent=win)
                return
            data["users"][username]["password"] = new_pass
            messagebox.showinfo("Success", f"Password updated for {username}", parent=win)
            win.destroy()

        tk.Button(win, text="Update", command=submit, bg="#0078D7", fg="white", width=15).pack(pady=20)

    #STUDENT METHODS
    def delete_student(self, parent):
        selected_staff = self.staff_tree.selection()
        if not selected_staff:
            messagebox.showerror("Error", "Select a staff member first.", parent=parent)
            return
        staff_username = self.staff_tree.item(selected_staff[0])["values"][0]

        selected_student = self.staff_student_tree.selection()
        if not selected_student:
            messagebox.showerror("Error", "Select a student to delete.", parent=parent)
            return
        roll_no = self.staff_student_tree.item(selected_student[0])["values"][0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete student '{roll_no}'?", parent=parent)
        if not confirm:
            return

        students = User.get_students(staff_username)
        if roll_no in students:
            students.pop(roll_no)
            User.save_students(staff_username, students)
            messagebox.showinfo("Deleted", f"Student '{roll_no}' deleted.", parent=parent)
            self.show_staff_students()
            self.clear_student_form()
    
    def populate_student_form(self):
        selected = self.staff_student_tree.selection()
        if not selected:
            return

        values = self.staff_student_tree.item(selected[0])['values']
        keys = ["roll_no", "name", "class", "contact", "address", "gender", "birthday"]

        for key, value in zip(keys, values):
            entry = self.admin_student_entries[key]
            if isinstance(entry, ttk.Combobox):
                entry.set(value)
            elif isinstance(entry, DateEntry):
                try:
                    entry.set_date(value)
                except:
                    entry.set_date(date.today())
            else:
                entry.delete(0, tk.END)
                entry.insert(0, value)
    
    def admin_add_student(self, parent):
        data = User.load_all()
        selected_staff = self.staff_tree.selection()
        if not selected_staff:
            messagebox.showerror("Error", "Select a staff member first.", parent=parent)
            return
        
        staff_username = self.staff_tree.item(selected_staff[0])["values"][0]

        roll_no = self.admin_student_entries["roll_no"].get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Roll No is required.", parent=parent)
            return

        password = self.admin_student_entries["password"].get().strip()
        if not password:
            messagebox.showerror("Error", "Password is required.", parent=parent)
            return

        #Check if student account already exists
        if roll_no in data["users"]:
            messagebox.showerror("Error", "A student account with this Roll No already exists.", parent=parent)
            return

        #Load staff's students
        students = User.get_students(staff_username)
        if roll_no in students:
            messagebox.showerror("Error", "Student with this Roll No already exists under this staff.", parent=parent)
            return

        #Create student object
        student = Student(
            roll_no=roll_no,
            name=self.admin_student_entries["name"].get().strip(),
            class_code=self.admin_student_entries["class"].get().strip(),
            contact=self.admin_student_entries["contact"].get().strip(),
            address=self.admin_student_entries["address"].get().strip(),
            gender=self.admin_student_entries["gender"].get().strip(),
            dob=self.admin_student_entries["birthday"].get().strip()
        )

        #Save student under staff
        students[roll_no] = student
        User.save_students(staff_username, students)

        #Create student login account
        data["users"][roll_no] = {
            "password": password,
            "role": "student",
            "owner": staff_username
        }

        messagebox.showinfo("Success", f"Student '{student.name}' added and account created!", parent=parent)

        self.show_staff_students()
        self.clear_student_form()

    def admin_update_student(self, parent):
        selected_staff = self.staff_tree.selection()
        if not selected_staff:
            messagebox.showerror("Error", "Select a staff member first.", parent=parent)
            return
        staff_username = self.staff_tree.item(selected_staff[0])["values"][0]

        roll_no = self.admin_student_entries["roll_no"].get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Roll No is required.", parent=parent)
            return

        students = User.get_students(staff_username)
        if roll_no not in students:
            messagebox.showerror("Error", "Selected student does not exist.", parent=parent)
            return

        student = students[roll_no]
        student.name = self.admin_student_entries["name"].get().strip()
        student.class_code = self.admin_student_entries["class"].get().strip()
        student.contact = self.admin_student_entries["contact"].get().strip()
        student.address = self.admin_student_entries["address"].get().strip()
        student.gender = self.admin_student_entries["gender"].get().strip()
        student.dob = self.admin_student_entries["birthday"].get().strip()

        User.save_students(staff_username, students)
        messagebox.showinfo("Success", f"Student '{student.name}' updated under {staff_username}!", parent=parent)

        self.show_staff_students()
        self.clear_student_form()

    def clear_student_form(self):
        for e in self.admin_student_entries.values():
            if isinstance(e, ttk.Combobox):
                e.set("")
            elif isinstance(e, DateEntry):
                e.set_date(date.today())
            else:
                e.delete(0, tk.END)

if __name__ == "__main__":
    app = LoginRegister()
    app.mainloop()
