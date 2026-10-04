from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "error": {
                "code": getattr(exc, "default_code", "error").upper(),
                "message": str(exc),
                "details": response.data,
            }
        }
    return response
