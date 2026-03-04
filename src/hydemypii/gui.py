from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


class HydeMyPIIGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Hyde My PII - Sanitize Documents")
        self.root.geometry("850x650")
        self.root.resizable(True, True)

        self._setup_ui()
        self._processing = False

    def _setup_ui(self) -> None:
        # Status bar - pack first so it stays at bottom
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            header_frame,
            text="Hyde My PII",
            font=("Arial", 16, "bold"),
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            header_frame,
            text="Replace sensitive information with fake data",
            font=("Arial", 10),
        )
        subtitle_label.pack()

        # Input section
        input_frame = ttk.LabelFrame(self.root, text="Input", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="File or Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_path_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path_var, width=60)
        input_entry.grid(row=0, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Browse File", command=self._browse_file, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Browse Folder", command=self._browse_folder, width=13).pack(side=tk.LEFT, padx=2)

        # Output section
        output_frame = ttk.LabelFrame(self.root, text="Output", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_path_var = tk.StringVar(value="./sanitized")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=60)
        output_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse", command=self._browse_output, width=12).grid(row=0, column=2, padx=5)

        # Options section
        options_frame = ttk.LabelFrame(self.root, text="Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        self.ocr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Enable OCR (for scanned PDFs and images)", variable=self.ocr_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=2
        )

        self.all_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Process all files (not only known extensions)", variable=self.all_files_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=2
        )

        ttk.Label(options_frame, text="OCR Language:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.ocr_lang_var = tk.StringVar(value="auto")
        ocr_lang_combo = ttk.Combobox(
            options_frame,
            textvariable=self.ocr_lang_var,
            values=["auto", "eng", "pol", "deu", "fra", "spa", "ita", "por"],
            width=10,
            state="readonly",
        )
        ocr_lang_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(options_frame, text="Faker Locale:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.locale_var = tk.StringVar(value="en_US")
        locale_combo = ttk.Combobox(
            options_frame,
            textvariable=self.locale_var,
            values=["en_US", "pl_PL", "de_DE", "fr_FR", "es_ES", "it_IT", "pt_BR"],
            width=10,
            state="readonly",
        )
        locale_combo.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Progress section
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.progress_text = scrolledtext.ScrolledText(
            progress_frame,
            height=12,
            width=90,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 9),
        )
        self.progress_text.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)

        self.process_btn = ttk.Button(
            action_frame,
            text="Sanitize Files",
            command=self._process_files,
            style="Accent.TButton",
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

    def _browse_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[
                ("All Supported", "*.pdf;*.txt;*.docx;*.png;*.jpg;*.jpeg"),
                ("PDF files", "*.pdf"),
                ("Text files", "*.txt"),
                ("Word documents", "*.docx"),
                ("Images", "*.png;*.jpg;*.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.input_path_var.set(filename)

    def _browse_folder(self) -> None:
        foldername = filedialog.askdirectory(title="Select a folder")
        if foldername:
            self.input_path_var.set(foldername)

    def _browse_output(self) -> None:
        foldername = filedialog.askdirectory(title="Select output folder")
        if foldername:
            self.output_path_var.set(foldername)

    def _clear_log(self) -> None:
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.config(state=tk.DISABLED)

    def _log(self, message: str) -> None:
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _process_files(self) -> None:
        if self._processing:
            return

        input_path_str = self.input_path_var.get().strip()
        if not input_path_str:
            messagebox.showerror("Error", "Please select an input file or folder")
            return

        input_path = Path(input_path_str)
        if not input_path.exists():
            messagebox.showerror("Error", f"Input path does not exist:\n{input_path}")
            return

        output_path = Path(self.output_path_var.get().strip())

        self._processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set("Processing...")
        self._clear_log()

        def worker() -> None:
            try:
                from hydemypii.cli import _collect_files
                from hydemypii.extractor import extract_text
                from hydemypii.redactor import PIIRedactor

                redactor = PIIRedactor(locale=self.locale_var.get())
                files = _collect_files(input_path, include_unknown=self.all_files_var.get())

                if not files:
                    self._log("No files found to process.")
                    self.status_var.set("No files found")
                    return

                self._log(f"Found {len(files)} file(s) to process\n")

                processed = 0
                total_replacements = 0

                for file_path in files:
                    self._log(f"Processing: {file_path.name}")

                    extraction = extract_text(
                        file_path,
                        ocr_enabled=self.ocr_var.get(),
                        ocr_lang=self.ocr_lang_var.get(),
                        poppler_path=None,
                    )

                    if not extraction.text.strip():
                        warnings = "; ".join(extraction.warnings) if extraction.warnings else "No text extracted"
                        self._log(f"  [SKIP] {warnings}\n")
                        continue

                    result = redactor.redact(extraction, output_dir=output_path)
                    processed += 1
                    total_replacements += result.replacements_count

                    ocr_tag = " [OCR]" if result.used_ocr else ""
                    self._log(f"  [OK] {result.replacements_count} replacements{ocr_tag}")
                    self._log(f"  Output: {result.output_path}\n")

                    if result.warnings:
                        self._log(f"  Warnings: {'; '.join(result.warnings)}\n")

                summary = f"Done! Processed {processed}/{len(files)} files. Total replacements: {total_replacements}"
                self._log(f"\n{summary}")
                self.status_var.set(summary)
                messagebox.showinfo("Complete", summary)

            except Exception as e:
                error_msg = f"Error: {e}"
                self._log(f"\n{error_msg}")
                self.status_var.set("Error occurred")
                messagebox.showerror("Error", error_msg)
            finally:
                self._processing = False
                self.process_btn.config(state=tk.NORMAL)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


def main() -> int:
    root = tk.Tk()
    
    # Try to set a modern theme
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except Exception:
        pass  # Fall back to default theme

    app = HydeMyPIIGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
