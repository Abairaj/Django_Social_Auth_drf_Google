from django.contrib.auth import get_user_model
from sesame.utils import get_query_string
from rest_framework.views import APIView
from rest_framework.response import Response
class TestView(APIView):
    def get(self,request):
        User = get_user_model()
        user = User.objects.first()
        LOGIN_URL = "http://127.0.0.1:8000/sesame/login/"
        LOGIN_URL += get_query_string(user)
        return Response({'url':LOGIN_URL})