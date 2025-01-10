import logging
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from decouple import config

from .services import create_comment_and_notify
from .models import Project, Attachment, ProjectComment, ProjectStatus, Category
from .serializers import (
    ProjectSerializer,
    ProjectCreateSerializer,
    AttachmentSerializer,
    ProjectCommentSerializer,
    CategorySerializer
)

logger = logging.getLogger('app')


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'category__name': ['icontains'],
        'budget': ['gte', 'lte'],
    }
    search_fields = ['title', 'description', 'sender_name']
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
        """
        Creates a new project and sends an email to the contact email.
        """
        project = serializer.save()
        logger.info(f"Project '{project.title}' created by {project.sender_name}.")

        # Send a "thank you" email to the user creating the project
        send_mail(
            subject='Thank you for your project proposal',
            message=f"We received your proposal '{project.title}'. Our team will review it soon.",
            from_email=config('EMAIL_HOST_USER'),  # or your default from email
            recipient_list=[project.contact_email],
            fail_silently=False
        )

    @action(detail=True, methods=['post'], url_path='accept')
    def accept_project(self, request, pk=None):
        """
        Marks the project as ACCEPTED, creates a comment, and sends an email.
        """
        project = get_object_or_404(Project, pk=pk)
        project.status = ProjectStatus.ACCEPTED
        project.save(update_fields=['status'])

        # Check if the request has a custom 'comment_text'
        comment_text = request.data.get(
            'comment_text',
            f"Project '{project.title}' was accepted."  # default if none provided
        )

        # Use the centralized function to handle comment creation & email.
        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject='Project Accepted'
        )

        return Response({
            'detail': 'Project accepted',
            'status': project.status,
            'comment_text': comment_text
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_project(self, request, pk=None):
        """
        Marks the project as REJECTED, creates a comment, and sends an email.
        """
        project = get_object_or_404(Project, pk=pk)
        project.status = ProjectStatus.REJECTED
        project.save(update_fields=['status'])

        comment_text = request.data.get(
            'comment_text',
            f"Project '{project.title}' was rejected."
        )

        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject='Project Rejected'
        )

        return Response({
            'detail': 'Project rejected',
            'status': project.status,
            'comment_text': comment_text
        })


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
        """
        Creates a new comment for a project, then sends an email notification.
        """
        validated_data = serializer.validated_data
        project = validated_data['project']
        comment_text = validated_data['comment_text']
        author_name = validated_data.get('author_name', 'Anonymous')

        # Create comment & send email using the helper function
        comment = create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=author_name,
            email_subject='New Comment'
        )

        # Ensure DRF knows which instance was created
        serializer.instance = comment


class AttachmentDownloadView(APIView):
    """
    Class-based view to force-download a Cloudinary file by inserting
    the 'fl_attachment' parameter into the URL.
    """
    permission_classes = [AllowAny]

    def get(self, request, attachment_id):
        attachment = get_object_or_404(Attachment, pk=attachment_id)

        # Original Cloudinary URL
        original_url = attachment.file.url
        forced_download_url = original_url.replace("/upload/", "/upload/fl_attachment/")

        # (Optional) If the path is "/raw/upload/", do the same replacement.
        forced_download_url = forced_download_url.replace("/raw/upload/", "/raw/upload/fl_attachment/")

        # Redirect to the forced download URL
        return redirect(forced_download_url)


class CategoryListView(APIView):
    """
    View to list all available categories.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        logger.info("Categories list retrieved.")
        return Response(serializer.data)
