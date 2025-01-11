from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet,
    AttachmentViewSet,
    ProjectCommentViewSet,
    AttachmentDownloadView, CategoryListView, ApplicationLogView
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'attachments', AttachmentViewSet, basename='attachments')
router.register(r'comments', ProjectCommentViewSet, basename='comments')

urlpatterns = [
    path('', include(router.urls)),
    path('attachments/<int:attachment_id>/download/', AttachmentDownloadView.as_view(), name='attachment_download'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('logs/', ApplicationLogView.as_view(), name='application-logs')
]
