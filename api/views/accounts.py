from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import generics
from django.contrib.auth.models import User
from ..serializer import RegisterSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        data = response.data

        # Cookies HttpOnly para segurança
        response.set_cookie(
            key="access",
            value=data["access"],
            httponly=True,
            secure=True,        # HTTPS obrigatório
            samesite="None",    # crucial para cross-site
            domain="micaelfarias.com"  # domínio que cobre o frontend
        )
        response.set_cookie(
            key="refresh",
            value=data["refresh"],
            httponly=True,
            secure=True,
            samesite="None",
            domain="micaelfarias.com"
        )   
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # pega refresh do cookie
        request.data["refresh"] = request.COOKIES.get("refresh")
        response = super().post(request, *args, **kwargs)
        data = response.data

        # atualiza access
        response.set_cookie(
            key="access",
            value=data["access"],
            httponly=True,
            secure=True,        # HTTPS obrigatório
            samesite="None",    # crucial para cross-site
            domain="micaelfarias.com"  # domínio que cobre o frontend
        )
        return response




@method_decorator(csrf_exempt, name='dispatch')
class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })
