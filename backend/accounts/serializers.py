"""
@file serializers.py
@brief Serializers para la serializacion y deserializacion de datos de usuario
@details Define serializers para el modelo Usuario, grupo, permisos y perfil,
incluyendo validacion de creacion y actualizacion de usuarios.
Implementa validaciones de seguridad para campos sensibles.
"""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.validators import validate_email
from rest_framework import serializers

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    """
    @class PermissionSerializer
    @brief Serializer para el modelo Permission de Django
    @details Serializa id, nombre, codename, content_type y app_label de permisos.
    """

    app_label = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type", "app_label"]

    def get_app_label(self, obj):
        """
        @brief Obtiene el app_label del content_type del permiso
        @param obj Instancia del modelo Permission
        @return String con el nombre de la app
        """
        return obj.content_type.app_label


class GroupSerializer(serializers.ModelSerializer):
    """
    @class GroupSerializer
    @brief Serializer para el modelo Group de Django
    @details Serializa id, nombre, permisos (lectura) y IDs de permisos (escritura).
    """

    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Permission.objects.all(), source="permissions", required=False
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions", "permission_ids"]


class UsuarioSerializer(serializers.ModelSerializer):
    """
    @class UsuarioSerializer
    @brief Serializer para creacion y lectura de usuarios
    @details Serializa datos basicos del usuario incluyendo grupos, rol y foto de perfil.
    El password es write_only para no exponerlo en respuestas.
    Implementa validaciones de seguridad para campos sensibles.
    """

    groups = GroupSerializer(many=True, read_only=True)
    rol = serializers.SerializerMethodField()
    foto_perfil = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "telefono",
            "foto_perfil",
            "is_active",
            "rol",
            "groups",
        ]

        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "email": {"required": True},
        }

    def validate_username(self, value):
        """
        @brief Valida que el username solo contenga caracteres seguros
        @param value Valor del username a validar
        @return Username validado
        @raises ValidationError Si el username contiene caracteres no permitidos
        """
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise serializers.ValidationError(
                "El nombre de usuario solo puede contener letras, numeros y guiones bajos."
            )
        if len(value) < 3:
            raise serializers.ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
        return value

    def validate_email(self, value):
        """
        @brief Valida el formato del correo electronico
        @param value Valor del email a validar
        @return Email validado
        @raises ValidationError Si el formato del email es invalido
        """
        validate_email(value)
        return value.lower()

    def validate_password(self, value):
        """
        @brief Valida la fortaleza de la contrasena
        @param value Valor de la contrasena a validar
        @return Contrasena validada
        @raises ValidationError Si la contrasena no cumple requisitos de seguridad
        """
        if len(value) < 8:
            raise serializers.ValidationError("La contrasena debe tener al menos 8 caracteres.")
        if value.isdigit():
            raise serializers.ValidationError("La contrasena no puede ser solo numeros.")
        return value

    def validate_telefono(self, value):
        """
        @brief Valida el formato del telefono
        @param value Valor del telefono a validar
        @return Telefono validado
        @raises ValidationError Si el telefono contiene caracteres no permitidos
        """
        if value and not re.match(r"^[\d\-\+\(\)\s]+$", value):
            raise serializers.ValidationError("El telefono solo puede contener numeros, espacios y guiones.")
        if value and len(value.replace(" ", "").replace("-", "")) < 8:
            raise serializers.ValidationError("El telefono debe tener al menos 8 digitos.")
        return value

    def get_rol(self, obj):
        """
        @brief Obtiene el nombre del primer grupo del usuario como rol
        @param obj Instancia del modelo User
        @return String con el nombre del rol o None
        """
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def create(self, validated_data):
        """
        @brief Crea un nuevo usuario con los datos validados
        @param validated_data Diccionario con los datos validados del usuario
        @return Instancia del usuario creado
        @details Utiliza create_user para hashear la contrasena correctamente.
        """
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            telefono=validated_data.get("telefono", ""),
            foto_perfil=validated_data.get("foto_perfil"),
        )
        return user


