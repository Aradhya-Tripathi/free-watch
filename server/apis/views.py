import os
import time
from typing import Union, Dict

import psutil
from asgiref.sync import async_to_sync
from authentication import issue_keys, permissions, utils
from channels.layers import get_channel_layer
from core.throttle import throttle
from django.http import request
from django.http.response import JsonResponse
from rest_framework.views import APIView

from .checks import enter_user, insert_data, login
from .definitions import UserSchema
from core.settings import conf


class HealthCheck(APIView):
    throttle_classes = [throttle]

    def get(self, request: request, **kwargs) -> JsonResponse:
        """Health check route

        Args:
            request (request): Request

        Returns:
            JsonResponse: Uptime
        """
        uptime = time.time() - psutil.Process(os.getpid()).create_time()
        return JsonResponse(data={"uptime": uptime, "OK": True}, status=200)


class Register(APIView):
    throttle_classes = [throttle]

    def post(self, request: request, **kwargs) -> JsonResponse:
        """Register users

        Args:
            request (request): wsgi request

        Returns:
            JsonResponse: Response
        """
        validate = UserSchema(data=request.data, register=True).approval()

        if "error" in validate:
            return JsonResponse(data={"error": validate["error"]}, status=400)

        if value := enter_user(validate):
            return JsonResponse(data={"error": str(value)}, status=400)

        return JsonResponse(data={"success": True}, status=201)


class Login(APIView):
    throttle_classes = [throttle]

    def post(self, request: request, **kwargs) -> JsonResponse:
        """Login users

        Args:
            request (request): wsgi request

        Returns:
            JsonResponse: Response
        """
        validate = UserSchema(data=request.data).approval()

        if "error" in validate:
            return JsonResponse(data={"error": validate["error"]}, status=400)

        creds = login(password=validate.get("password"), email=validate.get("email"))

        if isinstance(creds, str):
            return JsonResponse(data={"error": creds}, status=403)
        payload = {"user_name": creds["user_name"]}
        key = issue_keys.generate_key(
            payload=payload, expiry=1, get_refresh=True, refresh_exipry=12
        )
        return JsonResponse(
            data={"access_token": key["access_token"], "refresh_token": key["refresh_token"]},
            status=200,
        )


class ProtectedView(APIView):
    throttle_classes = [throttle]

    def get(self, request: request, **kwargs) -> JsonResponse:
        """Test protected route

        Args:
            request (request): request object

        Returns:
            JsonResponse: Response
        """
        return JsonResponse(data={"success": True}, status=200)


class CollectData(APIView):
    permission_classes = [permissions.ValidateUnit]
    throttle_classes = [throttle]

    def post(self, request: request, **kwargs) -> JsonResponse:
        """Accept data dumps from device

        Args:
            request (request): wsgi request

        Returns:
            JsonResponse: Response
        """
        if insert_data(unit_id=request.unit_id, data=request.data):
            return JsonResponse(data={}, status=201)
        return JsonResponse(data={}, status=400)


class SOS(APIView):
    permission_classes = [permissions.ValidateUnit]
    group_name = conf["socket"]["base_group"]
    channel_layer = get_channel_layer()

    def send_alert(self, token: str, data: Dict[str, Union[str, int]]) -> None:
        """Send alert to group.
           Get group id -> common `group_name` + `unit_id`
           send alert to that group

        Args:
            token (str): unit_id
            data (Dict[str, Union[str, int]]): alert data

        Returns:
            None
        """
        # TODO: Include email

        group_id = self.group_name + str(token)
        async_to_sync(self.channel_layer.group_send)(
            group_id, {"type": "send.alert", "content": data}
        )
        return None

    def post(self, request: request, **kwargs) -> JsonResponse:
        """Accept alert from device

        Args:
            request (request): wsgi request

        Returns:
            JsonResponse: Response
        """
        try:
            token = utils.get_token(request.headers)
        except Exception as e:
            return JsonResponse(data={"error": "Invalid token"}, status=403)
        self.send_alert(token, request.data)
        return JsonResponse(data={}, status=200)
