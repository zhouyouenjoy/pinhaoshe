from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'model_name', 'event_time', 'location', 'fee', 'created_by', 'approved', 'created_at')
    list_filter = ('approved', 'event_time', 'created_at')
    search_fields = ('title', 'model_name', 'location', 'created_by__username')
    list_editable = ('approved',)
    date_hierarchy = 'created_at'