from django.db.models import Count, Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, CommunityPost, PostLike
from .serializers import (CommentCreateSerializer, CommentSerializer,
                          CommentUpdateSerializer, CommunityPostCreateSerializer,
                          CommunityPostDetailSerializer,
                          CommunityPostListSerializer)
from .services import (create_post_from_recommendation,
                       get_recommendation_for_user, is_recommendation_shared)


def _annotate_posts(queryset, user):
    liked = PostLike.objects.filter(post_id=OuterRef("pk"), user=user)
    return queryset.annotate(
        like_count=Count("likes", distinct=True),
        comment_count=Count("comments", distinct=True),
        liked_by_me=Exists(liked),
    )


class CommunityPostListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommunityPostCreateSerializer
        return CommunityPostListSerializer

    def get_queryset(self):
        return _annotate_posts(
            CommunityPost.objects.select_related("user"),
            self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = CommunityPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = create_post_from_recommendation(
            request.user,
            serializer.validated_data["recommendation_id"],
            serializer.validated_data["title"],
            serializer.validated_data["body"],
        )
        post = _annotate_posts(
            CommunityPost.objects.filter(pk=post.pk).select_related("user"),
            request.user,
        ).get()
        out = CommunityPostDetailSerializer(post, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class RecommendationShareStatusView(APIView):
    """GET /community/posts/share-status/?recommendation_id= — 추천 공유 여부."""

    def get(self, request):
        raw_id = request.query_params.get("recommendation_id")
        if not raw_id:
            return Response(
                {"recommendation_id": "recommendation_id가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            recommendation_id = int(raw_id)
        except (TypeError, ValueError):
            return Response(
                {"recommendation_id": "올바른 recommendation_id가 아닙니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        get_recommendation_for_user(request.user, recommendation_id)
        post = CommunityPost.objects.filter(recommendation_id=recommendation_id).first()
        return Response({
            "shared": post is not None,
            "post_id": post.id if post else None,
        })


class CommunityPostDetailView(generics.RetrieveDestroyAPIView):
    lookup_url_kwarg = "post_id"

    def get_serializer_class(self):
        return CommunityPostDetailSerializer

    def get_queryset(self):
        return _annotate_posts(
            CommunityPost.objects.select_related("user"),
            self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user_id != request.user.id:
            return Response({"detail": "본인 게시글만 삭제할 수 있습니다."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class PostLikeToggleView(APIView):
    def post(self, request, post_id):
        post = get_object_or_404(CommunityPost, pk=post_id)
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        like_count = post.likes.count()
        return Response({"liked": liked, "like_count": like_count})


class CommentListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_post(self):
        return get_object_or_404(CommunityPost, pk=self.kwargs["post_id"])

    def get_queryset(self):
        post = self.get_post()
        replies_qs = Comment.objects.select_related("user").order_by("created_at")
        return (
            Comment.objects.filter(post=post, parent__isnull=True)
            .select_related("user")
            .prefetch_related(Prefetch("replies", queryset=replies_qs, to_attr="prefetched_replies"))
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = CommentSerializer(
            queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        post = self.get_post()
        serializer = CommentCreateSerializer(
            data=request.data, context={"post": post, "request": request})
        serializer.is_valid(raise_exception=True)
        parent = serializer.validated_data.get("parent")
        comment = Comment.objects.create(
            post=post,
            user=request.user,
            parent=parent,
            content=serializer.validated_data["content"],
        )
        out = CommentSerializer(comment, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    def get_comment(self, request, post_id, comment_id):
        return get_object_or_404(
            Comment.objects.select_related("user"),
            pk=comment_id,
            post_id=post_id,
        )

    def patch(self, request, post_id, comment_id):
        comment = self.get_comment(request, post_id, comment_id)
        if comment.user_id != request.user.id:
            return Response({"detail": "본인 댓글만 수정할 수 있습니다."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = CommentUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        comment.content = serializer.validated_data["content"]
        comment.save(update_fields=["content", "updated_at"])
        return Response(CommentSerializer(comment, context={"request": request}).data)

    def delete(self, request, post_id, comment_id):
        comment = self.get_comment(request, post_id, comment_id)
        if comment.user_id != request.user.id:
            return Response({"detail": "본인 댓글만 삭제할 수 있습니다."},
                            status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
