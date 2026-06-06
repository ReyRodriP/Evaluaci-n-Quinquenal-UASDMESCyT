from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UsuarioSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.shortcuts import get_object_or_404 #Para buscar objeto en la base de dato (buscar usuario)

from django.contrib.auth import get_user_model, authenticate #Para obtener el modelo

@api_view(['POST'])
def login(request):

    user = authenticate(
        username=request.data['username'],
        password=request.data['password']
    ) #Mejorar a futuro, logear con correo

    if user is None:
        return Response(
            {"error": "Credenciales inválidas"},
            status=status.HTTP_400_BAD_REQUEST
        )

    token, created = Token.objects.get_or_create(user=user)

    serializer = UsuarioSerializer(user)

    return Response(
        {
            "token": token.key,
            "user": serializer.data
        },
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
def register(request):
    serializer = UsuarioSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        token = Token.objects.create(user=user)

        return Response({'token': token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def profile(request):
    return Response({})