'''Define how to serialize our models.'''
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_bulk import (
    BulkListSerializer,
    BulkSerializerMixin,
)

import auth.models


User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    '''Indicate how to serialize Department instance.'''
    users = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    admins = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = auth.models.Department
        fields = ('id', 'name', 'users', 'admins')

    def get_admins(self, obj):
        '''Get department admin ids.'''
        groups = Group.objects.filter(name=obj.name+'-管理员')
        if groups.exists():
            return [user.first_name for user in groups[0].user_set.all()]
        return []


class PermissionSerializer(serializers.ModelSerializer):
    '''Indicate how to serialize Permission instance.'''
    label = serializers.CharField(source='name')

    class Meta:
        model = Permission
        fields = ('id', 'codename', 'label')


class UserPermissionSerializer(serializers.ModelSerializer):
    '''Indicate how to serialize UserPermission instance.'''

    class Meta:
        model = auth.models.UserPermission
        fields = ('id', 'user', 'permission')


class GroupSerializer(serializers.ModelSerializer):
    '''Indicate how to serialize Group instance.'''

    class Meta:
        model = auth.models.Group
        fields = ('id', 'name',)


class GroupPermissionSerializer(BulkSerializerMixin,
                                serializers.ModelSerializer):
    '''Indicate how to serialize GroupPermission instance.'''

    class Meta:
        model = auth.models.GroupPermission
        fields = ('id', 'group', 'permission')
        list_serializer_class = BulkListSerializer


class UserSerializer(serializers.ModelSerializer):
    '''Indicate how to serialize User instance.'''
    department_str = serializers.CharField(
        source='department.name', read_only=True)
    administrative_department_str = serializers.CharField(
        source='administrative_department.name', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'last_login', 'first_name', 'last_name',
                  'email', 'is_active', 'date_joined', 'user_permissions',
                  'department', 'department_str',
                  'administrative_department', 'administrative_department_str',
                  'is_teacher', 'is_department_admin', 'is_school_admin',
                  'groups')


class UserGroupSerializer(serializers.ModelSerializer):
    '''Indicate how to serialize UserGroup instance.'''
    user_first_name = serializers.CharField(
        source='user.first_name', read_only=True)

    class Meta:
        model = auth.models.UserGroup
        fields = ('id', 'user', 'group', 'user_first_name')
        validators = [
            UniqueTogetherValidator(
                queryset=auth.models.UserGroup.objects.all(),
                fields=['user', 'group']
            )
        ]
