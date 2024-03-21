import os
import datetime
import tkinter.ttk as ttk
from tkinter import filedialog
from PyPDF2 import PdfReader

from converters.boa_converter import convert_bank_of_america
from converters.wf_converter import convert_wells_fargo


selected_files = []


def get_pdf_files(frame, convert_button, browse_files_button):
    files = filedialog.askopenfiles(
        title="Select files", initialdir="/", filetypes=[("PDF files", "*.pdf")]
    )
    if files:
        render_files(frame, files, convert_button, browse_files_button)


def render_files(frame, files, convert_button, browse_files_button):
    is_header_rendered = False
    file_info_frames = []
    header_frame = None

    if not is_header_rendered:
        header_frame = create_column_headers(frame)
        is_header_rendered = True

    for i, file in enumerate(files):
        filename = os.path.basename(file.name)
        file_size = os.path.getsize(file.name)
        num_pages = get_num_pages(file.name)
        date_created = get_date_created(file.name)

        file_frame = ttk.Frame(frame)
        file_frame.grid(row=i + 3, column=0, sticky="w", padx=10, pady=5)

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
                f,
                file_info_frames,
                selected_files,
                row,
                is_header_rendered,
                convert_button,
                header_frame,
                browse_files_button,
            ),
        )
        remove_button.grid(row=0, column=4, padx=10, sticky="w")

        file_info_frames.append(file_frame)
        selected_files.append(file.name)

    if files:
        convert_button.grid(row=len(files) + 4, column=0, padx=10, pady=10, sticky="e")
    else:
        convert_button.grid_forget()


def create_column_headers(frame):
    header_frame = ttk.Frame(frame)
    header_frame.grid(row=2, column=0, sticky="w", padx=10, pady=5)

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

    return header_frame


def get_num_pages(file_path):
    with open(file_path, "rb") as f:
        pdf_reader = PdfReader(f)
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


def remove_file(
    file_frame,
    file_info_frames,
    selected_files,
    row,
    column_headers,
    convert_button,
    header_frame,
    browse_files_button,
):
    file_frame.destroy()
    file_info_frames.pop(row)
    selected_files.pop(row)
    if not selected_files:
        for frame in file_info_frames:
            frame.grid_forget()

        column_headers = False
        header_frame.grid_forget()
        convert_button.grid_forget()
        browse_files_button.grid(column=3, row=2, padx=10, pady=10, sticky="e")


def save_csv_file(frame, init_widgets, csv_content):
    filename = filedialog.asksaveasfilename(
        defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
    )
    if filename:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            file.write(csv_content)

        selected_files.clear()
        for widget in frame.winfo_children():
            if widget not in init_widgets:
                widget.grid_forget()


def convert_pdfs_to_csv(
    frame, convert_button, progress_bar, selected_bank, save_button
):
    csv_content = None
    progress_bar.grid(
        row=len(selected_files) + 5, column=0, padx=10, pady=10, sticky="w"
    )
    convert_button.config(state="disabled")
    progress_bar.start()

    bank_svar = selected_bank.get()
    files = selected_files

    if bank_svar == "Bank of America":
        csv_content = convert_bank_of_america(files)
    elif bank_svar == "Wells Fargo":
        csv_content = convert_wells_fargo(files)
    
    progress_bar.stop()
    show_conversion_success(frame)
    convert_button.config(state="enabled")

    if csv_content:
        save_button.grid(
            row=len(selected_files) + 6,
            column=0,
            columnspan=3,
            padx=10,
            pady=10,
            sticky="e",
        )
    else:
        save_button.grid_forget()

    return csv_content


def show_conversion_success(frame):
    success_label = ttk.Label(
        frame, text="PDFs successfully converted!", foreground="green"
    )
    success_label.grid(
         row=len(selected_files) + 5, column=0, padx=10, pady=10, sticky="e"
    )
