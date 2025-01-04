# proposals/admin.py
from django.contrib import admin
from .models import Project, Attachment, ProjectComment, Category

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'sender_name', 'contact_email', 'created_at')
    list_filter = ('status', 'category')

admin.site.register(Attachment)
admin.site.register(ProjectComment)
admin.site.register(Category)
