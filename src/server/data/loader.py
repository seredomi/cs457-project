import json
from jsonschema import validate, ValidationError
import logging
import os

QUIZ_DATA_DIR = "src/server/data/chapters/"
QUIZ_SCHEMA = "src/server/data/chapter-schema.json"


class QuizDataLoader:
    def __init__(self, logger, directory: str = QUIZ_DATA_DIR):
        self.logger = logger
        self.directory = directory
        self.quiz_schema = self.load_quiz_schema()
        self.quiz_data = []
        self.load_quiz_files()

    def load_quiz_schema(self):
        with open(QUIZ_SCHEMA, "r") as file:
            return json.load(file)

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

    def validate_quiz_format(self, data):
        try:
            validate(instance=data, schema=self.quiz_schema)
        except ValidationError as e:
            logging.error(f"Invalid quiz format: {e}")
            return False
        return True