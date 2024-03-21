import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import PyPDF2
import datetime

from boa_converter import convert_bank_of_america
from wf_converter import convert_wells_fargo

selected_files = []


def get_selected_files(frame, convert_button):
    files = filedialog.askopenfiles(
        title="Select files", initialdir="/", filetypes=[("PDF files", "*.pdf")]
    )
    if files:
        render_files(frame, files, convert_button)


def render_files(frame, files, convert_button):
    column_headers = False
    file_info_frames = []

    if not column_headers:
        create_column_headers(frame)
        column_headers = True

    for i, file in enumerate(files):
        filename = os.path.basename(file.name)
        file_size = os.path.getsize(file.name)
        num_pages = get_num_pages(file.name)
        date_created = get_date_created(file.name)

        file_frame = ttk.Frame(frame)
        file_frame.grid(column=1, row=i + 3, sticky="w", padx=10, pady=5)

        ttk.Label(
            file_frame, text=filename[:27] + (filename[27:] and "..."), width=30
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(file_frame, text=format_size(file_size), width=10).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(file_frame, text=num_pages, width=10).grid(
            row=0, column=2, sticky="w"
        )
        ttk.Label(
            file_frame, text=get_date_created_display(date_created), width=15
        ).grid(row=0, column=3, sticky="w")

        remove_button = ttk.Button(
            file_frame,
            text="❌",
            command=lambda row=i, f=file_frame: remove_file(
                f, file_info_frames, selected_files, row
            ),
        )
        remove_button.grid(row=0, column=4, padx=(10, 0), sticky="w")

        file_info_frames.append(file_frame)
        selected_files.append(file)

    convert_button.grid(column=1, row=len(files) + 4, padx=10, pady=10, sticky="e")


def create_column_headers(frame):
    header_frame = ttk.Frame(frame)
    header_frame.grid(column=1, row=2, sticky="w", padx=10, pady=5)

    filename_header = ttk.Label(header_frame, text="Filename", width=30)
    filename_header.grid(row=0, column=0, sticky="w")

    size_header = ttk.Label(header_frame, text="Size", width=10)
    size_header.grid(row=0, column=1, sticky="w")

    pages_header = ttk.Label(header_frame, text="Pages", width=10)
    pages_header.grid(row=0, column=2, sticky="w")

    date_header = ttk.Label(header_frame, text="Date Created", width=15)
    date_header.grid(row=0, column=3, sticky="w")

    remove_header = ttk.Label(header_frame, text="Remove", width=15)
    remove_header.grid(row=0, column=4, sticky="w")


def get_num_pages(file_path):
    with open(file_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        num_pages = len(pdf_reader.pages)
    return num_pages


def get_date_created(file_path):
    creation_time = os.path.getctime(file_path)
    return datetime.datetime.fromtimestamp(creation_time)


def get_date_created_display(timestamp):
    return timestamp.strftime("%Y-%m-%d")


def format_size(size_in_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return ""


def remove_file(file_frame, file_info_frames, selected_files, row):
    file_frame.destroy()
    file_info_frames.pop(row)
    selected_files.pop(row)


root = tk.Tk()
frame = ttk.Frame(root, padding=10)
frame.grid()

root.title("Kay Converter")

window_width = 800
window_height = 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2

root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

bank_label = ttk.Label(frame, text="Select Bank:")
bank_label.grid(
    column=1, row=1, padx=(10, 0), pady=5, sticky="w"
)  # Adjust left padding and make sticky="w"
bank_options = ["Bank of America", "Wells Fargo"]
bank_var = tk.StringVar()
bank_dropdown = ttk.Combobox(
    frame, values=bank_options, textvariable=bank_var, state="readonly"
)  # Set state to readonly
bank_dropdown.grid(column=2, row=1, padx=10, pady=5)
bank_dropdown.current(0)

window_label = ttk.Label(frame, text="Select PDF Bank Statements")
window_label.grid(column=1, row=2, padx=10, pady=10)

action_button = ttk.Button(
    frame, text="Browse", command=lambda: get_selected_files(frame, convert_button)
)
action_button.grid(column=3, row=2, padx=10, pady=10)


def convert_pdfs_to_csv():
    bank = bank_var.get()
    files = selected_files
    if bank == "Bank of America":
        convert_bank_of_america(files)
    elif bank == "Wells Fargo":
        convert_wells_fargo(files)
    else:
        print("Unknown bank selected!")


convert_button = ttk.Button(
    frame, text="Convert PDFs to CSV", command=convert_pdfs_to_csv
)
convert_button.grid(
    column=1, row=len(selected_files) + 4, padx=10, pady=10, sticky="e"
)

root.mainloop()
