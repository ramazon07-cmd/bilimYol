from django.contrib import admin

from .models import Conversation, Message, Notification


admin.site.register(Notification)
admin.site.register(Conversation)
admin.site.register(Message)
