from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GroupViewSet, UserViewSet

router = DefaultRouter()
router.register(r"groups", GroupViewSet)
router.register(r"users", UserViewSet, basename="user")


urlpatterns = [
    path("", include(router.urls)),
]
