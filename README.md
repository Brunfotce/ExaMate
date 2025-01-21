# ExaMate - ExamTopics Scraper & Quiz Maker

**ExaMate** is a Python desktop application with a user-friendly GUI that allows you to **parse**, **manage**, and **take quizzes** based on exam questions from **ExamTopics**—all **offline**. Simply **download** or **save** the ExamTopics webpages as HTML, place them in a designated folder, and ExaMate will create an interactive quiz experience for you. Enjoy features like images, multi-answer partial credit, question navigation, smooth mouse wheel scrolling, detailed results with color-coding, and more!

> **Important**: This tool is **not** affiliated with ExamTopics. You must **manually save** the pages from the ExamTopics website (HTML only) and place them in the correct folders. ExaMate then parses the local HTML to provide you with a comprehensive quiz.

---

## 🚀 Features

- **Offline Functionality**: No internet connection required once you've saved the HTML pages.
- **Interactive Quiz Interface**:
  - **Question Navigation**: Easily navigate between questions using **Previous**, **Next**, or the **Navigator Sidebar**.
  - **Mouse Wheel Scrolling**: Smooth scrolling in both the navigator and answers area.
- **Comprehensive Answer Handling**:
  - **Multiple Answers with Partial Credit**: Supports questions with multiple correct answers, awarding partial credit accordingly.
  - **Answer Checkmark Indicators**: Quick visual cues in the navigator to show which questions have been answered.
- **Rich Content Support**:
  - **Images in Questions and Answers**: Display images embedded in both questions and answers seamlessly.
- **Detailed Results**:
  - **Color-Coded Feedback**: Review your performance with green (correct), red (incorrect), and orange (partially correct) indicators.
  - **Save Results**: Manually save your quiz results as a text file for future reference.
- **Flexible Quiz Configuration**:
  - **Customizable Quiz Length**: Select the number of questions you wish to attempt in each session.
- **Automated Folder Management**:
  - **Automatic Creation of `exams` Folder**: ExaMate automatically creates the `exams` folder to store parsed JSON files.

---

