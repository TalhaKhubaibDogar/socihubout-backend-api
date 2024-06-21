from typing import Union, Optional, Dict, Any, List


def success_response_builder(
    message: Optional[str] = None,
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    code: int = 200,
    default_message: str = "Success"
) -> Dict[str, Any]:
    """
    Builds a success response dictionary with the provided parameters.

    Args:
        message (Optional[str], optional): The success message. Defaults to None.
        data (Optional[Union[Dict[str, Any], List[Dict[str, Any]]]], optional): The data payload. Defaults to None.
        code (int, optional): The success response code. Defaults to 200.
        default_message (str, optional): The default success message. Defaults to "Success".

    Returns:
        Dict[str, Any]: The success response dictionary.
    """
    response = {
        'meta': {
            'code': code,
            'message': message or default_message
        },
        'response': data or {}
    }

    return response


def error_response_builder(
    message: Optional[str] = None,
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    code: int = 400,
    default_message: str = "Failed"
) -> Dict[str, Any]:
    """.
    Args:
        message (Optional[str], optional): The error message. Defaults to None.
        data (Optional[Union[Dict[str, Any], List[Dict[str, Any]]]], optional): The data payload. Defaults to None.
        code (int, optional): The error response code. Defaults to 400.
        default_message (str, optional): The default error message. Defaults to "Failed".

    Returns:
        Dict[str, Any]: The error response dictionary.
    """
    response = {
        'meta': {
            'code': code,
            'message': message or default_message
        },
        'response': data or {}
    }

    return response