class UsuarioProfileSerializer(serializers.ModelSerializer):
    """
    @class UsuarioProfileSerializer
    @brief Serializer para el perfil completo del usuario autenticado
    @details Incluye grupos, rol, permisos y foto de perfil con URL absoluta.
    Utilizado para vistas de perfil y datos del usuario logueado.
    """

    foto_perfil = serializers.ImageField(required=False, allow_null=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)
    rol = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telefono",
            "foto_perfil",
            "is_superuser",
            "groups",
            "rol",
            "permisos",
        ]
        read_only_fields = ["id", "username", "is_superuser"]

    def get_rol(self, obj):
        """
        @brief Obtiene el nombre del primer grupo del usuario como rol
        @param obj Instancia del modelo User
        @return String con el nombre del rol o None
        """
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def get_permisos(self, obj):
        """
        @brief Obtiene la lista ordenada de todos los permisos del usuario
        @param obj Instancia del modelo User
        @return Lista de strings con los permisos del usuario
        """
        return sorted(obj.get_all_permissions())

    def to_representation(self, instance):
        """
        @brief Convierte la instancia del usuario a representacion serializada
        @param instance Instancia del modelo User
        @return Diccionario con los datos serializados, incluyendo URL absoluta de foto
        @details Construye la URL absoluta de la foto de perfil si existe,
        o retorna None si no tiene foto.
        """
        data = super().to_representation(instance)
        if instance.foto_perfil:
            request = self.context.get("request")
            if request is not None:
                data["foto_perfil"] = request.build_absolute_uri(instance.foto_perfil.url)
            else:
                data["foto_perfil"] = instance.foto_perfil.url
        else:
            data["foto_perfil"] = None
        return data


class UsuarioPermisosSerializer(serializers.ModelSerializer):
    """
    @class UsuarioPermisosSerializer
    @brief Serializer para consultar permisos de un usuario
    @details Serializa id, username, rol y lista de permisos del usuario.
    """

    rol = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "rol", "permisos"]

    def get_rol(self, obj):
        """
        @brief Obtiene el nombre del primer grupo del usuario como rol
        @param obj Instancia del modelo User
        @return String con el nombre del rol o None
        """
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def get_permisos(self, obj):
        """
        @brief Obtiene la lista ordenada de todos los permisos del usuario
        @param obj Instancia del modelo User
        @return Lista de strings con los permisos del usuario
        """
        return sorted(obj.get_all_permissions())


class AdminUsuarioSerializer(UsuarioSerializer):
    """
    @class AdminUsuarioSerializer
    @brief Serializer para administracion de usuarios con asignacion de grupos
    @details Extiende UsuarioSerializer agregando group_ids para asignar grupos
    al crear o actualizar usuarios desde el panel de administracion.
    """

    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Group.objects.all(), source="groups", required=False
    )

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ["group_ids"]

    def create(self, validated_data):
        """
        @brief Crea un usuario con grupos asignados
        @param validated_data Diccionario con datos validados incluyendo groups
        @return Instancia del usuario creado con grupos asignados
        @details Extrae groups y password antes de crear el usuario,
        luego asigna los grupos si se proporcionaron.
        """
        groups = validated_data.pop("groups", None)
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        if groups is not None:
            user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        """
        @brief Actualiza un usuario con grupos asignados
        @param instance Instancia del usuario a actualizar
        @param validated_data Diccionario con datos validados incluyendo groups
        @return Instancia del usuario actualizado
        @details Extrae groups y password antes de actualizar,
        luego asigna los grupos si se proporcionaron.
        """
        groups = validated_data.pop("groups", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance


class UsuarioListSerializer(serializers.ModelSerializer):
    """
    @class UsuarioListSerializer
    @brief Serializer ligero para listado de usuarios
    @details Serializa campos esenciales para la vista de lista:
    id, username, email, nombre, apellido, telefono, foto, estado activo y rol.
    """

    rol = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "telefono", "foto_perfil", "is_active", "rol"]

    def get_rol(self, obj):
        """
        @brief Obtiene el nombre del primer grupo del usuario como rol
        @param obj Instancia del modelo User
        @return String con el nombre del rol o None
        """
        groups = obj.groups.all()
        return groups.first().name if groups else None
