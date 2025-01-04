from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, AttachmentViewSet, ProjectCommentViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'attachments', AttachmentViewSet, basename='attachments')
router.register(r'comments', ProjectCommentViewSet, basename='comments')

urlpatterns = [
    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
