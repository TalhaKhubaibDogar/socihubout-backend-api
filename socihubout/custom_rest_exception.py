from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from common.utils import error_response_builder as er
from common.messages import (
    UNEXPECTED_ERROR,
    PERMISSION_DENIED
)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print(exc)
    if response is not None:
        if response.status_code == 401:
            if isinstance(exc, AuthenticationFailed):
                error_detail = exc.detail.get('detail', '')
                error_code = exc.detail.get('code', '')
                custom_response_data = {
                    "code": response.status_code,
                    "message_code": "Permission Denied",
                    "data": {
                        "message": error_detail
                    }
                }
                response.data = custom_response_data
            else:

                custom_response_data = er(code=401, default_message=PERMISSION_DENIED ,message=str(exc))
                response.data = custom_response_data


        elif response.status_code == 404 and isinstance(exc, NotFound):
            if 'Invalid cursor' in str(exc.detail):
                response.data = {
                    "code": 403,
                    "message_code": "Invalid Cursor",
                    "data": {
                        "message": "No results found for the provided cursor"
                    }
                }
            else:
                response.data = {
                    "code": 404,
                    "message_code": "Not found",
                    "data": {
                        "message": "No Record"
                    }
                }
        elif response.status_code == 403:
            if 'You do not have permission to perform this action.' in str(exc):
                response.data = {
                    "code": 403,
                    "message_code": "Error",
                    "data": {
                        "message": "Only Host can have Events"
                    }
                }
            elif 'Hotspot is not allowed' in str(exc):
                response.data = {
                    "code": 403,
                    "message_code": "Error",
                    "data": {
                        "message": "Only Type User Allowed"
                    }
                }
            elif 'Event owner can view only' in str(exc):
                response.data = {
                    "code": 403,
                    "message_code": "Error",
                    "data": {
                        "message": "Event owner can view only"
                    }
                }
            elif "Wallet owner can withdraw" in str(exc):
                response.data = {
                    "code": 403,
                    "message_code": "Error",
                    "data": {
                        "message": "Wallet owner can withdraw"
                    }
                }
            else:
                response.data = {
                    "code": 404,
                    "message_code": "Not found",
                    "data": {
                        "message": "No Record"
                    }
                }
    else:
        response = Response(er(code=500, message=UNEXPECTED_ERROR), status=500)

    # Set exception attribute if response has status_code attribute
    if hasattr(response, 'status_code'):
        response.exception = True

    return response
