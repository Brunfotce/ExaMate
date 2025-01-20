# main.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, json, random, re, time, base64
from parse_html import parse_html_to_json
from editor import EditorWindow
from quizgui import QuizGUI
from results import ResultsWindow  # Ensure you have this class implemented
from utils import clean_answer_text, clean_string  # Import necessary helper functions

"""
Main menu for ExaMate:
1) Parse from HTML to JSON (with base64 images)
2) Create a new exam from scratch (Editor)
3) Load a .json exam and start the quiz
4) Load a results file
"""

class MainMenu:
    def __init__(self, master):
        self.master = master
        self.master.title("ExaMate - Main Menu")
        self.master.geometry("600x400")  # Increased height to accommodate new buttons

        # Ensure 'exams' and 'results' folders exist
        self.exams_folder = "./exams"
        self.results_folder = "./results"
        os.makedirs(self.exams_folder, exist_ok=True)
        os.makedirs(self.results_folder, exist_ok=True)

        # Title
        tk.Label(self.master, text="ExaMate Offline Quiz", font=("Segoe UI", 18, "bold")).pack(pady=10)

        # Frame for exam selection
        frame_top = tk.Frame(self.master)
        frame_top.pack(pady=5)

        tk.Label(frame_top, text="Pick an Exam: ", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=5)
        self.exam_var = tk.StringVar(value="")
        self.combo_exams = ttk.Combobox(frame_top, textvariable=self.exam_var, state="readonly", width=40, font=("Segoe UI", 12))
        self.combo_exams.grid(row=0, column=1, sticky="w", padx=5)

        # Gather all .json files from './exams' folder
        self.exams_list = []
        self.refresh_exams()

        tk.Label(frame_top, text="How many questions?", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.num_var = tk.StringVar(value="10")
        tk.Entry(frame_top, textvariable=self.num_var, width=5, font=("Segoe UI", 12)).grid(row=1, column=1, sticky="w", padx=5, pady=10)

        # Frame for buttons
        frame_buttons = tk.Frame(self.master)
        frame_buttons.pack(pady=10)

        # Button to start quiz
        start_btn = tk.Button(frame_buttons, text="Start Quiz", font=("Segoe UI", 14, "bold"), width=20, command=self.start_quiz)
        start_btn.grid(row=0, column=0, padx=10, pady=5)

        # Button to create a new exam
        create_btn = tk.Button(frame_buttons, text="Create New Exam", font=("Segoe UI", 12), width=20, command=self.create_new_exam)
        create_btn.grid(row=0, column=1, padx=10, pady=5)

        # Button to parse HTML to JSON
        parse_btn = tk.Button(frame_buttons, text="Parse Exam Topics HTML to JSON", font=("Segoe UI", 12), width=25, command=self.parse_html)
        parse_btn.grid(row=1, column=0, padx=10, pady=5)

        # Button to load a results file
        load_results_btn = tk.Button(frame_buttons, text="Load Results File", font=("Segoe UI", 12), width=20, command=self.load_results)
        load_results_btn.grid(row=1, column=1, padx=10, pady=5)

    def refresh_exams(self):
        """Refresh the exams list from the exams folder."""
        self.exams_list = []
        for f in os.listdir(self.exams_folder):
            if f.lower().endswith(".json"):
                self.exams_list.append(f)
        if self.exams_list:
            self.combo_exams["values"] = self.exams_list
            self.combo_exams.current(0)
        else:
            self.combo_exams.set("")
            self.combo_exams["values"] = []

    def start_quiz(self):
        """Start the quiz with the selected exam."""
        exam_file = self.exam_var.get().strip()
        if not exam_file:
            messagebox.showwarning("No Exam Selected", "Please select an exam from the dropdown.")
            return

        # Read number of questions
        try:
            requested = int(self.num_var.get().strip())
            if requested <= 0:
                raise ValueError
        except:
            messagebox.showwarning("Invalid Number", "Please enter a valid number of questions (positive integer).")
            return

        json_path = os.path.join(self.exams_folder, exam_file)
        if not os.path.isfile(json_path):
            messagebox.showerror("File Not Found", f"The exam file {exam_file} does not exist.")
            return

        # Load JSON
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                exam_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON.\n{e}")
            return

        # Extract questions
        all_q = exam_data.get("questions", [])
        if not all_q:
            messagebox.showinfo("No Questions", "This exam has no questions.")
            return

        # Shuffle questions
        random.shuffle(all_q)
        # Slice to requested number
        selected_q = all_q[:min(len(all_q), requested)]
        exam_data["questions"] = selected_q  # Overwrite with the subset

        # Initialize QuizGUI
        exam_name = os.path.splitext(exam_file)[0]
        quiz_window = QuizGUI(
            self.master,
            exam_data,
            json_filename=json_path,
            exam_name=exam_name,
            results_folder=self.results_folder  # Pass the results_folder here
        )
        quiz_window.focus()
        quiz_window.grab_set()

    def create_new_exam(self):
        """Open the editor to create a new exam."""
        editor = EditorWindow(self.master)
        self.master.wait_window(editor)
        # After editor is closed, refresh the exams list
        self.refresh_exams()

    def parse_html(self):
        """Parse selected HTML folder to JSON and save in exams folder."""
        # Prompt user to select the folder containing HTML files
        input_folder = filedialog.askdirectory(title="Select Folder Containing HTML Files")
        if not input_folder:
            return  # User cancelled

        # Extract the folder name to use as the exam name
        folder_name = os.path.basename(os.path.normpath(input_folder))
        output_json_filename = f"{folder_name}.json"
        output_json_path = os.path.join(self.exams_folder, output_json_filename)

        # Check if output JSON already exists
        if os.path.exists(output_json_path):
            overwrite = messagebox.askyesno("Overwrite Existing", f"The exam '{folder_name}.json' already exists. Do you want to overwrite it?")
            if not overwrite:
                return

        try:
            # Parse HTML to JSON
            parse_html_to_json(input_folder, output_json_path)
            messagebox.showinfo("Success", f"Parsed HTML files from '{input_folder}' and saved to '{output_json_path}'.")
            # Refresh the exams list
            self.refresh_exams()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse HTML to JSON.\n{e}")

    def load_results(self):
        """Load and display a results file."""
        # Open a dialog to select a results JSON file
        file_selected = filedialog.askopenfilename(
            title="Select Results JSON File",
            initialdir=self.results_folder,
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_selected:
            return  # User cancelled

        # Load the results and display them using ResultsWindow
        try:
            with open(file_selected, "r", encoding="utf-8") as f:
                results_data = json.load(f)
            results_window = ResultsWindow(self.master, results_data)
            results_window.focus()
            results_window.grab_set()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results file.\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()
