import tkinter as tk
import tkinter.ttk as ttk

from ui.files import convert_pdfs_to_csv, get_pdf_files, save_csv_file


def main():
    window = tk.Tk()
    window.title("Kay Converter")
    window_width = 800
    window_height = 600
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_x_position = (screen_width - window_width) // 2
    window_y_position = (screen_height - window_height) // 2
    window.geometry(
        f"{window_width}x{window_height}+{window_x_position}+{window_y_position}"
    )

    root_frame = ttk.Frame(window, padding=10)
    root_frame.grid()

    prompt_frame = ttk.Frame(root_frame)
    prompt_frame.grid(row=1, column=1)

    results_frame = ttk.Frame(root_frame)
    results_frame.grid(row=2, column=1)

    bank_label = ttk.Label(master=prompt_frame, text="Select Bank:")
    bank_label.grid(column=1, row=1, padx=(10, 0), pady=5, sticky="w")
    bank_options = ["Bank of America", "Wells Fargo"]
    bank_str_var = tk.StringVar()
    bank_dropdown = ttk.Combobox(
        master=prompt_frame,
        values=bank_options,
        textvariable=bank_str_var,
        state="readonly",
    )
    bank_dropdown.grid(column=2, row=1, padx=10, pady=5, sticky="w")
    bank_dropdown.current(0)

    browse_files_label = ttk.Label(
        master=prompt_frame, text="Select PDF Bank Statements"
    )
    browse_files_label.grid(column=1, row=2, padx=10, pady=10, sticky="w")
    browse_files_button = ttk.Button(
        master=prompt_frame,
        text="Browse",
        command=lambda: get_pdf_files(
            prompt_frame, convert_button, browse_files_button
        ),
    )
    browse_files_button.grid(column=3, row=2, padx=10, pady=10, sticky="e")

    convert_button = ttk.Button(
        master=results_frame,
        text="Convert PDFs to CSV",
        command=lambda: convert_pdfs_to_csv(
            frame=results_frame,
            selected_bank=bank_str_var,
            convert_button=convert_button,
            progress_bar=conversion_progress_bar,
            save_button=save_button,
        ),
    )

    conversion_progress_bar = ttk.Progressbar(
        results_frame, orient="horizontal", length=200, mode="determinate"
    )

    save_button = ttk.Button(
        master=results_frame,
        text="Save CSV",
        command=lambda: save_csv_file(
            frame=results_frame,
            init_widgets=[
                bank_label,
                bank_dropdown,
                browse_files_label,
                browse_files_button,
            ],
            csv_content=convert_pdfs_to_csv(
                frame=results_frame,
                selected_bank=bank_str_var,
                convert_button=convert_button,
                progress_bar=conversion_progress_bar,
                save_button=save_button,
            ),
        ),
    )

    window.mainloop()


if __name__ == "__main__":
    main()
