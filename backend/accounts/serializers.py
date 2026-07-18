from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

User = get_user_model()

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True,
        queryset=Permission.objects.all(),
        source='permissions',
        required=False
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_ids']

class UsuarioSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    rol = serializers.SerializerMethodField()
    foto_perfil = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [ 
            'id',
            'username', 
            'email', 
            'password', 
            'first_name', 
            'last_name', 
            'telefono',
            'foto_perfil',
            'is_active',
            'rol',
            'groups']

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_rol(self, obj):
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telefono=validated_data.get('telefono',''),
            foto_perfil=validated_data.get('foto_perfil')
        )
        return user


class UsuarioProfileSerializer(serializers.ModelSerializer):
    foto_perfil = serializers.ImageField(required=False, allow_null=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)
    rol = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'foto_perfil',
            'groups',
            'rol',
            'permisos',
        ]

    def get_rol(self, obj):
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def get_permisos(self, obj):
        return sorted(obj.get_all_permissions())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.foto_perfil:
            request = self.context.get('request')
            if request is not None:
                data['foto_perfil'] = request.build_absolute_uri(instance.foto_perfil.url)
            else:
                data['foto_perfil'] = instance.foto_perfil.url
        else:
            data['foto_perfil'] = None
        return data


class UsuarioPermisosSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'rol', 'permisos']

    def get_rol(self, obj):
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def get_permisos(self, obj):
        return sorted(obj.get_all_permissions())


class AdminUsuarioSerializer(UsuarioSerializer):
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True,
        queryset=Group.objects.all(),
        source='groups',
        required=False
    )

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ['group_ids']

    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance

class UsuarioListSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telefono', 'foto_perfil', 'is_active', 'rol'
        ]

    def get_rol(self, obj):
        groups = obj.groups.all()
        return groups.first().name if groups else None