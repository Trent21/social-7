from rest_framework.response import Response
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from newsfeed.models import Post
from newsfeed.serializer import GroupPostSerializer
from notification.views import NotificationViewList
from models import *
from serializers import *
from django.http import Http404
from rest_framework import status
from rest_framework.renderers import JSONRenderer
import json


class MemberViewSet(ListCreateAPIView):
    """This class is an API for managing member in group.
    """
    serializer_class = GroupMemberSerializer

    def get_group_id(self):
        """Get the id of the current group.
        Args:

        Return:
            Id of the current group.
        """
        try:
            return int(self.kwargs['group_id'])
        except ValueError:
            return ValidationError('group id cannot be parsed')

    def get_queryset(self):
        """Get all members in the current group.
        Args:

        Return:
            Query all member in the current group.
        """
        this_group = Group.objects.get(id=self.get_group_id)
        return GroupMember.objects.filter(group=this_group)

    def create(self, *args, **kwargs):
        """create a new member to group.
        Args:

        Return:
            A response containing data of a group.
        """
        notification = NotificationViewList()
        if not self.request.user.is_authenticated():
            raise NotAuthenticated
        try:
            group = Group.objects.get(id=self.get_group_id())
        except Group.DoesNotExist:
            raise NotFound('no such group')
        member, created = GroupMember.objects.get_or_create(
            group=Group.objects.get(id=self.get_group_id),
            user=User.objects.get(id=self.request.user.id),
            defaults={
                'role': 0
            }
        )
        data_json = {}
        data = {}
        data_json['target_id'] = self.get_group_id()
        data_json['target_type'] = ContentType.objects.get(
            model='group', app_label='group').id
        data_json['text'] = 'requested to join a group'
        data['type'] = 'group'
        data['action'] = 'request'
        data['group_id'] = self.get_group_id()
        data['group_name'] = group.name
        json_data = json.dumps(data)
        notification.add(
            self.request.user,
            data_json,
            User.objects.filter(
                id__in=GroupMember.objects.values(
                    'user'
                ).filter(group_id=self.get_group_id(), role=2)),
            ContentType.objects.get(model='groupmember'),
            json.dumps({}),
            json_data
        )

        if not created:
            raise ValidationError('request already exists')
        return Response(GroupMemberSerializer(member).data)


class PendingMemberViewSet(ListCreateAPIView):
    """This class is an API for getting the list of pending member.
    """
    serializer_class = GroupMemberSerializer

    def get_queryset(self):
        """Get list of pending member from database.
        Args:

        Return:
                List of pending member.
        """
        this_group = Group.objects.get(id=int(self.kwargs['group_id']))
        return GroupMember.objects.filter(group=this_group, role=0)


class AcceptedMemberViewSet(ListCreateAPIView):
    """This class is an API for getting the list of pending member.
    """
    serializer_class = GroupMemberSerializer

    def get_queryset(self):
        """Get list of accepted member from database.
        Args:

        Return:
                List of accepted member.
        """
        this_group = Group.objects.get(id=int(self.kwargs['group_id']))
        return GroupMember.objects.filter(group=this_group, role__gte=1)


