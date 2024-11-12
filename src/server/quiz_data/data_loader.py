import json
import logging
import os
from typing import List, Dict, Union

QUIZ_DATA_DIR = "src/server/quiz_data"


class QuizDataLoader:
    def __init__(self, directory: str = QUIZ_DATA_DIR):
        self.directory = directory
        self.quiz_data: List[Dict[str, Union[int, List[Dict]]]] = []  # adjust
        self.load_quiz_files()

    def load_quiz_files(self):
        logging.info(f"loading quiz data from directory: {self.directory}")
        # check if directory exists
        if not os.path.exists(self.directory):
            logging.error(f"directory {self.directory} does not exist.")
            return
        # iterate over all JSON files
        for filename in os.listdir(self.directory):
            if filename.endswith(".json"):
                filepath = os.path.join(self.directory, filename)
                try:
                    with open(filepath, "r") as file:
                        data = json.load(file)
                        if self.validate_quiz_format(data):
                            self.quiz_data.append(data)
                            logging.info(f"loaded and validated {filename}")
                        else:
                            logging.warning(f"invalid format in file: {filename}")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logging.error(f"error loading file {filename}: {e}")

    # TODO: use json validator lol
    def validate_quiz_format(self, data) -> bool:
        if "number" not in data or "questions" not in data:
            logging.error(f"missing 'number' or 'questions' in quiz data: {data}")
            return False

        # validate question structure
        for question in data["questions"]:
            if not all(
                key in question
                for key in ("number", "topic", "question", "offered-answers")
            ):
                logging.error(f"missing required keys in quiz question: {question}")
                return False
            if not isinstance(question["offered-answers"], list) or not isinstance(
                question["question"], str
            ):
                logging.error(f"invalid types in quiz question: {question}")
                return False
        return True

    def get_quiz_data(self) -> List[Dict[str, Union[int, List[Dict]]]]:
        return self.quiz_data
