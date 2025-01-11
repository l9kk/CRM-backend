from decouple import config
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project, Attachment, ProjectComment, ProjectStatus, Category, ApplicationLog
from .serializers import (
    ProjectSerializer,
    ProjectCreateSerializer,
    AttachmentSerializer,
    ProjectCommentSerializer,
    CategorySerializer
)
from .services import create_comment_and_notify


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
        # Save log to ApplicationLog
        ApplicationLog.objects.create(
            level="INFO",
            message=f"Project '{project.title}' created by {project.sender_name}.",
            logger_name="ProjectViewSet.perform_create"
        )

        # Send a "thank you" email to the user creating the project
        send_mail(
            subject='Thank you for your project proposal',
            message=f"We received your proposal '{project.title}'. Our team will review it soon.",
            from_email=config('EMAIL_HOST_USER'),
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

        comment_text = request.data.get(
            'comment_text',
            f"Project '{project.title}' was accepted."
        )

        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject='Project Accepted'
        )

        ApplicationLog.objects.create(
            level="INFO",
            message=f"Project '{project.title}' accepted by {request.user.username}.",
            logger_name="ProjectViewSet.accept_project"
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

        ApplicationLog.objects.create(
            level="INFO",
            message=f"Project '{project.title}' rejected by {request.user.username}.",
            logger_name="ProjectViewSet.reject_project"
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
        ApplicationLog.objects.create(
            level="INFO",
            message=f"Attachment '{attachment.file.name}' uploaded for project '{attachment.project.title}'.",
            logger_name="AttachmentViewSet.perform_create"
        )


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

        comment = create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=author_name,
            email_subject='New Comment'
        )

        ApplicationLog.objects.create(
            level="INFO",
            message=f"Comment added to project '{project.title}' by {author_name}.",
            logger_name="ProjectCommentViewSet.perform_create"
        )

        serializer.instance = comment


class AttachmentDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, attachment_id):
        attachment = get_object_or_404(Attachment, pk=attachment_id)
        original_url = attachment.file.url
        forced_download_url = original_url.replace("/upload/", "/upload/fl_attachment/")
        forced_download_url = forced_download_url.replace("/raw/upload/", "/raw/upload/fl_attachment/")
        ApplicationLog.objects.create(
            level="INFO",
            message=f"Attachment '{attachment.file.name}' viewed by {request.user.username}.",
            logger_name="AttachmentDownloadView.get"
        )
        return redirect(forced_download_url)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        ApplicationLog.objects.create(
            level="INFO",
            message="Categories list retrieved.",
            logger_name="CategoryListView.get"
        )
        return Response(serializer.data)