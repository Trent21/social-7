from rest_framework import serializers
from models import *
from User.serializers import UserProfilePictureSerializer

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfilePictureSerializer(read_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'profile')


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = ('user', 'role')

class GroupCategorySerializer(serializers.ModelSerializer):
    class Meta:
        app_label = "group_category"
        model = GroupCategory
        fields = ('id', 'name')

class GroupCoverSerializer(serializers.ModelSerializer):
    class Meta:
        app_label = "social_group"
        model = Group
        fields = ('cover',)

class GroupSerializer(serializers.ModelSerializer):
    member_status = serializers.IntegerField(read_only=True, required=False)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        app_label = "social_group"
        model = Group
        fields = ('id', 'name', 'description', 'short_description',
                  'activities', 'type', 'category', 'member_status',
                  'date', 'member_count', 'cover', 'gtype')
        read_only_fields = ('cover',)
        extra_kwargs = {
            'category': {'required': False}
        }

class SubGroupSerializer(serializers.ModelSerializer):
    class Meta:
        app_label= 'subgroup'
        model = Group
        fields = ('id', 'name')