## 📸 Example GUI Flow
![imagen](https://github.com/user-attachments/assets/1258b072-5f05-4f30-85fe-7036efb5f555)


1. **Select an Exam**:
   - Choose a quiz folder from the dropdown menu. This folder should contain the saved HTML pages (e.g., `./res/MyExam`).
2. **Configure Quiz Settings**:
   - **Number of Questions**: Enter the number of questions you wish to attempt in the quiz session.
3. **Start the Quiz**:
   - Click **Start Quiz** to begin. An interactive quiz window will open.
4. **Quiz Interface**:
   - **Left Sidebar**: Navigate through questions using the scrollable list (`Q1`, `Q2`, etc.).
   - **Main Area**: View the question text, any associated images, and available answers (which may include images).
   - **Navigation Buttons**: Use **Previous**, **Next**, or click directly on a question in the navigator to move around.
5. **Finish Exam**:
   - Click **Finish Exam** to end the session.
   - Review your final score and detailed feedback, including which answers were correct, incorrect, or partially correct.
   - Optionally, save your results for later reference.

![imagen](https://github.com/user-attachments/assets/91ffbd75-07a8-456e-a570-e45564bcb71c)


*Image: Overview of the ExaMate Quiz Interface*

---

## 📥 Downloading Exams from ExamTopics

To use ExaMate effectively, you need to download and save the exam pages from ExamTopics. Follow these steps:

1. **Navigate to the Exam Page:**
   - Open your web browser and go to the specific exam page on [ExamTopics](https://www.examtopics.com/).
   - Example: `https://www.examtopics.com/exams/aws/aws-certified-developer-associate/`

2. **Save the Web Page:**
   - Press `Ctrl + S` (Windows) or `Cmd + S` (macOS) on your keyboard.
   - In the save dialog, choose **"Webpage, HTML Only"** or a similar option.

3. **Create an Exam Folder:**
   - Create a new folder named after the exam (e.g., `AWS Developer Associate`) within the `res` directory inside the ExaMate project folder.
   - Example path: `./res/AWS Developer Associate/`

4. **Save All Relevant Pages:**
   - If the exam spans multiple pages, navigate to each page and repeat the save process, ensuring all pages are saved within the same exam folder.
   - Ensure all associated assets (like images) are correctly saved.

5. **Parse HTML to JSON:**
   - Launch ExaMate by running `python main.py`.
   - In the **Main Menu**, click on **"Parse Exam Topics HTML to JSON"**.

6. **Select the Exam Folder:**
   - A dialog will appear prompting you to select the folder containing your saved HTML pages.
   - Navigate to the exam folder you created earlier (e.g., `./res/AWS Developer Associate/`) and select it.

7. **Automatic Conversion:**
   - ExaMate will parse all HTML files in the selected folder and convert them into a single JSON file.
   - The JSON file is automatically saved in the `./exams` folder, which ExaMate creates if it doesn't already exist.
   - **Note:** The JSON includes all images encoded in base64, allowing you to delete the original HTML folder if it's no longer needed.

8. **Load Your Exam:**
   - After parsing, return to the **Main Menu**.
   - Use the **"Pick an Exam"** dropdown to select the newly created JSON file from the `./exams` folder.
   - Configure your quiz settings and start your quiz!

---

## 🧑‍💻 Usage Guide

### 1. Prepare Your Exam Data

**Downloading Exams from ExamTopics:**

To use ExaMate effectively, you need to download and save the exam pages from ExamTopics. Follow these steps:

1. **Navigate to the Exam Page:**
   - Open your web browser and go to the specific exam page on [ExamTopics](https://www.examtopics.com/).
   - Example: `https://www.examtopics.com/exams/aws/aws-certified-developer-associate/`

2. **Save the Web Page:**
   - Press `Ctrl + S` (Windows) or `Cmd + S` (macOS) on your keyboard.
   - In the save dialog, choose **"Webpage, HTML Only"** or a similar option.

3. **Create an Exam Folder:**
   - Create a new folder named after the exam (e.g., `AWS Developer Associate`) within the `res` directory inside the ExaMate project folder.
   - Example path: `./res/AWS Developer Associate/`

4. **Save All Relevant Pages:**
   - If the exam spans multiple pages, navigate to each page and repeat the save process, ensuring all pages are saved within the same exam folder.
   - Ensure all associated assets (like images) are correctly saved.

### 2. Launch ExaMate

Open ExaMate by running `python main.py` as described in the usage instructions.

### 3. Parse HTML Exams to JSON

ExaMate converts your saved HTML exam pages into JSON files for the quiz functionality.

1. **Parse HTML to JSON:**
   - In the **Main Menu**, click on **"Parse Exam Topics HTML to JSON"**.

2. **Select the Exam Folder:**
   - A dialog will appear prompting you to select the folder containing your saved HTML pages.
   - Navigate to the exam folder you created earlier (e.g., `./res/AWS Developer Associate/`) and select it.

3. **Automatic Conversion:**
   - ExaMate will parse all HTML files in the selected folder and convert them into a single JSON file.
   - The JSON file is automatically saved in the `./exams` folder, which ExaMate creates if it doesn't already exist.
   - **Note:** The JSON includes all images encoded in base64, allowing you to delete the original HTML folder if it's no longer needed.

4. **Confirmation:**
   - After successful parsing, you'll receive a confirmation message indicating that the JSON file has been created.

### 4. Take a Quiz

1. **Select an Exam:**
   - In the **Main Menu**, use the **"Pick an Exam"** dropdown to select the JSON file corresponding to your exam (located in the `./exams` folder).

2. **Configure Quiz Settings:**
   - **Only Multi-Answer**: Check this box if you want the quiz to include only questions with multiple correct answers.
   - **Number of Questions**: Enter the number of questions you wish to attempt in the quiz session.

3. **Start the Quiz:**
   - Click **Start Quiz** to begin. An interactive quiz window will open.

4. **Navigating the Quiz:**
   - **Left Sidebar**: Use the navigator to jump to any question directly.
   - **Main Area**: Read each question, view associated images, and select your answers.
   - **Navigation Buttons**: Use **Previous**, **Next**, or click directly on a question in the navigator to move between questions.

5. **Finish the Quiz:**
   - Click **Finish Exam** to conclude the session.
   - Review your **final score** and **detailed results**, including which answers were correct, incorrect, or partially correct.
   - **Save Results**: Optionally, click the **"Save Results"** button to export your performance summary as a text file.

### 5. Load Previous Results

1. **Access Results:**
   - From the **Main Menu**, click on **"Load Results File"**.

2. **Select a Results File:**
   - A dialog will appear prompting you to select a JSON file from the `./results` folder.

3. **View Results:**
   - ExaMate will open a window displaying your quiz results, including detailed feedback on each question.

---

## 🐞 Troubleshooting

### **1. Images Not Displaying Correctly**

**Possible Causes:**

- Incorrect folder structure leading to broken image links.
- Images not saved in the expected format or corrupted.

**Solutions:**

- Verify that images are correctly saved and referenced in the HTML files.
- Ensure that image paths in the HTML match their actual locations in the folder structure.
- Re-save the HTML pages if necessary, ensuring all assets are correctly captured.

### **2. Application Crashing or Not Starting**

**Possible Causes:**

- Missing dependencies.
- Corrupted installation files.

**Solutions:**

- Reinstall dependencies using `pip install -r requirements.txt`.
- Re-clone the repository or download the latest release to ensure all files are intact.

### **3. Scrollbars Not Working Smoothly**

**Possible Causes:**

- Platform-specific mouse wheel event handling issues.

**Solutions:**

- The updated `quizgui.py` includes bindings for Linux mouse wheel events. If you're on a different platform, ensure that mouse wheel scrolling is properly configured.
- Consider adjusting the `mousewheel` event bindings in `quizgui.py` if issues persist.


---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your enhancements or bug fixes.

---

## 📞 Contact

For any questions, issues, or suggestions, feel free to open an issue on the [GitHub repository](https://github.com/draczer01/ExaMate/issues) or contact the maintainer directly.

---

## 📝 Acknowledgements

- Inspired by [ExamTopics](https://www.examtopics.com/) for providing comprehensive exam question repositories.
- Developed using Python's `tkinter` library for the GUI and `Pillow` for image handling.

---

