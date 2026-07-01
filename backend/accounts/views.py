from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UsuarioSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.shortcuts import get_object_or_404 #Para buscar objeto en la base de dato (buscar usuario)
<<<<<<< HEAD
from rest_framework.permissions import IsAuthenticated, AllowAny
=======
from rest_framework.permissions import IsAuthenticated
>>>>>>> Jose-Manuel
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication

from django.contrib.auth import get_user_model, authenticate #Para obtener el modelo
<<<<<<< HEAD
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

@api_view(['POST'])
@permission_classes([AllowAny])
=======

@api_view(['POST'])
>>>>>>> Jose-Manuel
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
<<<<<<< HEAD
@permission_classes([AllowAny])
=======
>>>>>>> Jose-Manuel
def register(request):
    serializer = UsuarioSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        token = Token.objects.create(user=user)

        return Response({'token': token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

<<<<<<< HEAD
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    token = Token.objects.filter(user=request.user).first()
    if token:
        token.delete()
    return Response({"detail": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)


@api_view(['POST'])
=======
@api_view(['PUT'])
>>>>>>> Jose-Manuel
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request): #Para la actualizacion de datos del usuario a excepcion de username y password

    serializer = UsuarioSerializer(
        request.user,
        data=request.data,
        partial=True #permite actualizar solo los campos enviados
    )

    if serializer.is_valid():
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@authentication_classes([TokenAuthentication])#Confirma si tiene token
@permission_classes([IsAuthenticated]) #Confirma si esta logeado
def me(request):#Funcion para devolver datos de un usuario autenticado

    serializer = UsuarioSerializer(request.user)

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request): #Para cambiar contraseña de usuario

    user = request.user

    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response(
            {"error": "Debe proporcionar ambas contraseñas"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(old_password):
        return Response(
            {"error": "La contraseña actual es incorrecta"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    return Response(
        {"message": "Contraseña actualizada correctamente"},
        status=status.HTTP_200_OK
<<<<<<< HEAD
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = (request.data.get('email') or '').strip()

    if email:
        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()

        if user and user.email:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                f"/reset-password?uid={uid}&token={token}"
            )

            try:
                send_mail(
                    subject='Restablecimiento de contraseña',
                    message=(
                        f'Hola {user.first_name or user.username},\n\n'
                        'Recibimos una solicitud para restablecer tu contraseña. '
                        f'Puedes hacerlo usando este enlace:\n{reset_url}\n\n'
                        'Si no solicitaste este cambio, puedes ignorar este correo.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                # Evitar que un fallo de SMTP haga explotar la petición de recuperación.
                pass

    return Response(
        {"message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña."},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not uid or not token or not new_password:
        return Response(
            {"error": "Debe proporcionar uid, token y nueva contraseña"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
    except (TypeError, ValueError, OverflowError):
        return Response({"error": "Enlace inválido"}, status=status.HTTP_400_BAD_REQUEST)

    user_model = get_user_model()
    try:
        user = user_model.objects.get(pk=user_id)
    except user_model.DoesNotExist:
        return Response({"error": "Enlace inválido"}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "El enlace de recuperación ya no es válido"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({"message": "Contraseña restablecida correctamente"}, status=status.HTTP_200_OK)
=======
    )
>>>>>>> Jose-Manuel
