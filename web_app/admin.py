from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import SyncLog, API


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    list_display = ('port', 'name')
    fields = ('port', 'name')



@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'status_visual', 'records_created', 'records_updated')
    list_filter = ('status', 'start_time')
    readonly_fields = ('start_time', 'end_time', 'status', 'summary', 'records_created', 'records_updated')

    def status_visual(self, obj):
        if obj.status.lower() == 'error':
            return mark_safe('<span style="color: red; font-weight: bold;">🔴 ERROR</span>')
        elif obj.status.lower() == 'success':
            return mark_safe('<span style="color: green; font-weight: bold;">🟢 SUCCESS</span>')
        elif obj.status.lower() == 'running':
            return mark_safe('<span style="color: orange; font-weight: bold;">🟡 RUNNING</span>')
        return obj.status

    status_visual.short_description = 'Status'