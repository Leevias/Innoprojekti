from django.urls import include, path

urlpatterns = [
    path("", include("controller.urls")),
]
