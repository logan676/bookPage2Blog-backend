"""
Django REST Framework serializers.
Transforms Django models to/from JSON matching React interfaces.
"""
from rest_framework import serializers
from .models import BlogPost, Paragraph, Idea


class ParagraphSerializer(serializers.ModelSerializer):
    """
    Serializer for Paragraph model.
    Matches React Paragraph interface: { id: number, text: string }
    """
    id = serializers.IntegerField(source='paragraph_id', read_only=True)

    class Meta:
        model = Paragraph
        fields = ['id', 'text']


class IdeaSerializer(serializers.ModelSerializer):
    """
    Serializer for Idea model.
    Matches React Idea interface: { id, paragraphId, quote, note, timestamp }
    """
    id = serializers.CharField(read_only=True)
    paragraphId = serializers.IntegerField(source='paragraph.paragraph_id', read_only=True)
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = Idea
        fields = ['id', 'paragraphId', 'quote', 'note', 'timestamp']

    def get_timestamp(self, obj):
        """Return ISO format timestamp."""
        return obj.created_at.isoformat()


class IdeaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new ideas.
    Accepts paragraphId instead of paragraph object.
    """
    paragraphId = serializers.IntegerField(write_only=True)

    class Meta:
        model = Idea
        fields = ['paragraphId', 'quote', 'note']

    def create(self, validated_data):
        paragraph_id = validated_data.pop('paragraphId')
        post_id = self.context.get('post_id')

        # Get the paragraph by post and paragraph_id
        try:
            paragraph = Paragraph.objects.get(
                post_id=post_id,
                paragraph_id=paragraph_id
            )
        except Paragraph.DoesNotExist:
            raise serializers.ValidationError(
                f"Paragraph {paragraph_id} not found in this post."
            )

        # Create the idea
        idea = Idea.objects.create(
            post_id=post_id,
            paragraph=paragraph,
            **validated_data
        )
        return idea


class BlogPostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing posts.
    """
    publishDate = serializers.CharField(source='publish_date', read_only=True)
    imageUrl = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'author', 'publishDate', 'imageUrl']

    def get_imageUrl(self, obj):
        """Return full URL for image."""
        if obj.image_url:
            return obj.image_url
        elif obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ''


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for single post with nested paragraphs and ideas.
    Matches React BlogPost interface.
    """
    publishDate = serializers.CharField(source='publish_date', read_only=True)
    imageUrl = serializers.SerializerMethodField()
    content = ParagraphSerializer(many=True, read_only=True)
    ideas = IdeaSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'author', 'publishDate', 'imageUrl', 'content', 'ideas']

    def get_imageUrl(self, obj):
        """Return full URL for image."""
        if obj.image_url:
            return obj.image_url
        elif obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ''


class BlogPostUploadSerializer(serializers.Serializer):
    """
    Serializer for handling image upload and OCR processing.
    """
    image = serializers.ImageField(required=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    author = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_image(self, value):
        """Validate image file type and size."""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large (max 10MB).")

        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
            )

        return value
