from rest_framework import serializers

from .models import Comment, CommunityPost
from .services import companion_label


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nickname = serializers.CharField(allow_null=True)
    profile_image_url = serializers.URLField(allow_null=True, required=False)


class CommentReplySerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "author",
            "is_edited",
            "is_mine",
            "created_at",
            "updated_at",
        ]

    def get_author(self, obj):
        return _author_payload(obj.user)

    def get_is_edited(self, obj):
        return (obj.updated_at - obj.created_at).total_seconds() > 1

    def get_is_mine(self, obj):
        user = self.context.get("request").user
        return user.is_authenticated and obj.user_id == user.id


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "author",
            "replies",
            "is_edited",
            "is_mine",
            "created_at",
            "updated_at",
        ]

    def get_author(self, obj):
        return _author_payload(obj.user)

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []
        replies = getattr(obj, "prefetched_replies", None)
        if replies is None:
            replies = obj.replies.select_related("user").all()
        return CommentReplySerializer(
            replies, many=True, context=self.context).data

    def get_is_edited(self, obj):
        return (obj.updated_at - obj.created_at).total_seconds() > 1

    def get_is_mine(self, obj):
        user = self.context.get("request").user
        return user.is_authenticated and obj.user_id == user.id


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=500, trim_whitespace=True)
    parent_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_content(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("댓글 내용을 입력해주세요.")
        return text

    def validate(self, attrs):
        parent_id = attrs.get("parent_id")
        post = self.context["post"]
        if parent_id is None:
            return attrs
        parent = Comment.objects.filter(post=post, id=parent_id).first()
        if parent is None:
            raise serializers.ValidationError({"parent_id": "원댓글을 찾을 수 없습니다."})
        if parent.parent_id is not None:
            raise serializers.ValidationError(
                {"parent_id": "대댓글에는 답글을 달 수 없습니다."})
        attrs["parent"] = parent
        return attrs


class CommentUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_content(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("댓글 내용을 입력해주세요.")
        return text


class CommunityPostListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    companion_label = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    liked_by_me = serializers.BooleanField(read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "title",
            "body",
            "country_name",
            "city_name",
            "start_date",
            "end_date",
            "nights",
            "companion_type",
            "companion_label",
            "companion_count",
            "author",
            "like_count",
            "comment_count",
            "liked_by_me",
            "is_mine",
            "created_at",
        ]

    def get_author(self, obj):
        return _author_payload(obj.user)

    def get_companion_label(self, obj):
        return companion_label(obj.companion_type)

    def get_is_mine(self, obj):
        user = self.context.get("request").user
        return user.is_authenticated and obj.user_id == user.id


class CommunityPostDetailSerializer(CommunityPostListSerializer):
    packing_snapshot = serializers.JSONField()

    class Meta(CommunityPostListSerializer.Meta):
        fields = CommunityPostListSerializer.Meta.fields + ["packing_snapshot"]


class CommunityPostCreateSerializer(serializers.Serializer):
    recommendation_id = serializers.IntegerField()
    title = serializers.CharField(max_length=80, trim_whitespace=True)
    body = serializers.CharField(max_length=2000, trim_whitespace=True)

    def validate_title(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("제목을 입력해주세요.")
        return text

    def validate_body(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("내용을 입력해주세요.")
        return text


def _author_payload(user):
    return {
        "id": user.id,
        "nickname": user.nickname,
        "profile_image_url": user.profile_image_url,
    }
