import logging
from quiz_data_loader import QuizDataLoader 

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
data_directory = "quiz_data"  # adjust to path
quiz_loader = QuizDataLoader(directory=data_directory)
# load quiz files
quiz_loader.load_quiz_files()
# print loaded data
loaded_data = quiz_loader.get_quiz_data()
print("Loaded Quiz Data:")
for quiz in loaded_data:
    print(json.dumps(quiz, indent=4))  # Pretty-print the JSON data
# check if data loaded successfully
if loaded_data:
    logging.info("Quiz data loaded successfully!")
else:
    logging.error("No valid quiz data loaded.")
