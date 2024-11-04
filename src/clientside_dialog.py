import re
import json

def quiz_question_dialog(question_data: dict) -> str:
    # get question and answers
    question = question_data.get("question", "No question found.")
    offered_answers = question_data.get("offered-answers", [])

    # check for missing data/answers
    if not offered_answers:
        print("No answers found for the question.")
        return "No Answer"

    # display question and answers
    print("\nQuestion: " + question)
    for index, answer_obj in enumerate(offered_answers, start=1):
        answer_text = answer_obj.get("answer", "No answer text provided.")
        print(f"{index}. {answer_text}")
        
    # prompt the player for response
    while True:
        try:
            user_choice = int(input("Enter the number of your answer: "))
            if 1 <= user_choice <= len(offered_answers):
                return offered_answers[user_choice - 1]["answer"]  # return answer
            else:
                print("Invalid choice, please enter a number associated with one of the options available.")
        except ValueError:
            print("Invalid input, please enter a number.")
