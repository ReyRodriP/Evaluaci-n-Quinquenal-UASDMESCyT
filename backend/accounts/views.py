from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
from rest_framework.response import Response
from .serializers import (
    UsuarioSerializer, UsuarioListSerializer, UsuarioPermisosSerializer,
    AdminUsuarioSerializer, GroupSerializer, PermissionSerializer,
    UsuarioProfileSerializer
)
from rest_framework.authtoken.models import Token
from rest_framework import status, viewsets, mixins
from django.shortcuts import get_object_or_404 #Para buscar objeto en la base de dato (buscar usuario)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import Group, Permission
from .permissions import CustomModelPermissions, IsAdminGroup, IsAdminOrReadOnly

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion

User = get_user_model()

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        if not Group.objects.exists():
            default_roles = [
                'Administrador General',
                'Consulta',
                'Responsable Departamental',
                'Revisor Institucional',
                'Coordinador Quinquenal',
                'Evaluador Externo'
            ]
            for role_name in default_roles:
                Group.objects.get_or_create(name=role_name)
        return super().list(request, *args, **kwargs)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, CustomModelPermissions]

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
@authentication_classes([])
@permission_classes([AllowAny])
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
@authentication_classes([])
@permission_classes([AllowAny])
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

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    token = Token.objects.filter(user=request.user).first()
    if token:
        token.delete()
    return Response({"detail": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        serializer = UsuarioProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = UsuarioProfileSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = UsuarioProfileSerializer(request.user, context={'request': request})
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
@authentication_classes([])
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
@authentication_classes([])
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
    
