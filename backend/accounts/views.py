from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .serializers import (
    UsuarioSerializer, UsuarioListSerializer, UsuarioPermisosSerializer,
    AdminUsuarioSerializer, GroupSerializer, PermissionSerializer,
    PasswordResetRequestSerializer
)
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework import viewsets, mixins
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import Group, Permission
from .permissions import IsAdminGroup

from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion

User = get_user_model()

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminGroup]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminGroup]


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get_serializer_class(self):
        if self.action == 'list':
            return UsuarioListSerializer
        if self.action == 'permisos':
            return UsuarioPermisosSerializer
        if self.action in ['update', 'partial_update']:
            return AdminUsuarioSerializer
        return UsuarioSerializer

    def perform_update(self, serializer):
        old_groups = list(self.get_object().groups.all())
        instance = serializer.save()
        new_groups = list(instance.groups.all())

        registrar_auditoria(
            usuario=self.request.user,
            accion="Modificar usuario",
            modelo="Usuario",
            registro_id=instance.pk,
            descripcion=f"Se modificó el usuario {instance.username}"
        )

        if old_groups != new_groups:
            old_names = [g.name for g in old_groups]
            new_names = [g.name for g in new_groups]
            registrar_auditoria(
                usuario=self.request.user,
                accion="Asignar rol",
                modelo="Usuario",
                registro_id=instance.pk,
                descripcion=(
                    f"Rol del usuario {instance.username} cambió de "
                    f"{old_names or 'sin rol'} a {new_names or 'sin rol'}"
                )
            )
            crear_notificacion(
                usuario=instance,
                titulo="Rol asignado",
                mensaje=f"Se te ha asignado el rol: {', '.join(new_names) if new_names else 'sin rol'}"
            )

    @action(detail=True, methods=['get'])
    def permisos(self, request, pk=None):
        user = self.get_object()
        serializer = UsuarioPermisosSerializer(user)
        return Response(serializer.data)


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

    registrar_auditoria(
        usuario=user,
        accion="Inicio de sesión",
        modelo="Usuario",
        registro_id=user.pk,
        descripcion=f"El usuario {user.username} inició sesión"
    )

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

        registrar_auditoria(
            usuario=user,
            accion="Crear usuario",
            modelo="Usuario",
            registro_id=user.pk,
            descripcion=f"Se registró el usuario {user.username} con email {user.email}"
        )

        return Response({'token': token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
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
    )


@api_view(['POST'])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    user = User.objects.get(email=email)

    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?uidb64={uidb64}&token={token}"

    subject = 'Recuperación de Contraseña - Evaluación Quinquenal UASD-MESCyT'
    html_message = render_to_string('registration/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=None,
        recipient_list=[email],
        fail_silently=False,
    )

    registrar_auditoria(
        usuario=user,
        accion="Solicitud de recuperación de contraseña",
        modelo="Usuario",
        registro_id=user.pk,
        descripcion=f"El usuario {user.username} solicitó recuperación de contraseña"
    )

    return Response(
        {"message": "Se ha enviado un correo con las instrucciones para recuperar tu contraseña."},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def password_reset_confirm(request):
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode

    uidb64 = request.data.get('uidb64')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not uidb64 or not token or not new_password:
        return Response(
            {"error": "Faltan campos requeridos (uidb64, token, new_password)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 6:
        return Response(
            {"error": "La contraseña debe tener al menos 6 caracteres."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"error": "El enlace de recuperación no es válido."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not default_token_generator.check_token(user, token):
        return Response(
            {"error": "El enlace de recuperación ha expirado o no es válido."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    Token.objects.filter(user=user).delete()

    registrar_auditoria(
        usuario=user,
        accion="Restablecer contraseña",
        modelo="Usuario",
        registro_id=user.pk,
        descripcion=f"El usuario {user.username} restableció su contraseña"
    )

    crear_notificacion(
        usuario=user,
        titulo="Contraseña restablecida",
        mensaje="Tu contraseña ha sido restablecida exitosamente."
    )

    return Response(
        {"message": "Contraseña restablecida correctamente."},
        status=status.HTTP_200_OK
    )