import customtkinter as ctk
import os
import subprocess
import sys
import shutil
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_FAILED_EXIT_CODE = 2
DATASET_CANCELLED_EXIT_CODE = 130


def get_attendance_module():
    """Import attendance từ thư mục gốc project."""
    sys.path.insert(0, str(BASE_DIR))
    from attendance import get_attendance, get_attendance_dates
    return get_attendance, get_attendance_dates


class AttendanceTab(ctk.CTkFrame):
    """Tab hiển thị bảng điểm danh."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.get_attendance, self.get_attendance_dates = get_attendance_module()
        self._build_ui()

    def _build_ui(self):
        # --- Thanh lọc ngày ---
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(filter_frame, text="Ngày:").pack(side="left", padx=(0, 6))

        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.date_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.date_var,
            values=self._get_date_options(),
            width=160,
            command=lambda _: self.refresh()
        )
        self.date_combo.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filter_frame, text="Tất cả ngày", width=100,
            command=self._show_all
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filter_frame, text="↻ Làm mới", width=90,
            command=self.refresh
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(filter_frame, text="")
        self.count_label.pack(side="right", padx=8)

        # --- Bảng dữ liệu ---
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Attendance.Treeview",
            background="#2b2b2b", foreground="white",
            fieldbackground="#2b2b2b", rowheight=28,
            font=("Arial", 12)
        )
        style.configure("Attendance.Treeview.Heading", font=("Arial", 12, "bold"))
        style.map("Attendance.Treeview", background=[("selected", "#1f6aa5")])

        cols = ("STT", "Họ và tên", "Ngày", "Giờ điểm danh")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            style="Attendance.Treeview"
        )

        col_widths = {"STT": 50, "Họ và tên": 200, "Ngày": 120, "Giờ điểm danh": 140}
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col], anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.refresh()

    def _get_date_options(self):
        try:
            dates = self.get_attendance_dates()
            today = date.today().isoformat()
            if today not in dates:
                dates.insert(0, today)
            return dates
        except Exception:
            return [date.today().isoformat()]

    def _show_all(self):
        self.date_var.set("Tất cả")
        self.refresh()

    def refresh(self):
        # Cập nhật danh sách ngày
        self.date_combo.configure(values=self._get_date_options())

        # Lấy dữ liệu
        selected = self.date_var.get()
        filter_d = None if selected in ("Tất cả", "") else selected

        try:
            rows = self.get_attendance(filter_d)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {e}")
            return

        # Xóa bảng cũ
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Điền dữ liệu mới
        for i, row in enumerate(rows, start=1):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(i, row["name"], row["date"], row["time"]),
                tags=(tag,)
            )

        self.tree.tag_configure("even", background="#323232")
        self.tree.tag_configure("odd",  background="#2b2b2b")

        self.count_label.configure(text=f"Tổng: {len(rows)} lượt")


class MainGUI(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Face Recognition - Nhóm 4")
        self.geometry("620x520")
        ctk.set_appearance_mode("dark")

        # Tiêu đề
        ctk.CTkLabel(
            self,
            text="Hệ thống nhận diện khuôn mặt",
            font=("Arial", 22, "bold")
        ).pack(pady=(18, 8))

        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.tabview.add("Chức năng")
        self.tabview.add("Bảng điểm danh")

        self._build_function_tab(self.tabview.tab("Chức năng"))
        self.attendance_tab = AttendanceTab(self.tabview.tab("Bảng điểm danh"))
        self.attendance_tab.pack(fill="both", expand=True)

        # Refresh bảng điểm danh mỗi khi chuyển tab
        self.tabview.configure(command=self._on_tab_change)

    def _build_function_tab(self, parent):
        ctk.CTkButton(
            parent, text="📷  Thu thập dữ liệu",
            width=260, height=44, font=("Arial", 14),
            command=self.build_dataset
        ).pack(pady=14)

        ctk.CTkButton(
            parent, text="🎯  Nhận diện & Điểm danh",
            width=260, height=44, font=("Arial", 14),
            command=self.recognize_face
        ).pack(pady=6)

        ctk.CTkButton(
            parent, text="🗑  Xóa dữ liệu",
            width=260, height=44, font=("Arial", 14),
            fg_color="#c0392b", hover_color="#96281b",
            command=self.delete_dataset
        ).pack(pady=14)

    def _on_tab_change(self):
        if self.tabview.get() == "Bảng điểm danh":
            self.attendance_tab.refresh()

    def build_dataset(self):
        name = simpledialog.askstring(
            "Nhập tên", "Nhập tên người để thu thập dữ liệu:", parent=self
        )
        if not name or not name.strip():
            if name is not None:
                messagebox.showwarning("Thiếu tên", "Vui lòng nhập tên trước khi thu thập.")
            return

        while True:
            result = subprocess.run(
                [sys.executable, str(BASE_DIR / "build_dataset.py"), name.strip()],
                cwd=BASE_DIR
            )
            if result.returncode == 0:
                subprocess.run(
                    [sys.executable, str(BASE_DIR / "train_model.py"), "--if-needed"],
                    cwd=BASE_DIR
                )
                return
            if result.returncode == DATASET_CANCELLED_EXIT_CODE:
                return
            if result.returncode == DATASET_FAILED_EXIT_CODE:
                continue
            messagebox.showerror("Lỗi", "Thu thập dữ liệu thất bại. Kiểm tra camera hoặc terminal.")
            return

    def recognize_face(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "recognize_face.py")],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        if result.returncode != 0:
            error_output = (result.stderr or result.stdout or "").strip()
            if not error_output:
                error_output = "Khong mo duoc webcam hoac chuong trinh nhan dien da thoat."
            messagebox.showerror("Loi nhan dien", error_output)

        # Sau khi đóng cửa sổ nhận diện, tự refresh bảng
        self.attendance_tab.refresh()

    def delete_dataset(self):
        if not messagebox.askyesno(
            "Xác nhận xóa",
            "Bạn có chắc chắn muốn xóa tất cả dữ liệu trong thư mục dataset?\nHành động này không thể hoàn tác."
        ):
            return

        dataset_path = BASE_DIR / "dataset"
        if dataset_path.exists():
            try:
                shutil.rmtree(dataset_path)
                dataset_path.mkdir(parents=True, exist_ok=True)
                messagebox.showinfo("Thành công", "Đã xóa tất cả dữ liệu thành công.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa dữ liệu: {e}")
        else:
            messagebox.showinfo("Thông báo", "Thư mục dataset không tồn tại hoặc đã trống.")
 
    def delete_dataset(self):
        action = self._choose_delete_action()
        if action == "images":
            self._delete_images()
        elif action == "attendance":
            self._delete_attendance()

    def _choose_delete_action(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Chọn dữ liệu cần xóa")
        dialog.geometry("360x190")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        choice = tk.StringVar(value="")

        ctk.CTkLabel(
            dialog,
            text="Bạn muốn xóa dữ liệu nào?",
            font=("Arial", 16, "bold")
        ).pack(pady=(22, 14))

        ctk.CTkButton(
            dialog,
            text="Xóa ảnh",
            width=240,
            height=36,
            fg_color="#c0392b",
            hover_color="#96281b",
            command=lambda: self._close_delete_dialog(dialog, choice, "images")
        ).pack(pady=6)

        ctk.CTkButton(
            dialog,
            text="Xóa dữ liệu điểm danh",
            width=240,
            height=36,
            fg_color="#c0392b",
            hover_color="#96281b",
            command=lambda: self._close_delete_dialog(dialog, choice, "attendance")
        ).pack(pady=6)

        ctk.CTkButton(
            dialog,
            text="Hủy",
            width=240,
            height=32,
            fg_color="#555555",
            hover_color="#444444",
            command=dialog.destroy
        ).pack(pady=(8, 0))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_window()
        return choice.get()

    def _close_delete_dialog(self, dialog, choice, value):
        choice.set(value)
        dialog.destroy()

    def _delete_images(self):
        if not messagebox.askyesno(
            "Xác nhận xóa ảnh",
            "Bạn có chắc chắn muốn xóa tất cả ảnh trong dataset và model đã train?\nHành động này không thể hoàn tác."
        ):
            return

        dataset_path = BASE_DIR / "dataset"
        trainer_path = BASE_DIR / "trainer"

        try:
            if dataset_path.exists():
                shutil.rmtree(dataset_path)
            dataset_path.mkdir(parents=True, exist_ok=True)

            for model_name in ("face_model.pkl", "face_model.yml"):
                model_path = trainer_path / model_name
                if model_path.exists():
                    model_path.unlink()

            messagebox.showinfo("Thanh cong", "Da xoa anh va model da train.")
        except Exception as e:
            messagebox.showerror("Loi", f"Khong the xoa anh: {e}")

    def _delete_attendance(self):
        if not messagebox.askyesno(
            "Xác nhận xóa điểm danh",
            "Bạn có chắc chắn muốn xóa tất cả dữ liệu điểm danh?\nHành động này không thể hoàn tác."
        ):
            return

        try:
            sys.path.insert(0, str(BASE_DIR))
            from attendance import clear_attendance

            clear_attendance()
            self.attendance_tab.refresh()
            messagebox.showinfo("Thanh cong", "Đã xóa dữ liệu điểm danh.")
        except Exception as e:
            messagebox.showerror("Loi", f"Không thể xóa dữ liệu điểm danh: {e}")


app = MainGUI()
app.mainloop()
