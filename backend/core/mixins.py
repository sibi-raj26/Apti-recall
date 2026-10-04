from rest_framework import serializers, status
from rest_framework.response import Response


class ApiResponseMixin:
    def success_response(self, data=None, status_code=status.HTTP_200_OK, meta=None):
        payload = {"success": True, "data": data}
        if meta is not None:
            payload["meta"] = meta
        return Response(payload, status=status_code)

    def error_response(self, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
        payload = {
            "success": False,
            "error": {
                "message": message,
                "details": details or {},
            }
        }
        return Response(payload, status=status_code)
