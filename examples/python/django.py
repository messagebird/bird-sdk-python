import json
import os

from bird import APIError, APIStatusError, Bird
from django.http import JsonResponse
from django.views import View

bird = Bird(api_key=os.environ["BIRD_API_KEY"])


class WelcomeView(View):
    def post(self, request):
        data = json.loads(request.body)
        try:
            message = bird.email.send(
                from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
                to=[data["email"]],
                subject="Welcome to Bird",
                html="<p>You are in.</p>",
            )
            return JsonResponse({"sent": True, "id": message.id})
        except APIStatusError as err:
            return JsonResponse({"error": str(err)}, status=err.status_code)
        except APIError as err:
            return JsonResponse({"error": str(err)}, status=500)
