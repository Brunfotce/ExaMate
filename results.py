# results.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils import combine_text_for_display  # Ensure this function is correctly implemented

class ResultsWindow(tk.Toplevel):
    def __init__(self, parent, results_data):
        super().__init__(parent)
        self.parent = parent
        self.results_data = results_data

        self.title("Quiz Results")
        self.geometry("800x600")
        self.resizable(True, True)

        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Summary Frame
        summary_frame = tk.Frame(self)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        summary_frame.grid_columnconfigure(1, weight=1)

        tk.Label(summary_frame, text="Quiz Results", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,10))

        # Display summary information
        tk.Label(summary_frame, text=f"Exam: {self.results_data.get('exam_name', 'N/A')}", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w")
        tk.Label(summary_frame, text=f"Score: {self.results_data.get('final_score', 0)} / {self.results_data.get('total_questions', 0)}", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w")
        tk.Label(summary_frame, text=f"Percentage: {self.results_data.get('percentage', 0)}%", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w")
        tk.Label(summary_frame, text=f"Elapsed Time: {self.results_data.get('elapsed_time', '00:00:00')}", font=("Segoe UI", 12)).grid(row=4, column=0, sticky="w")

        # "Save Results" Button
        save_btn = tk.Button(summary_frame, text="Save Results", font=("Segoe UI", 12), command=self.save_results)
        save_btn.grid(row=5, column=0, columnspan=2, pady=10)

        # Detailed Results Label
        tk.Label(self, text="Detailed Results:", font=("Segoe UI", 14, "bold")).grid(row=1, column=0, sticky="w", padx=10)

        # Scrollable Text Widget for detailed results
        self.text_area = tk.Text(self, wrap="word", font=("Segoe UI", 11))
        self.text_area.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.text_area.config(state="disabled")

        # Vertical Scrollbar for Text Widget
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.text_area.yview)
        scrollbar.grid(row=2, column=1, sticky="ns", pady=5)
        self.text_area.configure(yscrollcommand=scrollbar.set)

        # Populate detailed results
        self.populate_detailed_results()

        # Close Button
        close_btn = tk.Button(self, text="Close", font=("Segoe UI", 12), command=self.destroy)
        close_btn.grid(row=3, column=0, pady=10)

    def populate_detailed_results(self):
        self.text_area.config(state="normal")
        for idx, question in enumerate(self.results_data.get("questions", []), 1):
            q_text = combine_text_for_display(question.get("question_parts", []))
            correct_answers = set(question.get("correct_answers", []))
            user_picks = set(self.results_data.get("user_answers", [])[idx-1])

            # Determine correctness
            if not correct_answers:
                status = "No correct answer provided."
                color = "black"
            elif user_picks == correct_answers:
                status = "Correct"
                color = "green"
            elif user_picks & correct_answers:
                status = "Partially Correct"
                color = "orange"
            else:
                status = "Incorrect"
                color = "red"

            # Insert question number and text
            self.text_area.insert("end", f"Q{idx}: {q_text}\n", "question")

            # Insert user's answers
            user_ans_str = ", ".join(sorted(user_picks)) if user_picks else "No answer selected."
            self.text_area.insert("end", f"Your Answer(s): {user_ans_str}\n", "user_answer")

            # Insert correct answers
            correct_ans_str = ", ".join(sorted(correct_answers)) if correct_answers else "N/A"
            self.text_area.insert("end", f"Correct Answer(s): {correct_ans_str}\n", "correct_answer")

            # Insert status
            self.text_area.insert("end", f"Status: {status}\n\n", f"status_{color}")

        # Configure tags for styling
        self.text_area.tag_configure("question", font=("Segoe UI", 12, "bold"))
        self.text_area.tag_configure("user_answer", foreground="blue")
        self.text_area.tag_configure("correct_answer", foreground="green")
        self.text_area.tag_configure("status_correct", foreground="green")
        self.text_area.tag_configure("status_incorrect", foreground="red")
        self.text_area.tag_configure("status_partially_correct", foreground="orange")

        self.text_area.config(state="disabled")

    def save_results(self):
        """Allow the user to save the results manually."""
        # Prompt user to choose save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Results As"
        )
        if not file_path:
            return  # User cancelled

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Write summary
                f.write("Quiz Results\n")
                f.write(f"Exam: {self.results_data.get('exam_name', 'N/A')}\n")
                f.write(f"Score: {self.results_data.get('final_score', 0)} / {self.results_data.get('total_questions', 0)}\n")
                f.write(f"Percentage: {self.results_data.get('percentage', 0)}%\n")
                f.write(f"Elapsed Time: {self.results_data.get('elapsed_time', '00:00:00')}\n\n")
                
                # Write detailed results
                f.write("Detailed Results:\n")
                for idx, question in enumerate(self.results_data.get("questions", []), 1):
                    q_text = combine_text_for_display(question.get("question_parts", []))
                    correct_answers = set(question.get("correct_answers", []))
                    user_picks = set(self.results_data.get("user_answers", [])[idx-1])

                    # Determine correctness
                    if not correct_answers:
                        status = "No correct answer provided."
                    elif user_picks == correct_answers:
                        status = "Correct"
                    elif user_picks & correct_answers:
                        status = "Partially Correct"
                    else:
                        status = "Incorrect"

                    f.write(f"Q{idx}: {q_text}\n")
                    user_ans_str = ", ".join(sorted(user_picks)) if user_picks else "No answer selected."
                    f.write(f"Your Answer(s): {user_ans_str}\n")
                    correct_ans_str = ", ".join(sorted(correct_answers)) if correct_answers else "N/A"
                    f.write(f"Correct Answer(s): {correct_ans_str}\n")
                    f.write(f"Status: {status}\n\n")

            messagebox.showinfo("Success", f"Results successfully saved to {file_path}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results.\n{e}")
