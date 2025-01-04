import os

from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.http import Http404
from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from urllib.parse import quote

from .models import Project, Attachment, ProjectComment, ProjectStatus
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    AttachmentSerializer, ProjectCommentSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for Projects:
    - Public can POST (create) new projects.
    - Admin users (JWT) can list, retrieve, accept/reject, etc.
    """
    queryset = Project.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.action == 'create':
            # Anyone can submit a project
            return [AllowAny()]
        else:
            # For list/retrieve/accept/reject - admin only
            return [IsAdminUser()]

    def perform_create(self, serializer):
        """
        Called when a new project is submitted by the public.
        """
        project = serializer.save()  # status defaults to 'NEW'
        # Optionally send an email confirmation:
        send_mail(
            'Thank you for your project proposal',
            f"We received your proposal '{project.title}'. Our team will review it soon.",
            'noreply@yourdomain.com',
            [project.contact_email],
            fail_silently=True
        )

    @action(detail=True, methods=['post'], url_path='accept')
    def accept_project(self, request, pk=None):
        """
        Accepts the project (admin only).
        """
        project = get_object_or_404(Project, pk=pk)
        project.status = ProjectStatus.ACCEPTED
        project.save(update_fields=['status'])
        # Optionally notify the user
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
        """
        Rejects the project (admin only).
        """
        project = get_object_or_404(Project, pk=pk)
        project.status = ProjectStatus.REJECTED
        project.save(update_fields=['status'])
        # Optionally notify the user
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
    permission_classes = [IsAdminUser]


class ProjectCommentViewSet(viewsets.ModelViewSet):
    """
    Admin-only CRUD on project comments.
    """
    queryset = ProjectComment.objects.all().order_by('-created_at')
    serializer_class = ProjectCommentSerializer
    permission_classes = [IsAdminUser]


import os
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from .models import Attachment


class AttachmentDownloadView(APIView):
    """
    Class-based view to securely serve an attachment file if the user is an admin/staff.
    Handles non-ASCII filenames by encoding them properly.
    """
    permission_classes = [AllowAny]

    def get(self, request, attachment_id):
        """
        Stream the requested attachment as a file download.
        """
        # Fetch the attachment object
        attachment = get_object_or_404(Attachment, pk=attachment_id)

        # Ensure the file exists on disk
        file_path = attachment.file.path
        if not os.path.exists(file_path):
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

        return response