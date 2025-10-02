import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import json
from pathlib import Path
import queue
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AIvengersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AIvengers - Resume Processing Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')

        # Create main canvas and scrollbar for the entire app
        self.main_canvas = tk.Canvas(
            self.root, bg='#1a1a1a', highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(
            self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg='#1a1a1a')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all"))
        )

        self.main_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        # Pack main canvas and scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        self.main_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Colors
        self.bg_color = '#1a1a1a'
        self.green_color = '#00ff00'
        self.white_color = '#ffffff'
        self.yellow_color = '#ffff00'
        self.red_color = '#ff0000'
        self.hover_green = '#33ff33'

        # State variables
        self.resume_folder_path = ""
        self.job_description_path = ""
        self.current_process = None
        self.process_queue = queue.Queue()

        # Language support
        self.current_language = "en"  # Default to English
        self.translations = {
            "en": {
                "extract": "Extract",
                "extract_desc": "Parse and extract information from resumes",
                "choose_resumes": "Choose resumes folder",
                "start_extract": "Start Extracting",
                "start_extracting": "Start Extracting",
                "job_description": "Job Description",
                "job_description_desc": "Create job profile from description PDF",
                "job_desc_desc": "Create job profile from description PDF",
                "choose_job_desc": "Choose job description PDF",
                "start_job_description": "Start Job Descriptioning",
                "start_job_desc": "Start Job Descriptioning",
                "enrich": "Enrich",
                "enrich_desc": "Enhance resumes with additional insights",
                "start_enrich": "Start Enriching",
                "start_enriching": "Start Enriching",
                "score": "Score",
                "score_desc": "Evaluate and score candidate profiles",
                "start_score": "Start Scoring",
                "start_scoring": "Start Scoring",
                "rank": "Rank",
                "rank_desc": "Rank candidates based on requirements",
                "start_rank": "Start Ranking",
                "start_ranking": "Start Ranking",
                "results": "Results",
                "resume_name": "Resume Name",
                "score_col": "Score",
                "details": "Details",
                "no_file_selected": "No file selected",
                "processing": "Processing...",
                "completed": "Completed successfully!",
                "ai_analysis": "AI Analysis",
                "subtitle": "Do you want to hire the best person??",
                "tagline2": "So call AIvengers"
            },
            "fa": {
                "extract": "استخراج",
                "extract_desc": "استخراج و تجزیه اطلاعات از رزومه‌ها",
                "choose_resumes": "انتخاب پوشه رزومه‌ها",
                "start_extract": "شروع استخراج",
                "start_extracting": "شروع استخراج",
                "job_description": "شرح شغل",
                "job_description_desc": "ایجاد پروفایل شغل از فایل PDF",
                "job_desc_desc": "ایجاد پروفایل شغل از فایل PDF",
                "choose_job_desc": "انتخاب فایل شرح شغل",
                "start_job_description": "شروع ایجاد شرح شغل",
                "start_job_desc": "شروع ایجاد شرح شغل",
                "enrich": "غنی‌سازی",
                "enrich_desc": "بهبود رزومه‌ها با بینش‌های اضافی",
                "start_enrich": "شروع غنی‌سازی",
                "start_enriching": "شروع غنی‌سازی",
                "score": "امتیازدهی",
                "score_desc": "ارزیابی و امتیازدهی پروفایل‌های کاندیدا",
                "start_score": "شروع امتیازدهی",
                "start_scoring": "شروع امتیازدهی",
                "rank": "رتبه‌بندی",
                "rank_desc": "رتبه‌بندی کاندیداها بر اساس نیازمندی‌ها",
                "start_rank": "شروع رتبه‌بندی",
                "start_ranking": "شروع رتبه‌بندی",
                "results": "نتایج",
                "resume_name": "نام رزومه",
                "score_col": "امتیاز",
                "details": "جزئیات",
                "no_file_selected": "فایلی انتخاب نشده",
                "processing": "در حال پردازش...",
                "completed": "با موفقیت تکمیل شد!",
                "ai_analysis": "تحلیل هوش مصنوعی",
                "subtitle": "آیا می‌خواهید بهترین فرد را استخدام کنید؟؟",
                "tagline2": "پس با AIvengers تماس بگیرید"
            }
        }

        # Create GUI
        self.create_header()
        self.create_process_steps()
        self.create_results_display()

        # Start queue processor
        self.process_queue_events()

    def _on_mousewheel(self, event):
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_header(self):
        # Main title frame
        title_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        title_frame.pack(pady=30)

        # AIvengers title with different colors for AI and vengers
        title_frame_inner = tk.Frame(title_frame, bg=self.bg_color)
        title_frame_inner.pack()

        ai_label = tk.Label(
            title_frame_inner,
            text="AI",
            font=("Arial", 48, "bold"),
            bg=self.bg_color,
            fg=self.green_color
        )
        ai_label.pack(side='left')

        vengers_label = tk.Label(
            title_frame_inner,
            text="vengers",
            font=("Arial", 48, "bold"),
            bg=self.bg_color,
            fg=self.white_color
        )
        vengers_label.pack(side='left')

        # Taglines
        tagline1 = tk.Label(
            title_frame,
            text="Do you want to hire the best person??",
            font=("Arial", 20),
            bg=self.bg_color,
            fg=self.white_color
        )
        tagline1.pack(pady=(10, 5))
        self.tagline1 = tagline1  # Store reference for language switching

        # tagline2 = tk.Label(
        #     title_frame,
        #     text="So call AIvengers",
        #     font=("Arial", 16),
        #     bg=self.bg_color,
        #     fg=self.green_color
        # )
        # tagline2.pack()
        # self.tagline2 = tagline2  # Store reference for language switching

        # Underline
        underline = tk.Frame(title_frame, height=2, bg=self.green_color)
        underline.pack(fill='x', pady=(10, 0), padx=50)

        # Language switcher
        lang_frame = tk.Frame(title_frame, bg=self.bg_color)
        lang_frame.pack(pady=(20, 0))

        self.lang_btn = tk.Button(
            lang_frame,
            text="🌍",
            font=("Arial", 16),
            bg=self.bg_color,
            fg=self.green_color,
            relief='flat',
            bd=0,
            command=self.toggle_language,
            cursor='hand2'
        )
        self.lang_btn.pack()

        # Language label
        self.lang_label = tk.Label(
            lang_frame,
            text="English",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.white_color
        )
        self.lang_label.pack()

    def toggle_language(self):
        """Toggle between English and Persian"""
        self.current_language = "fa" if self.current_language == "en" else "en"
        self.update_language()

    def update_language(self):
        """Update all text elements to current language"""
        lang = self.current_language

        # Update language label
        self.lang_label.configure(text="English" if lang == "en" else "فارسی")

        # Update subtitle
        if hasattr(self, 'tagline1'):
            self.tagline1.configure(text=self.translations[lang]["subtitle"])

        # Update all step cards
        if hasattr(self, 'extract_card'):
            self.update_card_text(self.extract_card, "extract")
        if hasattr(self, 'job_desc_card'):
            self.update_card_text(self.job_desc_card, "job_description")
        if hasattr(self, 'enrich_card'):
            self.update_card_text(self.enrich_card, "enrich")
        if hasattr(self, 'score_card'):
            self.update_card_text(self.score_card, "score")
        if hasattr(self, 'rank_card'):
            self.update_card_text(self.rank_card, "rank")

        # Update results section
        if hasattr(self, 'results_title'):
            self.results_title.configure(
                text=self.translations[lang]["results"])

        # Update table headers
        if hasattr(self, 'results_tree'):
            self.results_tree.heading(
                'Name', text=self.translations[lang]["resume_name"])
            self.results_tree.heading(
                'Score', text=self.translations[lang]["score_col"])
            self.results_tree.heading(
                'Details', text=self.translations[lang]["details"])

    def update_card_text(self, card, card_type):
        """Update text in a specific card"""
        lang = self.current_language
        t = self.translations[lang]

        # Update title
        if hasattr(card, 'title_label'):
            card.title_label.configure(text=t[card_type])

        # Update description
        if hasattr(card, 'desc_label'):
            card.desc_label.configure(text=t[f"{card_type}_desc"])

        # Update button text
        if hasattr(card, 'start_btn'):
            card.start_btn.configure(text=t[f"start_{card_type}"])

        # Update file selection button
        if hasattr(card, 'file_btn'):
            if card_type == "extract":
                card.file_btn.configure(text=t["choose_resumes"])
            elif card_type == "job_description":
                card.file_btn.configure(text=t["choose_job_desc"])

        # Update path label
        if hasattr(card, 'path_label'):
            if card.path_label.cget("text") == "No file selected" or card.path_label.cget("text") == "فایلی انتخاب نشده":
                card.path_label.configure(text=t["no_file_selected"])

    def create_process_steps(self):
        # Process steps frame
        steps_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        steps_frame.pack(pady=40, padx=20)

        # First row
        first_row = tk.Frame(steps_frame, bg=self.bg_color)
        first_row.pack()

        # Extract step
        self.extract_card = self.create_step_card(
            first_row, "extract", "extract_desc",
            "📄", self.on_extract_click, 0
        )

        # Job Description step
        self.job_desc_card = self.create_step_card(
            first_row, "job_description", "job_desc_desc",
            "📋", self.on_job_desc_click, 1
        )

        # Enrich step
        self.enrich_card = self.create_step_card(
            first_row, "enrich", "enrich_desc",
            "✨", self.on_enrich_click, 2
        )

        # Score step
        self.score_card = self.create_step_card(
            first_row, "score", "score_desc",
            "🎯", self.on_score_click, 3
        )

        # Second row - Rank (full width)
        second_row = tk.Frame(steps_frame, bg=self.bg_color)
        second_row.pack(pady=(20, 0))

        self.rank_card = self.create_step_card(
            second_row, "rank", "rank_desc",
            "🏆", self.on_rank_click, 4, full_width=True
        )

    def create_step_card(self, parent, title_key, desc_key, icon, command, step_num, full_width=False):
        # Card frame
        card_frame = tk.Frame(
            parent,
            bg=self.bg_color,
            relief='solid',
            bd=2,
            highlightbackground=self.green_color,
            highlightthickness=2
        )

        if full_width:
            card_frame.pack(fill='x', padx=10, pady=5)
        else:
            card_frame.pack(side='left', padx=10, pady=5,
                            fill='both', expand=True)

        # Icon
        icon_label = tk.Label(
            card_frame,
            text=icon,
            font=("Arial", 24),
            bg=self.bg_color,
            fg=self.green_color
        )
        icon_label.pack(pady=(20, 10))

        # Title
        title_label = tk.Label(
            card_frame,
            text=self.translations[self.current_language][title_key],
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
            fg=self.green_color
        )
        title_label.pack()
        card_frame.title_label = title_label  # Store reference

        # Description
        desc_label = tk.Label(
            card_frame,
            text=self.translations[self.current_language][desc_key],
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.white_color,
            wraplength=200
        )
        desc_label.pack(pady=(5, 10), padx=10)
        card_frame.desc_label = desc_label  # Store reference

        # File selection button (for extract and job description)
        if step_num in [0, 1]:  # Extract and Job Description
            file_btn_text = self.translations[self.current_language][
                "choose_resumes"] if step_num == 0 else self.translations[self.current_language]["choose_job_desc"]
            file_btn = tk.Button(
                card_frame,
                text=file_btn_text,
                command=lambda: self.select_file(step_num),
                bg=self.bg_color,
                fg=self.white_color,
                relief='solid',
                bd=1,
                highlightbackground=self.green_color,
                highlightthickness=1,
                font=("Arial", 9)
            )
            file_btn.pack(pady=(0, 10), padx=10, fill='x')

            # File path label
            path_label = tk.Label(
                card_frame,
                text=self.translations[self.current_language]["no_file_selected"],
                font=("Arial", 8),
                bg=self.bg_color,
                fg=self.white_color,
                wraplength=200
            )
            path_label.pack(pady=(0, 10))

            # Store references
            card_frame.path_label = path_label
            card_frame.file_btn = file_btn

        # Start button
        start_btn = tk.Button(
            card_frame,
            text=self.translations[self.current_language][f"start_{title_key}"],
            command=command,
            bg=self.green_color,
            fg=self.white_color,
            relief='flat',
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        start_btn.pack(pady=(0, 20))
        card_frame.start_btn = start_btn  # Store reference

        # Progress label
        progress_label = tk.Label(
            card_frame,
            text="",
            font=("Arial", 9),
            bg=self.bg_color,
            fg=self.white_color
        )
        progress_label.pack(pady=(0, 5))

        # Progress bar (hidden by default) - using custom canvas for better visibility
        progress_canvas = tk.Canvas(
            card_frame,
            width=200,
            height=20,
            bg=self.bg_color,
            highlightthickness=0
        )
        progress_canvas.pack(pady=(0, 10))
        progress_canvas.pack_forget()  # Hide initially

        # Create progress bar elements
        progress_canvas.bg_rect = progress_canvas.create_rectangle(
            0, 0, 200, 20, fill='#333333', outline='#666666')
        progress_canvas.progress_rect = progress_canvas.create_rectangle(
            0, 0, 0, 20, fill=self.green_color, outline='')

        # Store references
        card_frame.start_btn = start_btn
        card_frame.progress_label = progress_label
        card_frame.progress_bar = progress_canvas
        card_frame.step_num = step_num

        # Hover effects
        self.add_hover_effects(card_frame, start_btn)

        return card_frame

    def add_hover_effects(self, card_frame, button):
        def on_enter(event):
            card_frame.configure(highlightbackground=self.hover_green)
            button.configure(bg=self.hover_green)

        def on_leave(event):
            card_frame.configure(highlightbackground=self.green_color)
            button.configure(bg=self.green_color)

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def select_file(self, step_num):
        if step_num == 0:  # Extract - select folder
            folder_path = filedialog.askdirectory(
                title="Select Resumes Folder")
            if folder_path:
                self.resume_folder_path = folder_path
                self.extract_card.path_label.configure(
                    text=f"Selected: {os.path.basename(folder_path)}")
        elif step_num == 1:  # Job Description - select PDF
            file_path = filedialog.askopenfilename(
                title="Select Job Description PDF",
                filetypes=[("PDF files", "*.pdf")]
            )
            if file_path:
                self.job_description_path = file_path
                self.job_desc_card.path_label.configure(
                    text=f"Selected: {os.path.basename(file_path)}")

    def create_results_display(self):
        # Results frame
        results_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        results_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Results title
        results_title = tk.Label(
            results_frame,
            text=self.translations[self.current_language]["results"],
            font=("Arial", 18, "bold"),
            bg=self.bg_color,
            fg=self.green_color
        )
        results_title.pack(anchor='w')
        self.results_title = results_title  # Store reference

        # Create table frame with green border
        table_container = tk.Frame(
            results_frame, bg=self.green_color, relief='solid', bd=2)
        table_container.pack(pady=(10, 0), padx=20, fill='x')

        # Create table constraint frame
        table_constraint = tk.Frame(
            table_container, bg='#2a2a2a', relief='flat', bd=0)
        table_constraint.pack(expand=True, fill='both', padx=2, pady=2)

        # Create Treeview for table
        columns = ('Name', 'Score', 'Details')
        self.results_tree = ttk.Treeview(
            table_constraint, columns=columns, show='headings', height=15)

        # Configure columns
        self.results_tree.heading(
            'Name', text=self.translations[self.current_language]["resume_name"])
        self.results_tree.heading(
            'Score', text=self.translations[self.current_language]["score_col"])
        self.results_tree.heading(
            'Details', text=self.translations[self.current_language]["details"])

        self.results_tree.column('Name', width=400, anchor='w')
        self.results_tree.column('Score', width=120, anchor='center')
        self.results_tree.column('Details', width=100, anchor='center')

        # Custom dark theme styling
        style = ttk.Style()
        style.theme_use('clam')

        # Configure Treeview styling
        style.configure("Treeview",
                        background='#2a2a2a',
                        foreground='white',
                        fieldbackground='#2a2a2a',
                        borderwidth=0,
                        font=('Arial', 10))

        # Configure Treeview headings
        style.configure("Treeview.Heading",
                        background='#333333',
                        foreground=self.green_color,
                        font=('Arial', 11, 'bold'),
                        borderwidth=0)

        # Configure Treeview selection
        style.map("Treeview",
                  background=[('selected', '#404040')],
                  foreground=[('selected', 'white')])

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_constraint, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.results_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Add click handler for details
        self.results_tree.bind("<Button-1>", self.on_table_click)

        # Store reference for later use
        self.results_text = None  # We'll use the treeview instead

    def on_table_click(self, event):
        """Handle clicks on the results table"""
        item = self.results_tree.identify_row(event.y)
        column = self.results_tree.identify_column(event.x)

        if item and column == "#3":  # Details column
            # Get the resume name from the first column
            resume_name = self.results_tree.item(item, "values")[0]
            # Remove the document icon prefix
            clean_name = resume_name.replace("📄 ", "")

            # Show AI reason popup
            self.show_ai_reason_popup(clean_name)

    def load_ai_reasons(self):
        """Load AI reasons from scored_ai.jsonl"""
        ai_reasons = {}
        try:
            with open("out/scored_ai.jsonl", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        filename = data.get("source_file", "")
                        ai_reason = data.get("ai_reason", "")
                        if filename and ai_reason:
                            # Remove .pdf extension for matching
                            clean_filename = filename.replace('.pdf', '')
                            ai_reasons[clean_filename] = ai_reason
        except Exception as e:
            print(f"Error loading AI reasons: {e}")

        return ai_reasons

    def show_ai_reason_popup(self, resume_name):
        """Show AI reason in a popup window"""
        # Load AI reasons
        ai_reasons = self.load_ai_reasons()

        # Find matching AI reason
        ai_reason = ai_reasons.get(
            resume_name, "AI reason not found for this resume.")

        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"AI Analysis - {resume_name}")
        popup.geometry("800x600")
        popup.configure(bg=self.bg_color)

        # Center the popup
        popup.transient(self.root)
        popup.grab_set()

        # Title
        title_label = tk.Label(
            popup,
            text=f"AI Analysis for {resume_name}",
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
            fg=self.green_color
        )
        title_label.pack(pady=20)

        # AI reason text with scrollbar
        text_frame = tk.Frame(popup, bg=self.bg_color)
        text_frame.pack(fill='both', expand=True, padx=20, pady=10)

        text_widget = tk.Text(
            text_frame,
            wrap='word',
            font=("Tahoma", 12),  # Better Persian font support
            bg='#2a2a2a',
            fg='white',
            insertbackground='white',
            selectbackground=self.green_color,
            selectforeground='white',
            padx=15,
            pady=15
        )

        scrollbar = tk.Scrollbar(
            text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Insert AI reason text
        text_widget.insert('1.0', ai_reason)

        # Configure for RTL text (Persian)
        text_widget.tag_configure("rtl", justify='right')
        text_widget.tag_add("rtl", "1.0", "end")

        text_widget.config(state='disabled')  # Make read-only

        # Pack text widget and scrollbar
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Close button
        close_btn = tk.Button(
            popup,
            text="Close",
            command=popup.destroy,
            bg=self.green_color,
            fg='white',
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        close_btn.pack(pady=20)

    def set_processing_state(self, card, is_processing, is_done=False, is_warning=False):
        if is_processing:
            card.configure(highlightbackground=self.yellow_color)
            card.start_btn.configure(
                bg=self.yellow_color, text="Processing...")
            for child in card.winfo_children():
                if isinstance(child, tk.Label) and child.cget('fg') == self.green_color:
                    child.configure(fg=self.yellow_color)
        elif is_done:
            card.configure(highlightbackground=self.red_color)
            card.start_btn.configure(bg=self.red_color, text="Done!")
            for child in card.winfo_children():
                if isinstance(child, tk.Label) and child.cget('fg') == self.yellow_color:
                    child.configure(fg=self.red_color)
        elif is_warning:
            card.configure(highlightbackground=self.yellow_color)
            card.start_btn.configure(bg=self.yellow_color, text="Warning!")
            for child in card.winfo_children():
                if isinstance(child, tk.Label) and child.cget('fg') == self.green_color:
                    child.configure(fg=self.yellow_color)
        else:
            card.configure(highlightbackground=self.green_color)
            card.start_btn.configure(bg=self.green_color)
            for child in card.winfo_children():
                if isinstance(child, tk.Label) and child.cget('fg') in [self.red_color, self.yellow_color]:
                    child.configure(fg=self.green_color)

    def update_progress(self, card, message):
        card.progress_label.configure(text=message)
        self.root.update_idletasks()

        # Also update the results text for better visibility
        if "Enriched" in message or "Scored" in message:
            self.results_text.insert(tk.END, f"{message}\n")
            self.results_text.see(tk.END)

    def update_progress_with_bar(self, card, message, percentage):
        card.progress_label.configure(text=message)

        # Show and update progress bar
        card.progress_bar.pack(pady=(0, 10))

        # Update canvas progress bar
        progress_width = int((percentage / 100) * 200)
        card.progress_bar.coords(
            card.progress_bar.progress_rect, 0, 0, progress_width, 20)

        # Debug: also update results text
        self.results_text.insert(
            tk.END, f"PROGRESS BAR: {message} - {percentage}%\n")
        self.results_text.see(tk.END)

        self.root.update_idletasks()

    def run_command(self, command, card, success_message):
        def run():
            try:
                self.set_processing_state(card, True)
                self.update_progress(card, "Starting...")

                # Change to the project directory and run the command
                project_dir = os.path.dirname(os.path.abspath(__file__))
                os.chdir(project_dir)

                # Set environment for UTF-8 encoding
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

                # Run the command
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=project_dir,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )

                # Read output in real-time
                output_lines = []
                for line in iter(process.stdout.readline, ''):
                    if line:
                        line = line.strip()
                        output_lines.append(line)

                        # Special handling for enrich progress (e.g., "AI-enriched 1/23 resumes")
                        if ("AI-enriched" in line or "enriched" in line.lower()) and "/" in line:
                            # Extract progress numbers like "1/23"
                            import re
                            progress_match = re.search(r'(\d+)/(\d+)', line)
                            if progress_match:
                                current = int(progress_match.group(1))
                                total = int(progress_match.group(2))
                                percentage = int((current / total) * 100)
                                # Debug: also send to results
                                self.process_queue.put(
                                    ('progress', card, f"DEBUG: Found enrich progress: {line}"))
                                self.process_queue.put(
                                    ('progress_with_bar', card, (f"Enriched {current}/{total} resumes", percentage)))
                            else:
                                self.process_queue.put(
                                    ('progress', card, line))
                        # Special handling for score progress (e.g., "AI-scored 1/23 resumes")
                        elif "AI-scored" in line and "/" in line:
                            import re
                            progress_match = re.search(r'(\d+)/(\d+)', line)
                            if progress_match:
                                current = int(progress_match.group(1))
                                total = int(progress_match.group(2))
                                percentage = int((current / total) * 100)
                                self.process_queue.put(
                                    ('progress_with_bar', card, (f"Scored {current}/{total} resumes", percentage)))
                            else:
                                self.process_queue.put(
                                    ('progress', card, line))
                        # Handle timeout errors
                        elif "timeout" in line.lower() or "timed out" in line.lower():
                            self.process_queue.put(('timeout', card, line))
                        # Catch any other progress patterns with numbers
                        elif "/" in line and any(word in line.lower() for word in ["enriched", "scored", "processed", "completed"]):
                            import re
                            progress_match = re.search(r'(\d+)/(\d+)', line)
                            if progress_match:
                                current = int(progress_match.group(1))
                                total = int(progress_match.group(2))
                                percentage = int((current / total) * 100)
                                if "enriched" in line.lower():
                                    self.process_queue.put(
                                        ('progress_with_bar', card, (f"Enriched {current}/{total} resumes", percentage)))
                                elif "scored" in line.lower():
                                    self.process_queue.put(
                                        ('progress_with_bar', card, (f"Scored {current}/{total} resumes", percentage)))
                                else:
                                    self.process_queue.put(
                                        ('progress_with_bar', card, (f"Processed {current}/{total} items", percentage)))
                            else:
                                self.process_queue.put(
                                    ('progress', card, line))
                        else:
                            self.process_queue.put(('progress', card, line))

                process.wait()

                if process.returncode == 0:
                    # Check if it's a "no PDFs found" case
                    if any("No PDFs found" in line for line in output_lines):
                        self.process_queue.put(
                            ('warning', card, "No PDFs found in the selected folder. Please check if the folder contains PDF files with 1-2 pages."))
                    else:
                        self.process_queue.put(
                            ('success', card, success_message))
                else:
                    # Last 10 lines for debugging
                    error_output = '\n'.join(output_lines[-10:])
                    self.process_queue.put(
                        ('error', card, f"Command failed with return code {process.returncode}\nLast output:\n{error_output}"))

            except Exception as e:
                self.process_queue.put(('error', card, f"Error: {str(e)}"))

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def process_queue_events(self):
        try:
            while True:
                event_type, card, message = self.process_queue.get_nowait()

                if event_type == 'progress':
                    self.update_progress(card, message)
                    self.results_text.insert(tk.END, message + "\n")
                    self.results_text.see(tk.END)
                elif event_type == 'progress_with_bar':
                    message, percentage = message  # Unpack the tuple
                    self.results_text.insert(
                        tk.END, f"DEBUG: progress_with_bar triggered - {message} - {percentage}%\n")
                    self.results_text.see(tk.END)
                    self.update_progress_with_bar(card, message, percentage)
                elif event_type == 'success':
                    self.set_processing_state(card, False, True)
                    self.update_progress(card, "Completed successfully!")
                    card.progress_bar.pack_forget()  # Hide progress bar
                    self.results_text.insert(tk.END, f"\n{message}\n")
                    self.results_text.see(tk.END)
                elif event_type == 'warning':
                    self.set_processing_state(card, False, False, True)
                    self.update_progress(card, f"Warning: {message}")
                    card.progress_bar.pack_forget()  # Hide progress bar
                    self.results_text.insert(tk.END, f"\nWarning: {message}\n")
                    self.results_text.see(tk.END)
                elif event_type == 'timeout':
                    self.set_processing_state(card, False, False, True)
                    self.update_progress(card, f"Timeout: {message}")
                    card.progress_bar.pack_forget()  # Hide progress bar
                    self.results_text.insert(tk.END, f"\nTimeout: {message}\n")
                    self.results_text.see(tk.END)
                elif event_type == 'error':
                    self.set_processing_state(card, False, False)
                    self.update_progress(card, f"Error: {message}")
                    card.progress_bar.pack_forget()  # Hide progress bar
                    self.results_text.insert(tk.END, f"\nError: {message}\n")
                    self.results_text.see(tk.END)

        except queue.Empty:
            pass

        self.root.after(100, self.process_queue_events)

    def on_extract_click(self):
        if not self.resume_folder_path:
            messagebox.showwarning(
                "Warning", "Please select a resumes folder first!")
            return

        command = f'python CVmining.py extract "{self.resume_folder_path}" --max-pages 2 --ocr --workers 4 --output "out/resumes.jsonl"'
        self.run_command(command, self.extract_card,
                         "Resumes extracted successfully!")

    def on_job_desc_click(self):
        if not self.job_description_path:
            messagebox.showwarning(
                "Warning", "Please select a job description PDF first!")
            return

        command = f'python CVmining.py job-profile "{self.job_description_path}" --provider openai --model "gpt-5" --output "out/job_profile.json"'
        self.run_command(command, self.job_desc_card,
                         "Job profile created successfully!")

    def on_enrich_click(self):
        if not os.path.exists("out/resumes.jsonl"):
            messagebox.showwarning("Warning", "Please run Extract step first!")
            return

        command = 'python CVmining.py enrich-ai "out/resumes.jsonl" --stream --batch-size 1 --output "out/resumes_enriched.jsonl"'
        self.run_command(command, self.enrich_card,
                         "Resumes enriched successfully!")

    def on_score_click(self):
        if not os.path.exists("out/resumes_enriched.jsonl"):
            messagebox.showwarning("Warning", "Please run Enrich step first!")
            return

        # Use enriched resumes and job profile if available, otherwise fallback to original resumes and job spec
        if os.path.exists("out/job_profile.json"):
            job_spec = "out/job_profile.json"
        else:
            job_spec = "samples/job_spec.json"

        command = f'python CVmining.py score-ai "out/resumes_enriched.jsonl" "{job_spec}" --stream --batch-size 1 --output "out/scored_ai.jsonl"'
        self.run_command(command, self.score_card,
                         "Resumes scored successfully!")

    def on_rank_click(self):
        if not os.path.exists("out/scored_ai.jsonl"):
            messagebox.showwarning("Warning", "Please run Score step first!")
            return

        command = 'python CVmining.py rank "out/scored_ai.jsonl" --output "out/final_results.csv"'
        self.run_command(command, self.rank_card,
                         "Ranking completed successfully!")

        # Load and display results
        self.display_ranking_results()

    def display_ranking_results(self):
        try:
            print("DEBUG: display_ranking_results called")
            # Load ranking results from CSV
            results = []
            with open("out/final_results.csv", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            filename = parts[0]
                            score = float(parts[1]) if parts[1] else 0.0
                            results.append(
                                {"filename": filename, "score": score})
                            print(
                                f"DEBUG: Loaded result - {filename}: {score}")

            print(f"DEBUG: Total results loaded: {len(results)}")
            # Sort by score (already sorted in CSV, but just to be sure)
            results.sort(key=lambda x: x.get("score", 0), reverse=True)

            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            print(
                f"DEBUG: Treeview children after clear: {len(self.results_tree.get_children())}")

            # Add results to table with enhanced styling
            for i, result in enumerate(results, 1):
                filename = result.get("filename", "Unknown")
                score = result.get("score", 0)

                # Clean up filename (remove .pdf extension for display)
                display_name = filename.replace(
                    '.pdf', '') if filename.endswith('.pdf') else filename

                # Create styled name with document icon
                styled_name = f"📄 {display_name}"

                # Create styled score with star icon and color coding
                if score >= 90:
                    # High score - green
                    styled_score = f"⭐ {score:.0f}"
                elif score >= 80:
                    # Medium score - yellow
                    styled_score = f"⭐ {score:.0f}"
                else:
                    # Low score - red
                    styled_score = f"⭐ {score:.0f}"

                # Details icon
                details_icon = "👁️"

                print(f"DEBUG: Inserting into table - {display_name}: {score}")
                # Insert into table
                item_id = self.results_tree.insert('', 'end', values=(
                    styled_name,
                    styled_score,
                    details_icon
                ))
                print(f"DEBUG: Inserted item with ID: {item_id}")

            print(
                f"DEBUG: Treeview children after insert: {len(self.results_tree.get_children())}")
            print("DEBUG: Results display completed")

        except Exception as e:
            print(f"DEBUG: Error in display_ranking_results: {str(e)}")
            messagebox.showerror("Error", f"Error loading results: {str(e)}")


def main():
    root = tk.Tk()
    app = AIvengersApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
