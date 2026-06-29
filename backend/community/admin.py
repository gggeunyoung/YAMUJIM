from django.contrib import admin

from .models import Comment, CommunityPost, PostLike

admin.site.register(CommunityPost)
admin.site.register(PostLike)
admin.site.register(Comment)
