# editor.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import base64
import os

"""
A simple "Exam Editor" to create an exam from scratch and save to .json (with base64 images).
This implementation now includes rich text support and a responsive UI.
"""

class EditorWindow(tk.Toplevel):
    def __init__(self, parent, existing_exam=None, exam_path=None):
        super().__init__(parent)
        self.title("ExaMate - Exam Editor")
        self.geometry("800x700")  # Increased size for better layout
        self.minsize(700, 600)     # Minimum size for responsiveness

        self.exam_path = exam_path  # Path to existing exam
        self.questions = existing_exam.get("questions", []) if existing_exam else []  # List of question dicts

        tk.Label(self, text="Exam Editor", font=("Segoe UI",16,"bold")).pack(pady=10)

        # Frame for adding questions and listing existing ones
        frame = tk.Frame(self)
        frame.pack(pady=5, padx=10, fill="both", expand=True)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Buttons for adding, editing, deleting questions
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=0, column=0, sticky="ew", pady=5)
        btn_frame.grid_columnconfigure((0,1,2), weight=1)

        add_btn = tk.Button(btn_frame, text="Add Question", command=self.add_question)
        add_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        edit_btn = tk.Button(btn_frame, text="Edit Selected Question", command=self.edit_selected_question)
        edit_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        delete_btn = tk.Button(btn_frame, text="Delete Selected Question", command=self.delete_selected_question)
        delete_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Listbox to display questions
        self.questions_listbox = tk.Listbox(frame, font=("Segoe UI",11))
        self.questions_listbox.grid(row=1, column=0, sticky="nsew", pady=5)
        self.refresh_questions_listbox()

        # Scrollbar for the listbox
        list_scroll = tk.Scrollbar(frame, orient="vertical", command=self.questions_listbox.yview)
        list_scroll.grid(row=1, column=1, sticky="ns")
        self.questions_listbox.config(yscrollcommand=list_scroll.set)

        # Buttons for saving and closing
        save_btn = tk.Button(frame, text="Save Exam to JSON", font=("Segoe UI",12), command=self.save_exam)
        save_btn.grid(row=2, column=0, pady=5, sticky="ew")

        close_btn = tk.Button(frame, text="Close Editor", font=("Segoe UI",12), command=self.destroy)
        close_btn.grid(row=3, column=0, pady=5, sticky="ew")

    def refresh_questions_listbox(self):
        self.questions_listbox.delete(0, tk.END)
        for idx, q in enumerate(self.questions, start=1):
            qnum = q.get("question_number", "?")
            self.questions_listbox.insert(tk.END, f"Q{idx}: #{qnum}")

    def add_question(self):
        # Open a dialog to input question details
        dialog = QuestionEditorDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.questions.append(dialog.result)
            self.refresh_questions_listbox()
            messagebox.showinfo("Success", "Question added successfully!")

    def edit_selected_question(self):
        selected = self.questions_listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a question to edit.")
            return
        index = selected[0]
        question = self.questions[index]

        # Open a dialog with existing question data
        dialog = QuestionEditorDialog(self, existing_question=question)
        self.wait_window(dialog)
        if dialog.result:
            self.questions[index] = dialog.result
            self.refresh_questions_listbox()
            messagebox.showinfo("Success", "Question updated successfully!")

    def delete_selected_question(self):
        selected = self.questions_listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a question to delete.")
            return
        index = selected[0]
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Question {index+1}?")
        if confirm:
            del self.questions[index]
            self.refresh_questions_listbox()
            messagebox.showinfo("Deleted", "Question deleted successfully!")

    def save_exam(self):
        if not self.questions:
            messagebox.showerror("Error", "No questions to save.")
            return
        exam_title = simpledialog.askstring("Exam Title", "Enter the exam title:", initialvalue="Untitled Exam")
        if not exam_title:
            exam_title = "Untitled Exam"
        data = {
            "title": exam_title,
            "questions": self.questions
        }

        if self.exam_path:
            # Overwrite existing exam
            try:
                with open(self.exam_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Exam saved to {self.exam_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save exam.\n{e}")
        else:
            # Save as new exam
            save_path = filedialog.asksaveasfilename(
                title="Save Exam as JSON",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")]
            )
            if not save_path:
                return
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Exam saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save exam.\n{e}")

class QuestionEditorDialog(tk.Toplevel):
    """
    A dialog to input question details: number, text, images, answers, correct answers.
    Supports rich text formatting using Markdown-like syntax.
    """
    def __init__(self, parent, existing_question=None):
        super().__init__(parent)
        self.title("Add/Edit Question")
        self.geometry("700x800")  # Increased size for better layout
        self.minsize(600, 700)     # Minimum size for responsiveness

        self.result = None  # To store the question data

        # Frame for all widgets
        frame = tk.Frame(self)
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # Question Number
        tk.Label(frame, text="Question Number:", font=("Segoe UI",11)).grid(row=0, column=0, sticky="w", pady=5)
        self.qnum_var = tk.StringVar()
        if existing_question:
            self.qnum_var.set(existing_question.get("question_number", ""))
        tk.Entry(frame, textvariable=self.qnum_var, width=10, font=("Segoe UI",11)).grid(row=0, column=1, sticky="w", pady=5)

        # Question Text with Rich Text Support
        tk.Label(frame, text="Question Text (Use Markdown for rich text):", font=("Segoe UI",11)).grid(row=1, column=0, sticky="nw", pady=5)
        self.qtext_box = tk.Text(frame, height=10, wrap="word", font=("Segoe UI",11))
        if existing_question:
            # Combine question parts text
            qtext = " ".join([part[1] for part in existing_question.get("question_parts", []) if part[0] == "text"])
            self.qtext_box.insert("1.0", qtext)
        self.qtext_box.grid(row=1, column=1, sticky="nsew", pady=5)

        # Button to attach image to question
        img_btn = tk.Button(frame, text="Attach Image to Question", command=self.attach_question_image)
        img_btn.grid(row=2, column=1, sticky="w", pady=5)

        if existing_question:
            # If there's an image, indicate it
            for part in existing_question.get("question_parts", []):
                if part[0] == "image_base64":
                    self.question_image = part[1]
                    messagebox.showinfo("Image Attached", "An image is already attached to this question.")

        # Answers Section
        tk.Label(frame, text="Answers:", font=("Segoe UI",11,"bold")).grid(row=3, column=0, sticky="nw", pady=5)
        self.answers = []
        for i in range(4):
            ans_frame = tk.Frame(frame)
            ans_frame.grid(row=4+i, column=0, columnspan=2, sticky="ew", pady=2)
            ans_frame.grid_columnconfigure(1, weight=1)

            tk.Label(ans_frame, text=f"Answer {chr(65+i)}:", font=("Segoe UI",11)).grid(row=0, column=0, sticky="w")
            ans_entry = tk.Entry(ans_frame, font=("Segoe UI",11))
            if existing_question:
                if i < len(existing_question.get("answers", [])):
                    ans_text = " ".join([part[1] for part in existing_question["answers"][i] if part[0] == "text"])
                    ans_entry.insert(0, ans_text)
            ans_entry.grid(row=0, column=1, sticky="ew", padx=5)

            img_btn_ans = tk.Button(ans_frame, text="Attach Image", command=lambda idx=i: self.attach_answer_image(idx))
            img_btn_ans.grid(row=0, column=2, padx=5)

            self.answers.append({
                "text_var": ans_entry,
                "image_data": None  # To store base64 image data
            })

            if existing_question:
                # Load existing answer images if any
                if i < len(existing_question.get("answers", [])):
                    for part in existing_question["answers"][i]:
                        if part[0] == "image_base64":
                            self.answers[i]["image_data"] = part[1]
                            messagebox.showinfo("Image Attached", f"An image is already attached to Answer {chr(65+i)}.")

        # Correct Answers Entry
        tk.Label(frame, text="Correct Answer(s) (e.g., A,C):", font=("Segoe UI",11)).grid(row=8, column=0, sticky="w", pady=5)
        self.correct_var = tk.StringVar()
        if existing_question:
            self.correct_var.set(",".join(existing_question.get("correct_answers", [])))
        tk.Entry(frame, textvariable=self.correct_var, font=("Segoe UI",11)).grid(row=8, column=1, sticky="w", pady=5)

        # Save Question Button
        save_btn = tk.Button(frame, text="Save Question", font=("Segoe UI",12), command=self.save_question)
        save_btn.grid(row=9, column=1, sticky="e", pady=10)

    def attach_question_image(self):
        path = filedialog.askopenfilename(
            title="Select Image for Question",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")]
        )
        if not path:
            return
        try:
            with open(path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            self.question_image = encoded
            messagebox.showinfo("Success", "Image attached to question.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to attach image.\n{e}")

    def attach_answer_image(self, index):
        path = filedialog.askopenfilename(
            title=f"Select Image for Answer {chr(65+index)}",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")]
        )
        if not path:
            return
        try:
            with open(path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            self.answers[index]["image_data"] = encoded
            messagebox.showinfo("Success", f"Image attached to Answer {chr(65+index)}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to attach image.\n{e}")

    def save_question(self):
        qnum = self.qnum_var.get().strip()
        qtext = self.qtext_box.get("1.0", "end").strip()
        correct = [x.strip().upper() for x in self.correct_var.get().split(",") if x.strip()]
        if not qtext or not correct:
            messagebox.showerror("Error", "Question text and correct answers are required.")
            return
        # Build question_parts with rich text
        question_parts = [("text", qtext)]
        if hasattr(self, 'question_image'):
            question_parts.append(("image_base64", self.question_image))
        # Build answers with rich text
        answers = []
        for ans in self.answers:
            parts = [("text", ans["text_var"].get().strip())]
            if ans["image_data"]:
                parts.append(("image_base64", ans["image_data"]))
            answers.append(parts)
        # Build question object
        qobj = {
            "question_number": qnum if qnum else "0",
            "question_parts": question_parts,
            "answers": answers,
            "correct_answers": correct
        }
        self.result = qobj
        self.destroy()
