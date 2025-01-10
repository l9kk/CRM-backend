from django.utils import timezone
from rest_framework import serializers
from .models import Project, Attachment, ProjectComment, Category


class AttachmentSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=True
    )

    class Meta:
        model = Attachment
        fields = ['id', 'file', 'uploaded_at', 'project']

    def validate_file(self, value):
        max_file_size = 5 * 1024 * 1024  # 5 MB
        allowed_file_types = ['image/jpeg', 'image/png', 'application/pdf']

        if value.size > max_file_size:
            raise serializers.ValidationError("File size must not exceed 5MB.")

        # If you're using Cloudinary and there's no local content_type, this may be empty.
        file_type = getattr(value, 'content_type', None)
        if not file_type or file_type not in allowed_file_types:
            raise serializers.ValidationError("Invalid file type. Allowed types: JPEG, PNG, PDF.")

        return value


class ProjectCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectComment
        fields = ['id', 'comment_text', 'author_name', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProjectSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments = ProjectCommentSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'budget', 'deadline',
            'sender_name', 'contact_email', 'status', 'created_at', 'updated_at',
            'attachments', 'comments', 'category'
        ]


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Used when public users create a new project proposal.
    """
    deadline = serializers.DateField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'budget', 'deadline',
            'sender_name', 'contact_email', 'category', 'status',
            'created_at', 'updated_at'
        ]

    def validate_deadline(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("The deadline cannot be in the past.")
        return value
