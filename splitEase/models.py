from django.db import models


class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(BaseModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class Group(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=200, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "groups"

    def __str__(self):
        return f"{self.id} -- {self.name}"


class Membership(BaseModel):
    group = models.ForeignKey("Group", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "memberships"
        unique_together = ("group", "user")

    def __str__(self):
        return f"Group: {self.group.name}, User: {self.user.email}"


class Transaction(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    amount = models.FloatField(blank=False, null=False)
    added_by = models.ForeignKey("User", on_delete=models.CASCADE)
    group = models.ForeignKey("Group", on_delete=models.CASCADE)
    paid_by = models.JSONField()
    shared_by = models.JSONField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "transactions"

    def __str__(self):
        return self.name
