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
            'id', 'title', 'description', 'budget', 'start_date', 'end_date',
            'sender_name', 'contact_email', 'status', 'created_at', 'updated_at',
            'attachments', 'comments', 'category'
        ]

class ProjectCreateSerializer(serializers.ModelSerializer):
    """ Used when public user creates a new project proposal. """
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'budget', 'start_date', 'end_date',
            'sender_name', 'contact_email', 'category'
        ]
