import json
import os
import socket
from jsonschema import validate, ValidationError
from typing import Dict, Any

SCHEMAS_DIR = "src/utils/message_schemas"


# Preload SCHEMAS
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


# Handle messages based on schema
def receive_message(logger, message: str, sock):
    logger.debug(f"Received message: {message}")

    # Parse into object
    try:
        message_obj: Dict[str, Any] = json.loads(message)
    except Exception as e:
        logger.error(f"Error parsing JSON message into object: {e}")
        if sock:
            error_response = {"message_type": "error", "message": "Invalid JSON message"}
            sock.send(json.dumps(error_response).encode("utf-8"))
        return
    message_type = message_obj.get("message_type", "unknown")

    logger.debug(f"Processing message of type: {message_type}")

    if message_type not in SCHEMAS:
        logger.error(f"Unknown message type: {message_type}")
        if sock:
            error_response = {"message_type": "error", "message": f"Unknown message type {message_type}"}
            sock.send(json.dumps(error_response).encode("utf-8"))
        return

    # Validate against schema
    try:
        validate(instance=message_obj, schema=SCHEMAS[message_type])
        logger.debug(f"Message of type {message_type} is valid.")
    except ValidationError as e:
        logger.error(f"Invalid {message_type} message: {e}")
        if sock:
            error_response = {"message_type": "error", "message": str(e)}
            sock.send(json.dumps(error_response).encode("utf-8"))


def send_message(logger, message: Dict[str, Any], sock: socket.socket):
    message_type = message.get("message_type", "unknown")

    # Validate against schema
    try:
        validate(instance=message, schema=SCHEMAS[message_type])
        logger.debug(f"Message of type {message_type} is valid.")
    except ValidationError as e:
        logger.error(f"Invalid {message_type} message: {e}")
        return

    # Send the message with a newline delimiter
    try:
        logger.debug(f"Sending message of type: {message_type} {message}")
        if sock:
            message_str = json.dumps(message) + '\n'  # Append newline
            sock.sendall(message_str.encode("utf-8"))
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        logger.debug(f"Error sending message: {e}")
