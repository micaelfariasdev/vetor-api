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
from rest_framework import status

from engenharia import models as tb

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
    serializer_class = RegisterSerializer

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })

    def patch(self, request):
        dados = request.data

        try:
            user = request.user
        except User.DoesNotExist:
            return Response(
                {"error": "Usuário não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(user, data=dados, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "message": "Usuário atualizado com sucesso."
            })

        else:
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )


class InfoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        data = {}
        obras = tb.Obras.objects.count()
        funcionarios = tb.Colaborador.objects.count()

        data['obras'] = {'label': 'Obras', 'count': obras}
        data['funcionarios'] = {'label': 'Funcionários', 'count': funcionarios}

        return Response(data)

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
