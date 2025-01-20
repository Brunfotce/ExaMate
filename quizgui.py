# quizgui.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, base64, json, random, re, time
from PIL import Image, ImageTk
from results import ResultsWindow  # Importing the ResultsWindow class
from utils import format_hms, combine_text_for_display, clean_answer_text  # Import from utils.py

class QuizGUI(tk.Toplevel):
    def __init__(self, parent, exam_data, json_filename=None, exam_name=None, results_folder=None):
        super().__init__(parent)
        self.parent = parent  # Reference to the main Tk window
        self.exam_data = exam_data
        self.json_filename = json_filename

        # Determine exam name
        if exam_name:
            self.exam_name = exam_name
        elif json_filename:
            self.exam_name = os.path.splitext(os.path.basename(json_filename))[0]
        else:
            self.exam_name = "Untitled"

        # Set the results_folder
        self.results_folder = results_folder or "./results"

        self.questions = exam_data.get("questions", [])
        self.num_questions = len(self.questions)

        self.title(f"Quiz - {self.exam_name}")
        self.geometry("1000x700")  # Increased size for better layout
        self.minsize(800, 600)      # Minimum size for responsiveness

        # User picks
        self.user_answers = [set() for _ in range(self.num_questions)]
        self.current_index = 0

        # Timer
        self.start_time = time.time()
        self.paused = False
        self.pause_start = None
        self.accumulated_pause = 0.0

        # For the navigator
        self.nav_buttons = []

        # For images
        self.question_imgs = []
        self.answer_imgs = []

        # Initialize check_vars and checkboxes to avoid AttributeError
        self.check_vars = []
        self.checkboxes = []

        self.build_ui()

        # If no questions, close
        if self.num_questions > 0:
            self.show_question(0)
        else:
            messagebox.showinfo("No Questions", "No questions after selection.")
            self.destroy()
            return

        # Bind mousewheel
        self.bind("<MouseWheel>", self.global_on_mousewheel, add=True)
        # Bind additional mousewheel events for Linux compatibility
        self.bind("<Button-4>", lambda event: self.on_mousewheel(event, delta=1))
        self.bind("<Button-5>", lambda event: self.on_mousewheel(event, delta=-1))
        self.update_timer()

    def build_ui(self):
        # Configure grid weights for responsiveness
        self.grid_rowconfigure(0, weight=0)  # Top bar
        self.grid_rowconfigure(1, weight=1)  # Main content
        self.grid_rowconfigure(2, weight=0)  # Bottom bar
        self.grid_columnconfigure(0, weight=0)  # Navigator
        self.grid_columnconfigure(1, weight=1)  # Main area

        # Top bar with timer and pause button
        top_bar = tk.Frame(self)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)
        top_bar.grid_columnconfigure(1, weight=0)

        self.pause_btn = tk.Button(top_bar, text="Pause", command=self.toggle_pause)
        self.pause_btn.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.timer_label = tk.Label(top_bar, text="Time: 00:00:00", font=("Segoe UI", 12, "bold"))
        self.timer_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        # Left navigator
        nav_frame = tk.Frame(self, bd=2, relief="sunken")
        nav_frame.grid(row=1, column=0, sticky="ns", padx=5, pady=5)
        nav_frame.grid_rowconfigure(1, weight=1)
        nav_frame.grid_columnconfigure(0, weight=1)

        lbl_nav = tk.Label(nav_frame, text="Navigator:", font=("Segoe UI", 12, "bold"))
        lbl_nav.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        nav_scroll = tk.Scrollbar(nav_frame, orient="vertical")
        nav_scroll.grid(row=1, column=1, sticky="ns")

        self.nav_canvas = tk.Canvas(nav_frame, yscrollcommand=nav_scroll.set, width=120)
        self.nav_canvas.grid(row=1, column=0, sticky="nsew")

        nav_scroll.config(command=self.nav_canvas.yview)

        self.nav_inner = tk.Frame(self.nav_canvas)
        self.nav_window = self.nav_canvas.create_window((0, 0), window=self.nav_inner, anchor="nw")
        self.nav_inner.bind("<Configure>",
                            lambda e: self.nav_canvas.configure(scrollregion=self.nav_canvas.bbox(self.nav_window)))

        for i in range(self.num_questions):
            b = tk.Button(self.nav_inner, text=f"Q{i + 1}", width=5,
                          command=lambda ix=i: self.show_question(ix))
            b.pack(padx=5, pady=2, fill="x")
            self.nav_buttons.append(b)

        # Main quiz area
        self.main_area = tk.Frame(self)
        self.main_area.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Question display with rich text support using Text widget
        self.question_frame = tk.Text(self.main_area, wrap="word", font=("Segoe UI", 11), state="disabled",
                                      bg=self.main_area.cget("bg"), relief="flat")
        self.question_frame.grid(row=0, column=0, sticky="nsew")

        # Scrollable answers area
        self.answers_canvas = tk.Canvas(self.main_area)
        self.answers_canvas.grid(row=1, column=0, sticky="nsew")

        self.answers_scroll = tk.Scrollbar(self.main_area, orient="vertical", command=self.answers_canvas.yview)
        self.answers_scroll.grid(row=1, column=1, sticky="ns")
        self.answers_canvas.configure(yscrollcommand=self.answers_scroll.set)

        self.answers_inner = tk.Frame(self.answers_canvas)
        self.answers_canvas.create_window((0, 0), window=self.answers_inner, anchor="nw")
        self.answers_inner.bind("<Configure>",
                                lambda e: self.answers_canvas.configure(scrollregion=self.answers_canvas.bbox("all")))

        # Bottom navigation buttons
        bottom = tk.Frame(self)
        bottom.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_columnconfigure(2, weight=1)

        self.prev_btn = tk.Button(bottom, text="Previous", command=self.prev_question)
        self.prev_btn.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        finish_btn = tk.Button(bottom, text="Finish Exam", command=self.finish_exam)
        finish_btn.grid(row=0, column=2, padx=5, pady=5, sticky="e")  # Positioned at bottom right

        self.next_btn = tk.Button(bottom, text="Next", command=self.next_question)
        self.next_btn.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def on_mousewheel(self, event, delta=0):
        """Handle mouse wheel events for Linux."""
        if delta:
            self.answers_canvas.yview_scroll(delta, "units")
        else:
            self.answers_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def global_on_mousewheel(self, event):
        """Handle mouse wheel events for other platforms."""
        px, py = self.winfo_pointerxy()
        if self.point_in_widget(px, py, self.nav_canvas):
            self.nav_canvas.yview_scroll(int(-event.delta / 120), "units")
        elif self.point_in_widget(px, py, self.answers_canvas):
            self.answers_canvas.yview_scroll(int(-event.delta / 120), "units")

    def point_in_widget(self, px, py, widget):
        """Check if the pointer is within a given widget."""
        x1 = widget.winfo_rootx()
        y1 = widget.winfo_rooty()
        x2 = x1 + widget.winfo_width()
        y2 = y1 + widget.winfo_height()
        return (px >= x1 and px < x2 and py >= y1 and py < y2)

    def toggle_pause(self):
        """Toggle the pause state of the quiz."""
        if not self.paused:
            # Start pause
            self.paused = True
            self.pause_start = time.time()
            self.pause_btn.config(text="Resume")
            # Disable navigation and answer selection
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            for btn in self.nav_buttons:
                btn.config(state="disabled")
            for cb in self.checkboxes:
                cb.config(state="disabled")
        else:
            # End pause
            self.paused = False
            paused_duration = time.time() - self.pause_start
            self.pause_start = None
            self.accumulated_pause += paused_duration
            self.pause_btn.config(text="Pause")
            # Re-enable navigation and answer selection
            self.prev_btn.config(state="normal")
            self.next_btn.config(state="normal")
            for btn in self.nav_buttons:
                btn.config(state="normal")
            self.enforce_checkbox_limit()

    def update_timer(self):
        """Update the timer label every 500 milliseconds."""
        if not self.paused:
            elapsed = time.time() - self.start_time - self.accumulated_pause
            self.timer_label.config(text="Time: " + format_hms(elapsed))
        self.after(500, self.update_timer)

    def show_question(self, index):
        """Display a specific question based on the index."""
        self.store_current_picks()
        self.current_index = index

        # Clear previous question
        self.question_frame.config(state="normal")
        self.question_frame.delete("1.0", "end")
        self.question_frame.config(state="disabled")

        for w in self.answers_inner.winfo_children():
            w.destroy()
        self.answer_imgs.clear()

        # Reset check_vars and checkboxes
        self.check_vars = []
        self.checkboxes = []

        qobj = self.questions[index]
        qnum = qobj.get("question_number", "?")
        # Header label with rich text
        header = f"Question {index + 1}/{self.num_questions}: #{qnum}\n\n"
        self.question_frame.config(state="normal")
        self.question_frame.insert("1.0", header, "header")
        self.question_frame.tag_configure("header", font=("Segoe UI", 12, "bold"))

        # Question parts with rich text
        for (ptype, content) in qobj.get("question_parts", []):
            if ptype == "text":
                self.question_frame.insert("end", content + "\n", "text")
            elif ptype == "image_base64":
                # Decode base64 and insert image
                try:
                    import io
                    bdata = base64.b64decode(content)
                    im = Image.open(io.BytesIO(bdata))
                    im.thumbnail((600, 400))  # Resize for better fit
                    tkimg = ImageTk.PhotoImage(im)
                    self.question_imgs.append(tkimg)  # Prevent garbage collection
                    self.question_frame.image_create("end", image=tkimg)
                    self.question_frame.insert("end", "\n")
                except Exception as e:
                    print(f"Error loading image in question: {e}")
                    self.question_frame.insert("end", "[Error loading image]\n", "error")
        self.question_frame.config(state="disabled")

        # Answers with checkboxes and rich text
        correct_list = qobj.get("correct_answers", [])
        max_picks = len(correct_list) if correct_list else 1

        picks = self.user_answers[index]
        ans = qobj.get("answers", [])
        for ans_i, ans_parts in enumerate(ans):
            letter = chr(ord("A") + ans_i)
            var = tk.BooleanVar(value=(letter in picks))
            self.check_vars.append(var)

            ans_frame = tk.Frame(self.answers_inner)
            ans_frame.pack(anchor="w", fill="x", pady=5)

            # Assign labels based on index instead of the text content
            cbtn = tk.Checkbutton(ans_frame, text=f"{letter}.", font=("Segoe UI", 11),
                                  variable=var, command=lambda i=ans_i: self.on_toggle_answer(i))
            cbtn.grid(row=0, column=0, sticky="nw")

            self.checkboxes.append(cbtn)

            # Answer text
            answer_text = ""
            for (apt, val) in ans_parts:
                if apt == "text":
                    answer_text += val + " "
            answer_text = answer_text.strip()

            # Remove any leading labels from answer_text to prevent duplication
            # Example: "A. Take EBS snapshots..." -> "Take EBS snapshots..."
            answer_text = clean_answer_text(answer_text)

            lb = tk.Label(ans_frame, text=answer_text, wraplength=700,
                         justify="left", font=("Segoe UI", 11))
            lb.grid(row=0, column=1, sticky="w", padx=5)

            # Handle images in answers (lazy loading)
            for (apt, val) in ans_parts:
                if apt == "image_base64":
                    try:
                        import io
                        bdat = base64.b64decode(val)
                        im2 = Image.open(io.BytesIO(bdat))
                        im2.thumbnail((400, 300))  # Resize for better fit
                        tkim2 = ImageTk.PhotoImage(im2)
                        self.answer_imgs.append(tkim2)  # Prevent garbage collection
                        ilb = tk.Label(ans_frame, image=tkim2)
                        ilb.grid(row=1, column=1, sticky="w", padx=25, pady=5)
                    except Exception as e:
                        print(f"Error loading image in answer: {e}")
                        elb = tk.Label(ans_frame, text="[Error loading image]", fg="red")
                        elb.grid(row=1, column=1, sticky="w", padx=25, pady=5)

        self.enforce_checkbox_limit(max_picks)
        self.update_nav_buttons()
        self.update_nav_button_text(index)

    def on_toggle_answer(self, ans_i):
        """Handle toggling of answer checkboxes."""
        self.store_current_picks()
        qobj = self.questions[self.current_index]
        cset = qobj.get("correct_answers", [])
        max_picks = len(cset) if cset else 1
        self.enforce_checkbox_limit(max_picks)
        self.update_nav_button_text(self.current_index)

    def store_current_picks(self):
        """Store the user's current picks for the active question."""
        if self.current_index < 0 or self.current_index >= self.num_questions:
            return
        picks = set()
        for i, var in enumerate(self.check_vars):
            if var.get():
                letter = chr(ord("A") + i)
                picks.add(letter)
        self.user_answers[self.current_index] = picks

    def enforce_checkbox_limit(self, max_picks):
        """Disable checkboxes if the maximum number of picks is reached."""
        picks = self.user_answers[self.current_index]
        if len(picks) >= max_picks:
            for i, var in enumerate(self.check_vars):
                if not var.get():
                    self.checkboxes[i].config(state="disabled")
        else:
            for i, var in enumerate(self.check_vars):
                self.checkboxes[i].config(state="normal")

    def update_nav_buttons(self):
        """Enable or disable navigation buttons based on the current question."""
        if self.current_index <= 0:
            self.prev_btn.config(state="disabled")
        else:
            self.prev_btn.config(state="normal")
        if self.current_index >= self.num_questions - 1:
            self.next_btn.config(state="disabled")
        else:
            self.next_btn.config(state="normal")

    def update_nav_button_text(self, ix):
        """Update navigator button text with a checkmark if answered."""
        picks = self.user_answers[ix]
        btn = self.nav_buttons[ix]
        base = f"Q{ix + 1}"
        if picks:
            btn.config(text=base + " \u2713")  # Checkmark
        else:
            btn.config(text=base)

    def prev_question(self):
        """Navigate to the previous question."""
        if self.current_index > 0:
            self.show_question(self.current_index - 1)

    def next_question(self):
        """Navigate to the next question."""
        if self.current_index < self.num_questions - 1:
            self.show_question(self.current_index + 1)

    def finish_exam(self):
        """Finalize the exam, calculate scores, save results, and display the ResultsWindow."""
        # Debugging: Confirm finish_exam is called
        print("QuizGUI: finish_exam called.")
        # Removed messagebox.showinfo to prevent UI blocking

        # Finalize
        self.store_current_picks()
        end_time = time.time()
        total_elapsed = end_time - self.start_time
        if self.paused and self.pause_start:
            total_elapsed -= (time.time() - self.pause_start)

        # Partial credit calculation
        total_points = 0.0
        for i, qobj in enumerate(self.questions):
            cset = set(qobj.get("correct_answers", []))
            picks = self.user_answers[i]
            if cset:
                partial = len(cset.intersection(picks)) / len(cset)
            else:
                partial = 0.0
            total_points += partial

        final_score = total_points
        total_q = len(self.questions)
        perc = (final_score / total_q) * 100 if total_q else 0

        # Debugging: Confirm score calculation
        print(f"QuizGUI: Final Score: {final_score} / {total_q} ({perc}%)")

        # Prepare results data
        results_data = {
            "exam_name": self.exam_name,
            "final_score": final_score,
            "total_questions": total_q,
            "percentage": perc,
            "elapsed_time": format_hms(total_elapsed),
            "user_answers": [list(ans) for ans in self.user_answers],  # Convert sets to lists
            "questions": self.questions
        }

        # Save results to the 'results' folder with a timestamped filename
        timestamp = int(time.time())
        results_filename = f"{self.exam_name}_results_{timestamp}.json"
        results_path = os.path.join(self.results_folder, results_filename)
        try:
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2)
            print(f"Results saved to {results_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results.\n{e}")
            print(f"QuizGUI: Exception occurred while saving results: {e}")

        # Show summary using ResultsWindow
        try:
            results_window = ResultsWindow(
                self.parent,  # Pass the main Tk window as the parent
                results_data
            )
            results_window.grab_set()  # Make the results window modal
            print("QuizGUI: ResultsWindow created successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create ResultsWindow.\n{e}")
            print(f"QuizGUI: Exception occurred while creating ResultsWindow: {e}")

        # Destroy QuizGUI after ResultsWindow is created
        self.destroy()

