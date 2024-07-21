from rest_framework import serializers

from splitEase.models import Group, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "email"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class ShareSerializer(serializers.Serializer):
    users = serializers.ListSerializer(child=serializers.CharField())
    share = serializers.ListSerializer(child=serializers.IntegerField())
    type = serializers.ChoiceField(choices=["share", "percentage", "amount"])

    def validate(self, data):
        share = data["share"]
        share_type = data["type"]

        if share_type == "percentage" and sum(share) != 100:
            raise serializers.ValidationError("Share percentages must add up to 100.")

        if len(data["users"]) != len(share):
            raise serializers.ValidationError("'users' and 'share' lists should have the same length.")

        return data


class TransactionSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=100, required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    paid_by = ShareSerializer(required=True)
    shared_by = ShareSerializer(required=True)
