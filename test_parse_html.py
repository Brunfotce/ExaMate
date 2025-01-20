# test_parse_html.py

import unittest
import os
import json
from parse_html import parse_html_to_json

class TestParseHTML(unittest.TestCase):
    def setUp(self):
        self.input_folder = "test_html"
        self.output_json = "test_output.json"
        os.makedirs(self.input_folder, exist_ok=True)
        # Create a sample HTML file
        sample_html = '''
        <div class="card exam-question-card">
            <div class="card-header text-white bg-primary">Question #1Topic</div>
            <div class="card-body">
                <p class="card-text">
                    A company has an application that uses Amazon Cognito user pools as an identity provider. The company must secure access to user records. The company has set up multi-factor authentication (MFA). The company also wants to send a login activity notification by email every time a user logs in. What is the MOST operationally efficient solution that meets this requirement?
                </p>
                <ul>
                    <li class="multi-choice-item">A. A. Create an AWS Lambda function that uses Amazon Simple Email Service (Amazon SES) to send the email notification. Add an Amazon API Gateway API to invoke the function. Call the API from the client side when login confirmation is received.</li>
                    <li class="multi-choice-item">B. B. Create an AWS Lambda function that uses Amazon Simple Email Service (Amazon SES) to send the email notification. Add an Amazon Cognito post authentication Lambda trigger for the function.</li>
                    <li class="multi-choice-item">C. C. Create an AWS Lambda function that uses Amazon Simple Email Service (Amazon SES) to send the email notification. Create an Amazon CloudWatch Logs log subscription filter to invoke the function based on the login status.</li>
                    <li class="multi-choice-item correct">D. D. Configure Amazon Cognito to stream all logs to Amazon Kinesis Data Firehose. Create an AWS Lambda function to process the streamed logs and to send the email notification based on the login status of each user.</li>
                </ul>
            </div>
        </div>
        '''
        with open(os.path.join(self.input_folder, "sample.html"), "w", encoding="utf-8") as f:
            f.write(sample_html)

    def test_parse_html(self):
        parse_html_to_json(self.input_folder, self.output_json)
        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["questions"]), 1)
        question = data["questions"][0]
        self.assertEqual(question["question_number"], "1Topic")
        self.assertEqual(question["correct_answers"], ["D"])
        # Check that answers have single labels
        for answer in question["answers"]:
            # The answer text should not start with a label like "A. "
            self.assertFalse(re.match(r'^[A-Z]\.\s+[A-Z]\.\s', answer["text"]))
            # It should not contain duplicated labels; no "A. A. "
            self.assertFalse("A. A." in answer["text"])
            self.assertFalse("B. B." in answer["text"])
            self.assertFalse("C. C." in answer["text"])
            self.assertFalse("D. D." in answer["text"])
            # Instead, labels should be handled by the GUI, so answer texts should start directly with the content

    def tearDown(self):
        # Clean up test files
        for file in os.listdir(self.input_folder):
            os.remove(os.path.join(self.input_folder, file))
        os.rmdir(self.input_folder)
        if os.path.exists(self.output_json):
            os.remove(self.output_json)

if __name__ == '__main__':
    unittest.main()
