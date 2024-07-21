from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from splitEase.models import Group, Membership, Transaction, User

from .helpers import calculate_optimal_settlement, create_memberships, group_balance
from .permissions import IsGroupMember
from .serializers import GroupSerializer, TransactionSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=["get"], url_path="user_groups")
    def get_user_groups(self, request):
        user = self.request.headers.get("User-Email")
        if not user:
            return Response({"message": "No user provided in the request headers"}, status=status.HTTP_400_BAD_REQUEST)

        # Get all memberships for the user
        memberships = Membership.objects.filter(user__email=user, is_deleted=False)

        # Create a list of dictionaries containing group name and join time
        user_groups = []
        for membership in memberships:
            user_groups.append({"group_name": membership.group.name, "join_time": membership.created_at})

        return Response(user_groups, status=status.HTTP_200_OK)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsGroupMember]

    @action(detail=True, methods=["delete"])
    def delete_group(self, request, pk=None):
        try:
            group = self.get_object()
            group.is_deleted = True
            group.save()
            Membership.objects.filter(group=group).update(is_deleted=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            group = serializer.save()
            Membership.objects.create(group=group, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        try:
            group = self.get_object()
            user_to_add_email = request.data.get("email")

            user_to_add, _ = User.objects.get_or_create(email=user_to_add_email)

            # Check if the user is already a member of the group and is deleted
            membership, _ = Membership.objects.get_or_create(user=user_to_add, group=group)
            if membership.is_deleted:
                membership.is_deleted = False
                membership.save()
            return Response(
                {"message": f"User {user_to_add_email} added to the group."}, status=status.HTTP_201_CREATED
            )
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["delete"])
    def remove_member(self, request, pk=None):
        try:
            group = self.get_object()
            user_to_remove_email = request.data.get("email")

            # Check if the user to remove exists
            try:
                user_to_remove = User.objects.get(email=user_to_remove_email)
            except User.DoesNotExist:
                return Response(
                    {"message": f"User {user_to_remove_email} does not exist."}, status=status.HTTP_404_NOT_FOUND
                )

            # Check if the user to remove is a member of the group
            membership = Membership.objects.filter(group=group, user=user_to_remove, is_deleted=False)
            if not membership:
                return Response(
                    {"message": f"User {user_to_remove_email} is not a member of this group."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Remove the user from the group
            membership.update(is_deleted=True)
            # Check if all members are deleted, and if so, mark the group as deleted
            if not Membership.objects.filter(group=group, is_deleted=False).exists():
                group.is_deleted = True
                group.save()
            return Response(
                {"message": f"User {user_to_remove_email} removed from the group."}, status=status.HTTP_204_NO_CONTENT
            )
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def list_members(self, request, pk=None):
        try:
            group = self.get_object()

            # Get the list of members in the group
            members = Membership.objects.filter(group=group, is_deleted=False)
            member_data = [
                {"id": member.user.id, "name": member.user.name, "email": member.user.email} for member in members
            ]

            return Response(member_data, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"])
    def add_transaction(self, request, pk=None):
        try:
            group = self.get_object()
            serializer = TransactionSerializer(data=request.data)

            if serializer.is_valid():
                transaction_data = serializer.validated_data
                paid_by_users = transaction_data["paid_by"]["users"]
                shared_by_users = transaction_data["shared_by"]["users"]

                # Ensure all users in paid_by and shared_by have group membership
                all_user_emails = set(paid_by_users + shared_by_users)
                create_memberships(all_user_emails, group)
                # Create a new transaction using the validated data
                transaction = Transaction(
                    name=transaction_data["name"],
                    amount=transaction_data["amount"],
                    paid_by=transaction_data["paid_by"],
                    shared_by=transaction_data["shared_by"],
                    added_by=request.user,
                    group=group,
                )
                transaction.save()

                return Response(
                    {"message": "Transaction created successfully.", "transaction_id": transaction.id},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def list_transactions(self, request, pk=None):
        try:
            group = self.get_object()
            transactions = Transaction.objects.filter(group=group, is_deleted=False)

            transaction_data = []
            for transaction in transactions:
                transaction_data.append(
                    {
                        "id": transaction.id,
                        "name": transaction.name,
                        "amount": transaction.amount,
                        "paid_by": transaction.paid_by,
                        "shared_by": transaction.shared_by,
                        "added_by": transaction.added_by.email,
                    }
                )

            return Response(transaction_data, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["put"])
    def update_transaction(self, request, pk=None):
        try:
            group = self.get_object()
            transaction_id = request.data.get("transaction_id")
            serializer = TransactionSerializer(data=request.data)

            if serializer.is_valid():
                try:
                    transaction_data = serializer.validated_data
                    paid_by_users = transaction_data["paid_by"]["users"]
                    shared_by_users = transaction_data["shared_by"]["users"]

                    # Ensure all users in paid_by and shared_by have group membership
                    all_user_emails = set(paid_by_users + shared_by_users)
                    create_memberships(all_user_emails, group)

                    transaction = Transaction.objects.get(id=transaction_id, group=group)
                    transaction.name = transaction_data["name"]
                    transaction.amount = transaction_data["amount"]
                    transaction.paid_by = transaction_data["paid_by"]
                    transaction.shared_by = transaction_data["shared_by"]
                    transaction.added_by = request.user
                    transaction.save()

                    return Response({"message": "Transaction updated successfully."}, status=status.HTTP_200_OK)
                except Transaction.DoesNotExist:
                    return Response(
                        {"message": "Transaction not found in this group."}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["delete"])
    def delete_transaction(self, request, pk=None):
        try:
            group = self.get_object()
            transaction_id = request.data.get("transaction_id")

            try:
                transaction = Transaction.objects.get(id=transaction_id, group=group)

                # Soft delete the transaction by setting is_deleted=True
                transaction.is_deleted = True
                transaction.save()

                return Response({"message": "Transaction deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
            except Transaction.DoesNotExist:
                return Response({"message": "Transaction not found in this group."}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def list_balances(self, request, pk=None):
        try:
            group = self.get_object()
            balance_data = group_balance(group)
            if not balance_data:
                # No transactions, return the names of all users with 0 balance
                members = Membership.objects.filter(group=group, is_deleted=False)
                user_balance_mapping = [
                    {"user_id": member.user.id, "user_email": member.user.email, "balance": 0} for member in members
                ]
                return Response(user_balance_mapping, status=status.HTTP_200_OK)
            return Response(balance_data, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def calculate_settlement(self, request, pk=None):
        try:
            group = self.get_object()

            # Calculate the optimal settlement transactions
            settlement_transactions = calculate_optimal_settlement(group)

            return Response(settlement_transactions, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({"message": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