class GroupViewSet(APIView):
    """This class is an API for managing a set of group.
    """
    serializer_class = GroupSerializer

    def get(self, request, id=None, format=None):
        """Get list of all group from database.
        Args:

        Return:
                List of group.
        """
        group = Group.objects.all()
        response = self.serializer_class(group, many=True)

        return Response(response.data)

    def post(self, request, format=None):
        """create a new group to database.
        Args:
                request: Django Rest Framework request object
                format: pattern for Web APIs
        Return:
            A response containing data of a group.
        """
        serializer = GroupSerializer(data=request.data)

        if serializer.is_valid():
            # serializer.user = self.request.user
            serializer.save(group=Group.objects.get(id=self.request.group.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupViewDetail(APIView):
    """This class is an API for managing one group.
    """
    serializer_class = GroupSerializer

    def get_group(self, group_id):
        """Get one group from the database.
        Args:
                group_id: id of the query group
        Return:
                Query group.
        """

        try:
            return Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise Http404

    def get(self, request, group_id=None, format=None):
        """.GET function for sending the request group to the frontend
        Args:
                request: Django Rest Framework request object
                group_id: id of the query group
                format: pattern for Web APIs

        Return:
                Query group.
        """
        group_object = self.get_group(group_id)

        if request.user.is_authenticated():
            group_object.member_status = -1

            try:
                member_status = group_object.groupmember_set.filter(
                    user=request.user).get()
                group_object.member_status = member_status.role
            except GroupMember.DoesNotExist:
                pass

        response = self.serializer_class(group_object)
        return Response(response.data)

    def post(self, request, group_id, format=None):
        """create a new group to database.
        Args:
                request: Django Rest Framework request object
                format: pattern for Web APIs
        Return:

        """
        serializer = GroupSerializer(data=request.data)

        if serializer.is_valid():
            # serializer.user = self.request.user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCover (APIView):
    """This class is an API for managing one group.
    """
    serializer_class = GroupCoverSerializer

    def get(self, request, group_id=None, format=None):
        """.GET function for sending the request group to the frontend
        Args:
                request: Django Rest Framework request object
                group_id: id of the query group
                format: pattern for Web APIs

        Return:
                Query group.
        """
        group_object = Group.objects.get(id=group_id)
        response = self.serializer_class(group_object)
        return Response(response.data.get('cover'))

    def put(self, request, group_id, format=None):
        """Update the group cover image.
        Args:
                request: Django Rest Framework request object
                group_id: A number identification for group
                format: pattern for Web APIs
        Return:

        """
        group_object = Group.objects.get(id=group_id)
        serializer = GroupCoverSerializer(group_object, data=request.data)
        if serializer.is_valid():
            if 'cover' in self.request.FILES:
                serializer.data.cover = self.request.FILES.get('cover')
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemberDetail(APIView):
    """This class is an API for managing member in group.
    """
    serializer_class = GroupMemberSerializer

    def get_member(self, group_id, user_id):
        """Get user from group's database.
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                format: pattern for Web APIs
        Return:
        """
        try:
            return GroupMember.objects.get(group=group_id, user=user_id)
        except GroupMember.DoesNotExist:
            raise Http404

    def post(self, request, group_id, pk, format=None):
        """change user status from group.
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                pk: ID of user
                format: pattern for Web APIs
        Return:
        """
        try:
            member = self.get_member(group_id, pk)
            member.role = request.data.get('role')
            member.save()
            response = self.serializer_class(member)
        except Exception as inst:
            print type(inst)     # the exception instance
            print inst           # __str__ allows args to be printed directly
            raise Http404
        return Response(response.data)

    def delete(self, request, group_id, pk, format=None):
        """Delete user from group.
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                pk: ID of user
                format: pattern for Web APIs
        Return:
        """
        member = self.get_member(group_id, pk)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, group_id, pk, format=None):
        """Add or update member in group.
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                pk: ID of user
                format: pattern for Web APIs
        Return:
        """
        notification = NotificationViewList()

        member = self.get_member(group_id, pk)
        member.role = 1
        member.save()

        data_json = {}
        data = {}
        data_json['target_id'] = group_id
        data_json['target_type'] = ContentType.objects.get(
            model='group', app_label='group').id
        data_json['text'] = 'approved your request to join the group'
        data['type'] = 'group'
        data['action'] = 'approve'
        data['group_id'] = group_id
        data['group_name'] = Group.objects.get(id=group_id).name
        json_data = json.dumps(data)
        notification.add(
            request.user,
            data_json,
            User.objects.filter(id=pk),
            ContentType.objects.get(model='groupmember'),
            json.dumps({}),
            json_data
        )

        return Response(status=status.HTTP_201_CREATED)

    def get(self, request, group_id, pk, format=None):
        """Sending data of member in group from server to client.
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                pk: ID of user
                format: pattern for Web APIs
        Return:
        """
        group_member_object = self.get_member(group_id, pk)
        response = self.serializer_class(group_member_object)
        return Response(response.data)


class EditInfo(APIView):
    """This class is an API for editing information in the group.
    """
    serializer_class = GroupSerializer

    def put(self, request, group_id, format=None):
        """Edit or add information in the group.
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                format: pattern for Web APIs
        Return:
        """
        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group, data=request.data)
        print "not valid"
        if serializer.is_valid():
            print "valid"
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupByCategory(APIView):
    """This class an API for query groups by its category.
    """

    serializer_class = GroupSerializer

    def get(self, request, cat, format=None):
        """Get a list of group with the same category selected.
        Args:
                request: Django Rest Framework request object.
                cat: category of groups.
                format: pattern for Web APIs.
        Return:
                List of group with same category.
        """
        try:
            cate = GroupCategory.objects.get(name=cat)
        except GroupCategory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        groups = Group.objects.filter(category=cate.id)
        for g in groups:
            g.member_count = len(GroupMember.objects.filter(group=g))
        response = self.serializer_class(groups, many=True)
        return Response(response.data)


