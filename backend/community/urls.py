from django.urls import path

from .views import (CommentDetailView, CommentListCreateView,
                    CommunityPostDetailView, CommunityPostListCreateView,
                    PostLikeToggleView, RecommendationShareStatusView)

urlpatterns = [
    path("community/posts/", CommunityPostListCreateView.as_view(), name="community-posts"),
    path("community/posts/share-status/", RecommendationShareStatusView.as_view(),
         name="community-share-status"),
    path("community/posts/<int:post_id>/", CommunityPostDetailView.as_view(),
         name="community-post-detail"),
    path("community/posts/<int:post_id>/like/", PostLikeToggleView.as_view(),
         name="community-post-like"),
    path("community/posts/<int:post_id>/comments/", CommentListCreateView.as_view(),
         name="community-comments"),
    path("community/posts/<int:post_id>/comments/<int:comment_id>/",
         CommentDetailView.as_view(), name="community-comment-detail"),
]
