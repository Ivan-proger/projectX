from django.contrib import admin
from django.db.models import Count
from mainBot.models import *


@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ("name", "external_id", "last_activity")
    search_fields = ("external_id__startswith", "name")
    list_filter = ("is_superuser", )

@admin.register(Channel)
class ChannelsAdmin(admin.ModelAdmin):
    list_display = ("title", "external_id")
    search_fields = ("title", "external_id")

@admin.register(СategoryChannel)
class СategoryChannelsAdmin(admin.ModelAdmin):
    list_display = ("name", "id")

@admin.register(Comment)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ("created_at", "channel", "user")
    search_fields = ("channel", "user", "text")

@admin.register(Complaint)
class ComplaintsAdmin(admin.ModelAdmin):
    list_display = ("category" ,"created_at", "channel", "user")
    search_fields = ("category", "channel", "user")
    list_filter = ("is_viewed", )

@admin.register(СategoryComplaint)
class СategoryComplaintAdmin(admin.ModelAdmin):
    list_display = ("name", )

@admin.register(SuperChannel)
class SuperChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "external_id", "subscribers_added")

@admin.register(ServiceUsage)
class ServiceUsageAdmin(admin.ModelAdmin):
    list_display = ('date', 'count')