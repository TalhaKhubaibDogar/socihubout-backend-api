from typing import Union, Optional, Dict, Any, List

def success_response_builder(
    message: Optional[str] = None,
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    code: int = 200,
    default_message: str = "Success"
) -> Dict[str, Any]:
    response = {
        'meta': {
            'code': code,
            'status': default_message,
            'message': message or default_message
        },
        'response': data or {}
    }
    return response


def error_response_builder(
    message: Optional[Union[str, Dict[str, List[str]]]] = None,
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    code: int = 400,
    default_message: str = "Failed"
) -> Dict[str, Any]:
    print("------>", message)
    if message is None:
        print("here1")
        message = default_message
    elif isinstance(message, str):
        print("str")
        pass
    elif isinstance(message, dict):
        error_messages = []
        for field_errors in message.values():
            error_messages.extend(field_errors)
        message = error_messages
    else:
        print("else")
        message = message

    if isinstance(message, list) and len(message) == 1:
        message = message[0]

    response = {
        'meta': {
            'code': code,
            'status': default_message,
            'message': message
        },
        'response': data or {}
    }
    return response