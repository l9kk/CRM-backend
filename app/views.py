from decouple import config
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import Project, Attachment, ProjectComment, ProjectStatus, Category, ApplicationLog
from .serializers import (
    ApplicationLogSerializer,
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
        'priority': ['exact'],
        'budget': ['gte', 'lte'],
        'accepted_by': ['exact'],
        'started_by': ['exact'],
        'completed_by': ['exact'],
    }
    search_fields = ['title', 'description', 'sender_name', 'priority']
    ordering_fields = ['budget', 'created_at', 'updated_at', 'priority']

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        """
        Creates a new project and sends an email to the contact email.
        """
        project = serializer.save()
        ApplicationLog.objects.create(
            message=f"Project '{project.title}' with priority '{project.priority}' created by {project.sender_name}.",
            logger_name="Create project",
            interacted_by=project.sender_name
        )
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
        if project.status != ProjectStatus.NEW:
            return Response({'error': 'Only new projects can be accepted.'}, status=400)

        project.status = ProjectStatus.ACCEPTED
        project.accepted_by = request.user
        project.save(update_fields=['status', 'accepted_by'])

        comment_text = request.data.get(
            'comment_text',
            f"Project '{project.title}' was accepted."
        )

        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject=f"Project '{project.title}' Accepted"
        )

        ApplicationLog.objects.create(
            message=f"Project '{project.title}' accepted by {request.user.username}.",
            logger_name="Accept project",
            interacted_by=request.user.username
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
        if project.status != ProjectStatus.NEW:
            return Response({'error': 'Only new projects can be rejected.'}, status=400)

        project.status = ProjectStatus.REJECTED
        project.save(update_fields=['status'])

        comment_text = request.data.get('comment_text', f"Project '{project.title}' was rejected.")
        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject=f"Project '{project.title}' Rejected"
        )

        ApplicationLog.objects.create(
            message=f"Project '{project.title}' rejected by {request.user.username}.",
            logger_name="Reject project",
            interacted_by=request.user.username
        )

        return Response({
            'detail': 'Project rejected',
            'status': project.status,
            'comment_text': comment_text
        })

    @action(detail=True, methods=['post'], url_path='start')
    def start_project(self, request, pk=None):
        """
        Moves the project to IN PROGRESS after it has been ACCEPTED.
        """
        project = get_object_or_404(Project, pk=pk)
        if project.status != ProjectStatus.ACCEPTED:
            return Response({'error': 'Only accepted projects can be started.'}, status=400)

        project.status = ProjectStatus.IN_PROGRESS
        project.started_by = request.user
        project.save(update_fields=['status', 'started_by'])

        comment_text = request.data.get(
            'comment_text',
            f"Project '{project.title}' "
            f"has started."
        )

        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject=f"Project '{project.title}' Started"
        )

        ApplicationLog.objects.create(
            message=f"Project '{project.title}' started by {request.user.username}.",
            logger_name="Start project",
            interacted_by=request.user.username
        )
        return Response({'detail': 'Project started', 'status': project.status, 'comment_text': comment_text})

    @action(detail=True, methods=['post'], url_path='completed')
    def mark_completed(self, request, pk=None):
        """
        Marks the project as COMPLETED, creates a comment, and sends an email.
        """
        project = get_object_or_404(Project, pk=pk)
        if project.status != ProjectStatus.IN_PROGRESS:
            return Response({'error': 'Only projects in progress can be marked as completed.'}, status=400)

        project.status = ProjectStatus.COMPLETED
        project.completed_by = request.user
        project.save(update_fields=['status', 'completed_by'])

        comment_text = request.data.get(
            'comment_text',
            f"Project '{project.title}' has been completed."
        )

        create_comment_and_notify(
            project=project,
            comment_text=comment_text,
            author_name=request.user.username,
            email_subject=f"Project '{project.title}' Completed"
        )

        ApplicationLog.objects.create(
            message=f"Project '{project.title}' marked as completed by {request.user.username}.",
            logger_name="Complete project",
            interacted_by=request.user.username
        )

        return Response({'detail': 'Project marked as completed', 'status': project.status, 'comment_text': comment_text})


class UserProjectViewSet(viewsets.ViewSet):
    """
    Personal projects for user
    """
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'category__name': ['icontains'],
        'priority': ['exact'],
        'budget': ['gte', 'lte']
    }
    search_fields = ['title', 'description', 'sender_name', 'priority']
    ordering_fields = ['budget', 'created_at', 'updated_at', 'priority']

    @action(detail=False, methods=['get'], url_path='my-projects')
    def my_projects(self, request):
        user = request.user
        projects = Project.objects.filter(
            Q(accepted_by=user) |
            Q(started_by=user) |
            Q(completed_by=user)
        ).distinct()

        for backend in list(self.filter_backends):
            projects = backend().filter_queryset(request, projects, self)

        response_data = {
            "projects": ProjectSerializer(projects, many=True).data
        }

        return Response(response_data)

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        attachment = serializer.save()


class ProjectCommentViewSet(viewsets.ModelViewSet):
    queryset = ProjectComment.objects.all().order_by('-created_at')
    serializer_class = ProjectCommentSerializer
    permission_classes = [IsAdminUser]

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
            message=f"Comment added to project '{project.title}' by {author_name}.",
            logger_name="Create comment to project",
            interacted_by=author_name
        )

        serializer.instance = comment


class AttachmentDownloadView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, attachment_id):
        """
        GET operation to view files
        """
        attachment = get_object_or_404(Attachment, pk=attachment_id)
        original_url = attachment.file.url
        ApplicationLog.objects.create(
            message=f"Attachment '{attachment.file.name}' viewed by {request.user.username}.",
            logger_name="Attachment download",
            interacted_by=request.user.username
        )
        return redirect(original_url)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET operation to view available categories
        """
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class ApplicationLogView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        GET operation to view all logs
        """
        queryset = ApplicationLog.objects.all().order_by('-created_at')

        interacted_by = request.query_params.get('interacted_by')
        if interacted_by:
            queryset = queryset.filter(interacted_by__icontains=interacted_by)

        search_term = request.query_params.get('search')
        if search_term:
            queryset = queryset.filter(message__icontains=search_term)

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = ApplicationLogSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
