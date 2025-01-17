from django.contrib import admin

from .models import ApplicationLog
from .models import Project, Attachment, ProjectComment, Category

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'sender_name', 'contact_email', 'created_at')
    list_filter = ('status', 'category')

@admin.register(ApplicationLog)
class ApplicationLogAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_staff and request.user.is_superuser

    list_display = ('message', 'logger_name', 'interacted_by', 'created_at')
    search_fields = ('message', 'logger_name', 'interacted_by')
    list_filter = ('logger_name', 'created_at')

admin.site.register(Attachment)
admin.site.register(ProjectComment)
admin.site.register(Category)
