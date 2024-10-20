import json
import os
from jsonschema import validate, ValidationError
import logging

# load schema
def load_schema(schema_file):
    with open(os.path.join('message_schemas', schema_file), 'r') as file:
        return json.load(file)

# handle messages based on schema
def handle_message(message, client_socket, schemas):
    message_type = message.get('message_type', 'unknown')
    
    logging.info(f"Processing message of type: {message_type}")

    if message_type not in schemas:
        logging.error(f"Unknown message type: {message_type}")
        client_socket.send(json.dumps({"error": "Unknown message type"}).encode('utf-8'))
        return

    # echo back to client
    response_message = f"received {message_type}"
    logging.info(f"Sending response: {response_message}")
    client_socket.send(json.dumps({"response": response_message}).encode('utf-8'))

    # validate against schema
    try:
        validate(instance=message, schema=schemas[message_type])
        logging.info(f"Message of type {message_type} is valid.")
    except ValidationError as e:
        logging.error(f"Invalid {message_type} message: {e}")
        client_socket.send(json.dumps({"error": str(e)}).encode('utf-8'))

# preload schemas 
def load_schemas():
    return {
        "join_game": load_schema('join_game.json'),
        "start_game": load_schema('start_game.json'),
        "quiz_answer": load_schema('quiz_answer.json'),
        "quiz_question": load_schema('quiz_question.json'),
        "results": load_schema('results.json'),
        "new_connection_prompt": load_schema('new_connection_prompt.json')
    }
