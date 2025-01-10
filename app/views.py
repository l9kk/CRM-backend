import logging
import os
from urllib.parse import quote

from django.core.mail import send_mail
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project, Attachment, ProjectComment, ProjectStatus, Category
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    AttachmentSerializer, ProjectCommentSerializer, CategorySerializer
)

# Configure logger for the app
logger = logging.getLogger('app')


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')

    # Add filter backends for filtering, searching, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Define the fields to filter on
    filterset_fields = {
        'status': ['exact'],  # Filter by exact match on status
        'category__name': ['icontains'],  # Case-insensitive filter on category name
        'budget': ['gte', 'lte'],  # Filter projects by budget range
    }

    # Define fields to enable search
    search_fields = ['title', 'description', 'sender_name']

    # Define fields to enable ordering
    ordering_fields = ['budget', 'created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [AllowAny()]

    def perform_create(self, serializer):
        project = serializer.save()
        logger.info(f"Project '{project.title}' created by {project.sender_name}.")
        send_mail(
            'Thank you for your project proposal',
            f"We received your proposal '{project.title}'. Our team will review it soon.",
            'noreply@yourdomain.com',
            [project.contact_email],
            fail_silently=True
        )

    @action(detail=True, methods=['post'], url_path='accept')
    def accept_project(self, request, pk=None):
        project = get_object_or_404(Project, pk=pk)
        project.status = ProjectStatus.ACCEPTED
        project.save(update_fields=['status'])
        ProjectComment.objects.create(
            project=project,
            comment_text=f"Project '{project.title}' was accepted.",
            author_name=request.user.username
        )
        logger.info(f"Project '{project.title}' accepted by {request.user.username}.")
        send_mail(
            'Project Accepted',
            f"Your project '{project.title}' has been accepted.",
            'noreply@yourdomain.com',
            [project.contact_email],
            fail_silently=True
        )
        return Response({'detail': 'Project accepted', 'status': project.status})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_project(self, request, pk=None):
        project = get_object_or_404(Project, pk=pk)
        project.status = ProjectStatus.REJECTED
        project.save(update_fields=['status'])
        ProjectComment.objects.create(
            project=project,
            comment_text=f"Project '{project.title}' was rejected.",
            author_name=request.user.username
        )
        logger.info(f"Project '{project.title}' rejected by {request.user.username}.")
        send_mail(
            'Project Rejected',
            f"Your project '{project.title}' has been rejected.",
            'noreply@yourdomain.com',
            [project.contact_email],
            fail_silently=True
        )
        return Response({'detail': 'Project rejected', 'status': project.status})

class AttachmentViewSet(viewsets.ModelViewSet):
    """
    Admin-only CRUD on attachments.
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        attachment = serializer.save()
        logger.info(f"Attachment '{attachment.file.name}' uploaded for project '{attachment.project.title}'.")

class ProjectCommentViewSet(viewsets.ModelViewSet):
    """
    Admin-only CRUD on project comments.
    """
    queryset = ProjectComment.objects.all().order_by('-created_at')
    serializer_class = ProjectCommentSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        comment = serializer.save()
        logger.info(f"Comment added to project '{comment.project.title}' by {comment.author_name}.")

class AttachmentDownloadView(APIView):
    """
    Class-based view to securely serve an attachment file if the user is an admin/staff.
    Handles non-ASCII filenames by encoding them properly.
    """
    permission_classes = [AllowAny]

    def get(self, request, attachment_id):
        # Fetch the attachment object
        attachment = get_object_or_404(Attachment, pk=attachment_id)

        # Ensure the file exists on disk
        file_path = attachment.file.path
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise Http404("File not found.")

        # Open the file for streaming
        file_handle = open(file_path, 'rb')

        # Get the original file name
        file_name = os.path.basename(attachment.file.name)

        # Encode the filename for browser compatibility
        encoded_file_name = quote(file_name)

        # Set up the response
        response = FileResponse(file_handle, content_type='application/octet-stream')

        # Set Content-Disposition with UTF-8 encoding for non-ASCII characters
        response['Content-Disposition'] = (
            f"attachment; filename*=UTF-8''{encoded_file_name}"
        )

        logger.info(f"File '{file_name}' downloaded by {request.user.username}.")
        return response

class CategoryListView(APIView):
    """
    View to list all available categories.
    """
    permission_classes = [AllowAny]  # Anyone can access this endpoint

    def get(self, request):
        categories = Category.objects.all()  # Fetch all categories
        serializer = CategorySerializer(categories, many=True)  # Serialize them
        logger.info("Categories list retrieved.")
        return Response(serializer.data)
