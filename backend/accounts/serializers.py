from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 
            'id',
            'username', 
            'email', 
            'password', 
            'first_name', 
            'last_name', 
            'telefono',]
        
        extra_kwargs = {
            'password': {'write_only': True} #Solo se aceptara al entrar datos y lo oculta al hacer get
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telefono=validated_data.get('telefono','')

        )

        return user