class AllCategory(APIView):
    """This class an API for querying list of all category in the database.



    """
    serializer_class = GroupCategorySerializer

    def get(self, request, format=None):
        """Get a list of all category.
        Args:
                request: Django Rest Framework request object.
                format: pattern for Web APIs.
        Return:
                List of all category.
        """
        category = GroupCategory.objects.all()
        response = self.serializer_class(category, many=True)
        return Response(response.data)


class GroupPostView(APIView):
    """This class an API for managing group post.

    """
    serializer_class = GroupPostSerializer

    def get(self, request, group_id, limit=20, format=None):
        """Get a post from database.
        Args:
                request: Django Rest Framework request object.
                group_id: group id of querying post.
                format: pattern for Web APIs.
        Return:
                post from querying group.
        """
        post = Post.objects.filter(
            target_id=group_id,
            target_type=ContentType.objects.get(
                model='group', app_label='group'
            )).order_by('-pinned', '-datetime')[:limit]
        response = self.serializer_class(post, many=True)
        return Response(response.data)

    def post(self, request, group_id, format=None):
        """Create new post to the system.
        Args:
                request: Django Rest Framework request object.
                group_id: group id that we going to post to.
                format: pattern for Web APIs.
        Return:

        """
        serializer = GroupPostSerializer(data=request.data)
        notification = NotificationViewList()
        parent_id = None
        if Group.objects.get(id=group_id).parent is not None:
            parent_id = Group.objects.get(id=group_id).parent.id
        if serializer.is_valid():
            if self.request.user.id in GroupMember.objects.filter(
                group_id__in=[group_id, parent_id],
                role__gt=0
            ).values_list('user_id', flat=True):
                if self.request.user.is_authenticated():
                    request.data['target_type'] = ContentType.objects.get(
                        model='group', app_label='group').id
                    request.data['target_id'] = group_id
                    target = Group.objects.get(id=request.data['target_id'])
                    serializer.save(
                        user=User.objects.get(
                            id=self.request.user.id),
                        target_id=group_id,
                        target_type=ContentType.objects.get(
                            model='group', app_label='group'),
                        target_name=target.name
                    )
                    data = {}
                    data['type'] = 'group'
                    data['group_id'] = group_id
                    data['group_name'] = Group.objects.get(id=group_id).name
                    json_data = json.dumps(data)
                    notification.add(
                        request.user,
                        request.data,
                        User.objects.filter(
                            id__in=GroupMember.objects.values(
                                'user'
                            ).filter(group_id=group_id)),
                        ContentType.objects.get(model='post'),
                        JSONRenderer().render(serializer.data), json_data
                    )
                    return Response(
                        serializer.data, status=status.HTTP_201_CREATED
                    )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateGroup(APIView):
    """This class is an API for creating new group.
    """

    serializer_class = GroupSerializer

    def post(self, request, format=None):
        """Create new group
        Args:
                request: Django Rest Framework request object.
                format: pattern for Web APIs.
        Return:
        """

        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.user = self.request.user
            this_group = serializer.save()
            GroupMember.objects.create(
                group=this_group,
                user=request.user,
                role=2
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupList(ListAPIView):
    """List groups that the requesting user is member of
    It could be accessed at :http:get:`/api/group`"""
    serializer_class = GroupSerializer

    def get_queryset(self):
        """Get a list of group that requesting user is a member.
        Args:

        Return:
                list of group that requesting user is a member.
        """
        if not self.request.user.is_authenticated():
            raise NotAuthenticated

        return Group.objects.filter(
            groupmember__user=self.request.user,
            groupmember__role__gte=1
        )


class SubGroupViewSet(APIView):
    """This class is api for managing subgroup"""
    serializer_class = SubGroupSerializer

    def get_group(self, group_id):
        """Get one group from the database.
        Args:
                group_id: id of the query group
        Return:
                Query group.
        """
        return Group.objects.get(id=group_id)

    def get(self, request, group_parent_id, format=None):
        """Get subgroup of the requesting parent group
        Args:
                request: Django Rest Framework request object
                group_parent_id: ID of parent group
                format: pattern for Web APIs
        Return:
            Requesting Subgroup
        """
        parent_group = self.get_group(group_parent_id)
        try:
            sub_group = Group.objects.filter(parent=parent_group)
            response = self.serializer_class(sub_group, many=True)
        except Exception as inst:
            print type(inst)     # the exception instance
            print inst           # __str__ allows args to be printed directly
            raise Http404
        return Response(response.data)

    def post(self, request, group_parent_id, format=None):
        """Create subgroup of the requesting parent group
        Args:
                request: Django Rest Framework request object
                group_parent_id: ID of parent group
                format: pattern for Web APIs
        Return:
        """
        parent_group = self.get_group(group_parent_id)
        try:
            sub_group = Group.objects.create(
                name=request.data.get('name'), type=1,
                description="Subgroup of" + parent_group.name,
                short_description="Subgroup of" + parent_group.name,
                activities="somthing",
                parent=parent_group, gtype=parent_group.gtype
            ).save()
            return Response(sub_group)
        except Exception as inst:
            print type(inst)     # the exception instance
            print inst           # __str__ allows args to be printed directly
            raise Http404

    def put(self, request, group_parent_id, format=None):
        """Update subgroup of the requesting parent group
        Args:
                request: Django Rest Framework request object
                group_parent_id: ID of parent group
                format: pattern for Web APIs
        Return:
        """
        parent_group = self.get_group(group_parent_id)
        print request.data.get('group_id')
        try:
            sub_group = Group.objects.get(id=request.data.get('group_id'))
            print sub_group
            print sub_group.parent
            print parent_group
            if sub_group.parent == parent_group:
                sub_group.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as inst:
            print type(inst)     # the exception instance
            print inst           # __str__ allows args to be printed directly
            raise Http404


class GroupPostPegination(APIView):
    """This class is use for updating the group newsfeed"""
    serializer_class = GroupPostSerializer
    group_model_id = ContentType.objects.get(
        model='group',
        app_label='group'
    ).id

    def get(self, request, group_id, action, post_id, limit=20, format=None):
        """Update subgroup of the requesting parent group
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                action: use 'more' to look at older post , use 'new' to request
                new post
                post_id: ID of post
                format: pattern for Web APIs
        Return:
                list of post
        """

        if action == 'more':
            post = Post.objects.filter(
                target_id=group_id,
                target_type=self.group_model_id).filter(
                    id__lt=post_id
            ).order_by('-datetime')[:limit]
        if action == 'new':
            post = Post.objects.filter(
                target_id=group_id,
                target_type=self.group_model_id).filter(
                    id__gt=post_id
            ).order_by('-datetime')
        response = self.serializer_class(post, many=True)
        return Response(response.data)


class PostUnpin(APIView):
    """This class is use for removing the pinned post"""
    serializer_class = GroupPostSerializer

    def post(self, request, group_id, post_id):
        """Use to unpinned requesting post
        Args:
                request: Django Rest Framework request object
                group_id: ID of group
                post_id: ID of post
        Return:
        """
        post = Post.objects.get(id=post_id)
        if post.target_id != int(group_id):
            raise Http404

        post.pinned = False
        post.save()

        return Response(self.serializer_class(post).data)
