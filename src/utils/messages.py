import json
import os
import socket
from jsonschema import validate, ValidationError
from typing import Dict, Any

SCHEMAS_DIR = "src/utils/message_schemas"


# preload SCHEMAS
def load_schemas():
    def load_schema(schema_file):
        with open(os.path.join(SCHEMAS_DIR, schema_file), "r") as file:
            return json.load(file)

    schemas = os.listdir(SCHEMAS_DIR)
    return {
        schema.split(".")[0]: load_schema(schema)
        for schema in schemas
        if schema.endswith(".json")
    }


SCHEMAS = load_schemas()


# handle messages based on schema
def receive_message(logger, message: str, sock=None):
    logger.debug(f"Received message: {message}")

    # parse into object
    try:
        message_obj: Dict[str, Any] = json.loads(message)
    except Exception as e:
        logger.error(f"Error parsing json message into object: {e}")
        if sock:
            sock.send(json.dumps({"error": "Invalid JSON message"}).encode("utf-8"))
        return
    message_type = message_obj.get("message_type", "unknown")

    logger.debug(f"Processing message of type: {message_type}")

    if message_type not in SCHEMAS:
        logger.error(f"Unknown message type: {message_type}")
        if sock:
            sock.send(
                json.dumps({"error": f"Unknown message type {message_type}"}).encode(
                    "utf-8"
                )
            )
        return

    # validate against schema
    try:
        validate(instance=message_obj, schema=SCHEMAS[message_type])
        logger.debug(f"Message of type {message_type} is valid.")
    except ValidationError as e:
        logger.error(f"Invalid {message_type} message: {e}")
        if sock:
            sock.send(json.dumps({"error": str(e)}).encode("utf-8"))


def send_message(logger, message: Dict[str, Any], sock=None):
    message_type = message.get("message_type", "unknown")

    # Validate against schema
    try:
        validate(instance=message, schema=SCHEMAS[message_type])
        logger.debug(f"Message of type {message_type} is valid.")
    except ValidationError as e:
        logger.error(f"Invalid {message_type} message: {e}")
        return

    # Send the message
    try:
        logger.debug(f"Sending message of type: {message_type}")
        if sock:
            sock.send(json.dumps(message).encode("utf-8"))
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        logger.error(f"Error sending message to client: {e}")
        # Handle the disconnection if necessary


MOCKS = {
    "new_connection_prompt": {
        "message_type": "new_connection_prompt",
        "current_games": ["abc", "def", "ghi"],
        "current_players": ["jim", "andy", "max"],
        "chapters_available": [
            {"chapter": 1, "questions": 10},
            {"chapter": 2, "questions": 10},
            {"chapter": 3, "questions": 25},
        ],
    },
    "create_game": {
        "message_type": "start_game",
        "player_name": "Bob",
        "is_private": False,
        "chapters": [1, 3],
        "num_questions": 10,
    },
    "join_game": {
        "message_type": "join_game",
        "player_name": "Alice",
        "game_id": "abc",
    },
    "quiz_question": {
        "message_type": "quiz_question",
        "chapter": 1,
        "question": "What is the capital of France?",
        "possible_answers": ["Paris", "London", "Berlin", "Madrid"],
    },
    "quiz_answer": {
        "message_type": "quiz_answer",
        "question": "What is the capital of France?",
        "answer": "Madrid",
    },
    "results": {
        "message_type": "results",
        "players": [
            {
                "player_name": "Alice",
                "results": [
                    {
                        "chapter": 1,
                        "question": "What is the capital of France?",
                        "answer": "Paris",
                        "submitted_answer": "Paris",
                        "correct_answer": "Paris",
                        "is_correct": True,
                    },
                    {
                        "chapter": 2,
                        "question": "What is the capital of Germany?",
                        "answer": "Berlin",
                        "submitted_answer": "Madrid",
                        "correct_answer": "Berlin",
                        "is_correct": False,
                    },
                ],
            }
        ],
    },
}
