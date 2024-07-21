# permissions.py
from rest_framework import permissions

from splitEase.models import Group, Membership, User


class IsGroupMember(permissions.BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user_email = request.headers.get("User-Email")
        # print("headers:", request.headers)
        print("User email from headers:", user_email)

        if not user_email:
            return False  # No email header, permission denied

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return False  # User with this email does not exist, permission denied

        # Set request user to be used later
        request.user = user
        # Extract 'group_id' from the URL kwargs
        group_id = view.kwargs.get("pk")

        # Check if 'group_id' is not None and user is a member of the group
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return False  # Group with this ID does not exist, permission denied

            # Check if user is a member of the group (with is_deleted=False)
            membership = Membership.objects.filter(user=user, group=group, is_deleted=False).first()
            if not membership:
                return False  # User is not a member of the group, permission denied

        return True  # Permission granted
