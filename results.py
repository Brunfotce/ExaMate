# results.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText  # Using ScrolledText for better scrolling
from utils import combine_text_for_display, clean_answer_text  # Ensure clean_answer_text is imported
import base64
from PIL import Image, ImageTk
import io

class ResultsWindow(tk.Toplevel):
    def __init__(self, parent, results_data):
        super().__init__(parent)
        self.parent = parent
        self.results_data = results_data
        self.images = []  # To keep references to images

        self.title("Quiz Results")
        self.geometry("900x700")  # Increased default size for better layout
        self.resizable(True, True)

        # Configure grid to make widgets expandable
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
        self.text_area = ScrolledText(self, wrap="word", font=("Segoe UI", 11), state="disabled")
        self.text_area.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Close Button Frame
        close_frame = tk.Frame(self)
        close_frame.grid(row=3, column=0, pady=10)
        close_frame.grid_columnconfigure(0, weight=1)

        # Close Button
        close_btn = tk.Button(close_frame, text="Close", font=("Segoe UI", 12), command=self.destroy)
        close_btn.pack()

        # Configure text widget tags for styling
        self.configure_tags()

        # Populate detailed results
        self.populate_detailed_results()

    def configure_tags(self):
        """Define text tags for different styles."""
        self.text_area.tag_configure("question", font=("Segoe UI", 12, "bold"), spacing1=10, spacing3=5)
        self.text_area.tag_configure("user_answer_label", foreground="blue", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_configure("user_correct", foreground="green")
        self.text_area.tag_configure("user_incorrect", foreground="red")
        self.text_area.tag_configure("correct_answer_label", foreground="blue", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_configure("correct_answer_text", foreground="green")
        self.text_area.tag_configure("status_correct", foreground="green", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_configure("status_partially_correct", foreground="orange", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_configure("status_incorrect", foreground="red", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_configure("explanation_label", foreground="blue", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_configure("explanation_text", foreground="purple")
        self.text_area.tag_configure("image", lmargin1=20, lmargin2=20)  # Indent images
        self.text_area.tag_configure("error", foreground="red", font=("Segoe UI", 11, "bold"))

    def populate_detailed_results(self):
        self.text_area.config(state="normal")
        for idx, question in enumerate(self.results_data.get("questions", []), 1):
            # Insert Question Number and Text with Inline Images
            q_label = f"Q{idx}: "
            self.text_area.insert("end", q_label, "question")
            for ptype, content in question.get("question_parts", []):
                if ptype == "text":
                    self.text_area.insert("end", content + " ", "question")
                elif ptype == "image_base64":
                    try:
                        image = self.decode_image(content)
                        self.text_area.insert("end", "\n", "")  # Line break before image
                        self.text_area.image_create("end", image=image)
                        self.images.append(image)  # Keep a reference
                        self.text_area.insert("end", "\n", "image")  # Line break after image
                    except Exception as e:
                        self.text_area.insert("end", "[Error loading image]\n", "error")
            self.text_area.insert("end", "\n")  # Add space after question

            # Insert User's Answers with Color-Coding
            self.text_area.insert("end", "Your Answer(s):\n", "user_answer_label")
            user_picks = set(self.results_data.get("user_answers", [])[idx-1])
            correct_answers = set(question.get("correct_answers", []))
            if user_picks:
                for letter in sorted(user_picks):
                    ans_info = self.get_answer_info(question, letter)
                    ans_text = ans_info["text"]
                    full_text = f"{letter}. {ans_text}\n"
                    if letter in correct_answers:
                        self.text_area.insert("end", full_text, "user_correct")
                    else:
                        self.text_area.insert("end", full_text, "user_incorrect")
                    
                    # Insert image if exists
                    if ans_info["image"]:
                        try:
                            image = self.decode_image(ans_info["image"])
                            self.text_area.insert("end", "\n", "")  # Line break before image
                            self.text_area.image_create("end", image=image)
                            self.images.append(image)  # Keep a reference
                            self.text_area.insert("end", "\n", "image")  # Line break after image
                        except Exception as e:
                            self.text_area.insert("end", "[Error loading image]\n", "error")
            else:
                self.text_area.insert("end", "No answer selected.\n", "user_incorrect")
            self.text_area.insert("end", "\n")  # Add space after user's answers

            # Insert Correct Answers with Color-Coding
            self.text_area.insert("end", "Correct Answer(s):\n", "correct_answer_label")
            if correct_answers:
                for letter in sorted(correct_answers):
                    ans_info = self.get_answer_info(question, letter)
                    ans_text = ans_info["text"]
                    full_text = f"{letter}. {ans_text}\n"
                    self.text_area.insert("end", full_text, "correct_answer_text")
                    
                    # Insert image if exists
                    if ans_info["image"]:
                        try:
                            image = self.decode_image(ans_info["image"])
                            self.text_area.insert("end", "\n", "")  # Line break before image
                            self.text_area.image_create("end", image=image)
                            self.images.append(image)  # Keep a reference
                            self.text_area.insert("end", "\n", "image")  # Line break after image
                        except Exception as e:
                            self.text_area.insert("end", "[Error loading image]\n", "error")
            else:
                self.text_area.insert("end", "N/A\n", "correct_answer_text")
            self.text_area.insert("end", "\n")  # Add space after correct answers

            # Determine and Insert Status
            if not correct_answers:
                status = "No correct answer provided."
                status_tag = "status_incorrect"
            elif user_picks == correct_answers:
                status = "Correct"
                status_tag = "status_correct"
            elif user_picks & correct_answers:
                status = "Partially Correct"
                status_tag = "status_partially_correct"
            else:
                status = "Incorrect"
                status_tag = "status_incorrect"
            self.text_area.insert("end", f"Status: {status}\n\n", status_tag)

            # Insert Explanation if Available
            explanation = question.get("explanation", "")
            if explanation:
                self.text_area.insert("end", "Explanation:\n", "explanation_label")
                self.text_area.insert("end", f"{explanation}\n\n", "explanation_text")

        self.text_area.config(state="disabled")

    def get_answer_info(self, question, letter):
        """Retrieve answer text and image based on the letter."""
        answers = question.get("answers", [])
        ans_index = ord(letter.upper()) - ord('A')
        if 0 <= ans_index < len(answers):
            ans_parts = answers[ans_index]
            ans_text = ""
            ans_image = None
            for ptype, content in ans_parts:
                if ptype == "text":
                    ans_text += content + " "
                elif ptype == "image_base64":
                    ans_image = content
            ans_text = ans_text.strip()
            ans_text = clean_answer_text(ans_text)
            return {"text": ans_text, "image": ans_image}
        else:
            return {"text": "[Unknown]", "image": None}

    def decode_image(self, image_base64):
        """Decode base64 image data and return a PhotoImage object."""
        bdata = base64.b64decode(image_base64)
        im = Image.open(io.BytesIO(bdata))
        im.thumbnail((400, 300))  # Resize for better fit
        return ImageTk.PhotoImage(im)

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
                    # Write Question
                    q_text = combine_text_for_display(question.get("question_parts", []))
                    f.write(f"Q{idx}: {q_text}\n")
                    
                    # Indicate image if exists
                    for ptype, content in question.get("question_parts", []):
                        if ptype == "image_base64":
                            # Images are not included in text files
                            f.write("[Image]\n")

                    # Write User's Answers
                    f.write("Your Answer(s):\n")
                    user_picks = set(self.results_data.get("user_answers", [])[idx-1])
                    correct_answers = set(question.get("correct_answers", []))
                    if user_picks:
                        for letter in sorted(user_picks):
                            ans_info = self.get_answer_info(question, letter)
                            ans_text = ans_info["text"]
                            f.write(f"{letter}. {ans_text}\n")
                            # Indicate image if exists
                            if ans_info["image"]:
                                f.write("[Image]\n")
                    else:
                        f.write("No answer selected.\n")
                    
                    # Write Correct Answers
                    f.write("Correct Answer(s):\n")
                    if correct_answers:
                        for letter in sorted(correct_answers):
                            ans_info = self.get_answer_info(question, letter)
                            ans_text = ans_info["text"]
                            f.write(f"{letter}. {ans_text}\n")
                            # Indicate image if exists
                            if ans_info["image"]:
                                f.write("[Image]\n")
                    else:
                        f.write("N/A\n")
                    
                    # Write Status
                    if not correct_answers:
                        status = "No correct answer provided."
                    elif user_picks == correct_answers:
                        status = "Correct"
                    elif user_picks & correct_answers:
                        status = "Partially Correct"
                    else:
                        status = "Incorrect"
                    f.write(f"Status: {status}\n\n")

                    # Write Explanation if Available
                    explanation = question.get("explanation", "")
                    if explanation:
                        f.write("Explanation:\n")
                        f.write(f"{explanation}\n\n")
            messagebox.showinfo("Success", f"Results successfully saved to {file_path}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results.\n{e}")
