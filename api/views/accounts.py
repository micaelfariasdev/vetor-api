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

# -------------------
# Registro de usuário
# -------------------


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


# -------------------
# Login com JWT via cookies
# -------------------
class CookieTokenObtainPairView(TokenObtainPairView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        data = response.data

        # Cookies HttpOnly
        response.set_cookie(
            key="access",
            value=data["access"],
            secure=False,
            samesite="none",
        )
        response.set_cookie(
            key="refresh",
            value=data["refresh"],
            secure=False,
            samesite="none",
        )

        return response


# -------------------
# Refresh token via cookie
# -------------------
class CookieTokenRefreshView(TokenRefreshView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        request.data["refresh"] = request.COOKIES.get("refresh")
        response = super().post(request, *args, **kwargs)
        data = response.data

        response.set_cookie(
            key="access",
            value=data["access"],
            secure=False,
            samesite="none",
        )
        return response


# -------------------
# Endpoint /me/ 100% JWT
# -------------------
@method_decorator(csrf_exempt, name='dispatch')
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):

        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })


# -------------------
# Logout
# -------------------
@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]  # Adicione esta linha
    # Opcional, mas boa prática para logout
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Logout successful"})
        response.delete_cookie("access", domain="micaelfarias.com")
        response.delete_cookie("refresh", domain="micaelfarias.com")
        return response
