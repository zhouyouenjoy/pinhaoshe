from django.contrib import admin
from .models import Event, EventModel, EventSession

class EventSessionInline(admin.TabularInline):
    model = EventSession
    extra = 1

class EventModelInline(admin.TabularInline):
    model = EventModel
    extra = 1
    inlines = [EventSessionInline]

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_time', 'location', 'created_by', 'approved', 'created_at')
    list_filter = ('approved', 'event_time', 'created_at')
    search_fields = ('title', 'location', 'created_by__username')
    list_editable = ('approved',)
    date_hierarchy = 'created_at'
    inlines = [EventModelInline]

@admin.register(EventModel)
class EventModelAdmin(admin.ModelAdmin):
    list_display = ('event', 'name', 'fee')
    search_fields = ('name', 'event__title')

@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = ('model', 'title', 'start_time', 'end_time')
    search_fields = ('title', 'model__name')