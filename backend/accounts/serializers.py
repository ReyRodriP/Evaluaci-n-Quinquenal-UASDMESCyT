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
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True,
        queryset=Group.objects.all(),
        source='groups',
        required=False
    )
    rol = serializers.SerializerMethodField()

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
            'is_active',
            'rol',
            'groups',
            'group_ids']

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_rol(self, obj):
        groups = obj.groups.all()
        return groups.first().name if groups else None

    def create(self, validated_data):
        groups_data = validated_data.pop('groups', [])
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telefono=validated_data.get('telefono','')
        )
        if groups_data:
            user.groups.set(groups_data)
        return user

class UsuarioListSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telefono', 'is_active', 'rol'
        ]

    def get_rol(self, obj):
        groups = obj.groups.all()
        return groups.first().name if groups else None