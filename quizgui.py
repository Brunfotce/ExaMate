# quizgui.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
import base64
import json
from datetime import datetime
from PIL import Image, ImageTk
import io
from results import ResultsWindow
from utils import format_hms, clean_answer_text

class QuizGUI(tk.Toplevel):
    def __init__(self, parent, exam_data, json_filename=None, exam_name=None, results_folder=None):
        super().__init__(parent)
        self.parent = parent
        self.exam_data = exam_data
        self.questions = exam_data.get("questions", [])
        self.num_questions = len(self.questions)
        self.json_filename = json_filename
        self.exam_name = exam_name or "Untitled Exam"
        self.results_folder = results_folder or "./results"

        self.title(f"Exam - {self.exam_name}")
        self.geometry("950x650")
        self.minsize(800, 600)

        # User answers and state management
        self.user_answers = [set() for _ in range(self.num_questions)]
        self.current_question_index = 0
        self.question_image_refs = []
        self.answer_image_refs = []
        self.check_vars = []
        self.checkboxes = []

        # Timer and pause management
        self.start_time = time.time()
        self.timer_running = True
        self.paused = False
        self.pause_start = None
        self.accumulated_pause = 0.0

        # Navigation buttons
        self.nav_buttons = []

        self.build_ui()
        self.show_question(0)

        # Input bindings
        self.bind("<MouseWheel>", self.global_on_mousewheel, add=True)
        self.bind("<Button-4>", lambda e: self.on_mousewheel(e, delta=1))
        self.bind("<Button-5>", lambda e: self.on_mousewheel(e, delta=-1))
        self.update_timer()

    def build_ui(self):
        # ---------- LEFT: Navigator ----------
        self.nav_frame = tk.Frame(self, bd=2, relief="sunken")
        self.nav_frame.pack(side="left", fill="y", padx=5, pady=5)

        label_nav = tk.Label(self.nav_frame, text="Question Navigator:", font=("Segoe UI", 12, "bold"))
        label_nav.pack(pady=5)

        nav_scroll = tk.Scrollbar(self.nav_frame, orient="vertical")
        nav_scroll.pack(side="right", fill="y")

        self.nav_canvas = tk.Canvas(self.nav_frame, yscrollcommand=nav_scroll.set, width=120)
        self.nav_canvas.pack(side="left", fill="both", expand=True)
        nav_scroll.config(command=self.nav_canvas.yview)

        self.nav_inner = tk.Frame(self.nav_canvas)
        self.nav_window_item = self.nav_canvas.create_window((0,0), window=self.nav_inner, anchor="nw")

        self.nav_inner.bind("<Configure>",
                          lambda e: self.nav_canvas.configure(scrollregion=self.nav_canvas.bbox(self.nav_window_item)))

        for i in range(self.num_questions):
            btn_text = f"Q{i+1}"
            b = tk.Button(self.nav_inner, text=btn_text, font=("Segoe UI", 11),
                        width=6, command=lambda ix=i: self.show_question(ix))
            b.pack(padx=5, pady=2, fill="x")
            self.nav_buttons.append(b)

        # ---------- RIGHT: Main area ----------
        self.main_area = tk.Frame(self)
        self.main_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Main container with grid layout
        main_container = tk.Frame(self.main_area)
        main_container.pack(fill="both", expand=True)
        main_container.grid_rowconfigure(0, weight=0)  # Top bar
        main_container.grid_rowconfigure(1, weight=1)  # Question area
        main_container.grid_rowconfigure(2, weight=0)  # Navigation buttons
        main_container.grid_columnconfigure(0, weight=1)

        # Top bar with timer and pause button
        top_bar = tk.Frame(main_container)
        top_bar.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.pause_btn = tk.Button(top_bar, text="Pause", command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=5)
        
        self.timer_label = tk.Label(top_bar, text="Time: 00:00:00", font=("Segoe UI", 12, "bold"))
        self.timer_label.pack(side="right", padx=5)

        # Question display area
        q_frame = tk.Frame(main_container)
        q_frame.grid(row=1, column=0, sticky="nsew", pady=5)

        self.q_scroll = tk.Scrollbar(q_frame)
        self.q_scroll.pack(side="right", fill="y")

        self.q_canvas = tk.Canvas(q_frame, yscrollcommand=self.q_scroll.set)
        self.q_canvas.pack(side="left", fill="both", expand=True)
        self.q_scroll.config(command=self.q_canvas.yview)

        self.q_container = tk.Frame(self.q_canvas)
        self.q_window_item = self.q_canvas.create_window((0, 0), window=self.q_container, anchor="nw")

        # Dynamic width adjustment
        def configure_canvas(event):
            canvas_width = event.width
            scrollbar_width = self.q_scroll.winfo_width()
            content_width = canvas_width - scrollbar_width - 20
            self.q_canvas.itemconfig(self.q_window_item, width=content_width)
            
            # Update wraplength for all labels
            for child in self.q_container.winfo_children():
                if isinstance(child, tk.Label) and "wraplength" in child.config():
                    child.config(wraplength=content_width - 40)

        self.q_canvas.bind('<Configure>', configure_canvas)

        # Bottom navigation buttons
        nav_btns_frame = tk.Frame(main_container)
        nav_btns_frame.grid(row=2, column=0, sticky="ew", pady=10)

        # Configure grid weights for button alignment
        nav_btns_frame.grid_columnconfigure(0, weight=1)
        nav_btns_frame.grid_columnconfigure(1, weight=0)
        nav_btns_frame.grid_columnconfigure(2, weight=1)

        # Left-aligned buttons container
        left_btn_frame = tk.Frame(nav_btns_frame)
        left_btn_frame.grid(row=0, column=0, sticky="w")

        self.prev_btn = tk.Button(left_btn_frame, text="Previous", 
                                font=("Segoe UI", 11), command=self.prev_question)
        self.prev_btn.pack(side="left", padx=5)

        self.next_btn = tk.Button(left_btn_frame, text="Next", 
                                font=("Segoe UI", 11), command=self.next_question)
        self.next_btn.pack(side="left", padx=5)

        # Right-aligned finish button
        tk.Button(nav_btns_frame, text="Finish Exam", 
                font=("Segoe UI", 12, "bold"), command=self.finish_exam
                ).grid(row=0, column=2, sticky="e", padx=5)

        # Configure container resize
        self.q_container.bind("<Configure>", 
                            lambda e: self.q_canvas.configure(
                                scrollregion=self.q_canvas.bbox("all")))

    def show_question(self, index):
        self.store_current_picks()
        self.current_question_index = index
        
        # Clear previous content
        for widget in self.q_container.winfo_children():
            widget.destroy()
            
        self.question_image_refs.clear()
        self.answer_image_refs.clear()
        self.check_vars = []
        self.checkboxes = []

        # Get current question data
        qobj = self.questions[index]
        question_number = qobj.get("question_number", index+1)
        
        # Header
        header = tk.Label(self.q_container, 
                        text=f"Question {index+1}/{self.num_questions}: #{question_number}",
                        font=("Segoe UI", 14, "bold"), anchor="w")
        header.pack(anchor="w", pady=(0, 15))

        # Question content
        for part in qobj.get("question_parts", []):
            ptype, content = part[0], part[1]
            if ptype == "text":
                lbl = tk.Label(self.q_container, text=content, 
                             wraplength=700, justify="left",
                             font=("Segoe UI", 11))
                lbl.pack(anchor="w", pady=2)
            elif ptype == "image_base64":
                try:
                    image_data = base64.b64decode(content)
                    image = Image.open(io.BytesIO(image_data))
                    image.thumbnail((600, 400))
                    photo = ImageTk.PhotoImage(image)
                    self.question_image_refs.append(photo)
                    lbl = tk.Label(self.q_container, image=photo)
                    lbl.pack(anchor="w", pady=5)
                except Exception as e:
                    err = tk.Label(self.q_container, text="[Error loading image]", fg="red")
                    err.pack(anchor="w")

        # Answers
        answers_frame = tk.Frame(self.q_container)
        answers_frame.pack(anchor="w", fill="x", pady=10)
        
        correct_answers = qobj.get("correct_answers", [])
        max_picks = len(correct_answers) if correct_answers else 1
        
        for ans_idx, answer_parts in enumerate(qobj.get("answers", [])):
            answer_frame = tk.Frame(answers_frame)
            answer_frame.pack(anchor="w", fill="x", pady=3)
            
            # Checkbox
            var = tk.BooleanVar(value=chr(65+ans_idx) in self.user_answers[index])
            cb = tk.Checkbutton(answer_frame, text=f"{chr(65+ans_idx)}.", 
                              font=("Segoe UI", 11), variable=var,
                              command=lambda i=ans_idx: self.on_answer_toggle(i))
            cb.grid(row=0, column=0, sticky="w")
            self.check_vars.append(var)
            self.checkboxes.append(cb)

            # Answer content
            col = 1
            row = 0
            for part in answer_parts:
                ptype, content = part[0], part[1]
                if ptype == "text":
                    cleaned_text = clean_answer_text(content)
                    lbl = tk.Label(answer_frame, text=cleaned_text, 
                                 wraplength=600, justify="left",
                                 font=("Segoe UI", 11))
                    lbl.grid(row=row, column=col, sticky="w", padx=5)
                elif ptype == "image_base64":
                    try:
                        image_data = base64.b64decode(content)
                        image = Image.open(io.BytesIO(image_data))
                        image.thumbnail((400, 300))
                        photo = ImageTk.PhotoImage(image)
                        self.answer_image_refs.append(photo)
                        lbl = tk.Label(answer_frame, image=photo)
                        row += 1
                        lbl.grid(row=row, column=col, sticky="w", padx=25, pady=5)
                    except Exception as e:
                        err = tk.Label(answer_frame, text="[Error loading image]", fg="red")
                        row += 1
                        err.grid(row=row, column=col, sticky="w", padx=25)

        self.enforce_checkbox_limit(max_picks)
        self.update_navigation()
        self.q_canvas.yview_moveto(0.0)

    def on_answer_toggle(self, ans_idx):
        self.store_current_picks()
        qobj = self.questions[self.current_question_index]
        correct_answers = qobj.get("correct_answers", [])
        max_picks = len(correct_answers) if correct_answers else 1
        self.enforce_checkbox_limit(max_picks)
        self.update_navigation()

    def enforce_checkbox_limit(self, max_picks):
        current_picks = sum(var.get() for var in self.check_vars)
        for i, var in enumerate(self.check_vars):
            if current_picks >= max_picks and not var.get():
                self.checkboxes[i].config(state="disabled")
            else:
                self.checkboxes[i].config(state="normal")

    def store_current_picks(self):
        index = self.current_question_index
        self.user_answers[index] = set()
        for i, var in enumerate(self.check_vars):
            if var.get():
                self.user_answers[index].add(chr(65+i))

    def update_navigation(self):
        index = self.current_question_index
        btn = self.nav_buttons[index]
        btn_text = f"Q{index+1}"
        if self.user_answers[index]:
            btn_text += " ✓"
        btn.config(text=btn_text)
        
        self.prev_btn.config(state="normal" if index > 0 else "disabled")
        self.next_btn.config(state="normal" if index < self.num_questions-1 else "disabled")

    def toggle_pause(self):
        if not self.paused:
            self.paused = True
            self.pause_start = time.time()
            self.pause_btn.config(text="Resume")
            self.timer_running = False
            
            # Disable interactions
            for widget in [self.prev_btn, self.next_btn] + self.nav_buttons + self.checkboxes:
                widget.config(state="disabled")
        else:
            self.paused = False
            self.accumulated_pause += time.time() - self.pause_start
            self.pause_btn.config(text="Pause")
            self.timer_running = True
            
            # Enable interactions
            for widget in [self.prev_btn, self.next_btn] + self.nav_buttons:
                widget.config(state="normal")
            qobj = self.questions[self.current_question_index]
            correct_answers = qobj.get("correct_answers", [])
            self.enforce_checkbox_limit(len(correct_answers) if correct_answers else 1)
            
        self.update_timer()

    def update_timer(self):
        if self.timer_running and not self.paused:
            elapsed = time.time() - self.start_time - self.accumulated_pause
            self.timer_label.config(text=f"Time: {format_hms(elapsed)}")
        self.after(500, self.update_timer)

    def prev_question(self):
        if self.current_question_index > 0:
            self.show_question(self.current_question_index - 1)

    def next_question(self):
        if self.current_question_index < self.num_questions - 1:
            self.show_question(self.current_question_index + 1)

    def finish_exam(self):
        self.timer_running = False
        total_time = time.time() - self.start_time - self.accumulated_pause
        
        # Calculate score
        total_points = 0.0
        for i, q in enumerate(self.questions):
            correct = set(q.get("correct_answers", []))
            user = self.user_answers[i]
            if correct:
                total_points += len(user & correct) / len(correct)
        
        percentage = (total_points / self.num_questions) * 100 if self.num_questions else 0
        
        # Prepare results data
        results_data = {
            "exam_name": self.exam_name,
            "final_score": total_points,
            "total_questions": self.num_questions,
            "percentage": percentage,
            "elapsed_time": format_hms(total_time),
            "user_answers": [sorted(ans) for ans in self.user_answers],
            "questions": self.questions
        }
        
        # Save results
        os.makedirs(self.results_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.exam_name}_results_{timestamp}.json"
        with open(os.path.join(self.results_folder, filename), "w") as f:
            json.dump(results_data, f, indent=2)
            
        # Show results window
        ResultsWindow(self.parent, results_data)
        self.destroy()

    def global_on_mousewheel(self, event):
        px, py = self.winfo_pointerxy()
        if self.point_in_widget(px, py, self.nav_frame):
            if self.can_scroll_nav():
                self.nav_canvas.yview_scroll(int(-event.delta/120), "units")
        elif self.point_in_widget(px, py, self.main_area):
            if self.can_scroll_question():
                self.q_canvas.yview_scroll(int(-event.delta/120), "units")

    def on_mousewheel(self, event, delta):
        px, py = self.winfo_pointerxy()
        if self.point_in_widget(px, py, self.nav_frame):
            if self.can_scroll_nav():
                self.nav_canvas.yview_scroll(-delta, "units")
        elif self.point_in_widget(px, py, self.main_area):
            if self.can_scroll_question():
                self.q_canvas.yview_scroll(-delta, "units")

    def point_in_widget(self, px, py, widget):
        x1 = widget.winfo_rootx()
        y1 = widget.winfo_rooty()
        x2 = x1 + widget.winfo_width()
        y2 = y1 + widget.winfo_height()
        return (px >= x1 and px < x2 and py >= y1 and py < y2)

    def can_scroll_nav(self):
        bbox = self.nav_canvas.bbox(self.nav_window_item)
        if not bbox:
            return False
        content_h = bbox[3]-bbox[1]
        visible_h = self.nav_canvas.winfo_height()
        return content_h > visible_h

    def can_scroll_question(self):
        bbox = self.q_canvas.bbox("all")
        if not bbox:
            return False
        content_h = bbox[3]-bbox[1]
        visible_h = self.q_canvas.winfo_height()
        return content_h > visible_h