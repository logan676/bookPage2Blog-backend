"""
Django REST Framework Views for BookPost API.
"""
import os
import tempfile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from .models import BlogPost, Paragraph, Idea, Underline
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostUploadSerializer,
    IdeaSerializer,
    IdeaCreateSerializer,
    UnderlineSerializer,
    UnderlineCreateSerializer,
)
from .ocr_service import ocr_service


class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BlogPost model.

    Endpoints:
    - GET    /api/posts/           - List all posts
    - POST   /api/posts/upload/    - Upload image and create post with OCR
    - GET    /api/posts/{id}/      - Get single post with paragraphs and ideas
    - PUT    /api/posts/{id}/      - Update post
    - DELETE /api/posts/{id}/      - Delete post
    """
    queryset = BlogPost.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return BlogPostListSerializer
        elif self.action == 'upload':
            return BlogPostUploadSerializer
        return BlogPostDetailSerializer

    def list(self, request, *args, **kwargs):
        """List all blog posts."""
        queryset = self.get_queryset()
        serializer = BlogPostListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get single blog post with all paragraphs and ideas."""
        instance = self.get_object()
        serializer = BlogPostDetailSerializer(
            instance,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload book page image, perform OCR, and create blog post.

        Request:
            - image: Image file (multipart/form-data)
            - title: Optional post title
            - author: Optional author name

        Response:
            - BlogPost with extracted paragraphs
        """
        serializer = BlogPostUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data['image']
        title = serializer.validated_data.get('title', 'Untitled Post')
        author = serializer.validated_data.get('author', 'Anonymous')

        # Save uploaded image to temporary file for OCR processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_image_path = temp_file.name

        try:
            # Perform OCR and extract paragraphs
            raw_text, paragraphs = ocr_service.extract_and_parse(temp_image_path)

            # Generate title from first paragraph if not provided
            if not title or title == 'Untitled Post':
                if paragraphs:
                    # Use first 50 characters of first paragraph as title
                    title = paragraphs[0][:50] + ('...' if len(paragraphs[0]) > 50 else '')
                else:
                    title = 'Untitled Post'

            # Create BlogPost instance
            blog_post = BlogPost.objects.create(
                title=title,
                author=author,
                image=image_file
            )

            # Create Paragraph instances
            for idx, para_text in enumerate(paragraphs, start=1):
                Paragraph.objects.create(
                    post=blog_post,
                    paragraph_id=idx,
                    text=para_text
                )

            # Return created post with paragraphs
            response_serializer = BlogPostDetailSerializer(
                blog_post,
                context={'request': request}
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': f'OCR processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Clean up temporary file
            if os.path.exists(temp_image_path):
                os.unlink(temp_image_path)

    def update(self, request, *args, **kwargs):
        """Update blog post (title, author)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Only allow updating title and author
        allowed_fields = {'title', 'author'}
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=filtered_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete blog post and all related paragraphs and ideas."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IdeaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Idea model.

    Endpoints:
    - GET    /api/ideas/?post={post_id}  - List ideas for a post
    - POST   /api/ideas/                 - Create new idea
    - PUT    /api/ideas/{id}/            - Update idea
    - DELETE /api/ideas/{id}/            - Delete idea
    """
    queryset = Idea.objects.all()
    serializer_class = IdeaSerializer

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return IdeaCreateSerializer
        return IdeaSerializer

    def get_queryset(self):
        """Filter ideas by post_id if provided."""
        queryset = Idea.objects.all()
        post_id = self.request.query_params.get('post', None)

        if post_id:
            queryset = queryset.filter(post_id=post_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create new idea linked to a paragraph."""
        # Get post_id from request data
        post_id = request.data.get('post_id')
        if not post_id:
            return Response(
                {'error': 'post_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify post exists
        get_object_or_404(BlogPost, id=post_id)

        serializer = IdeaCreateSerializer(
            data=request.data,
            context={'post_id': post_id, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        idea = serializer.save()

        # Return created idea with full serialization
        response_serializer = IdeaSerializer(idea)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update idea (quote and/or note)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Only allow updating quote and note
        allowed_fields = {'quote', 'note'}
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=filtered_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete idea."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnderlineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Underline model.

    Endpoints:
    - GET    /api/underlines/?post={post_id}  - List underlines for a post
    - POST   /api/underlines/                 - Create new underline
    - DELETE /api/underlines/{id}/            - Delete underline
    """
    queryset = Underline.objects.all()
    serializer_class = UnderlineSerializer

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UnderlineCreateSerializer
        return UnderlineSerializer

    def get_queryset(self):
        """Filter underlines by post_id if provided."""
        queryset = Underline.objects.all()
        post_id = self.request.query_params.get('post', None)

        if post_id:
            queryset = queryset.filter(post_id=post_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create new underline linked to a paragraph."""
        # Get post_id from request data
        post_id = request.data.get('post_id')
        if not post_id:
            return Response(
                {'error': 'post_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify post exists
        get_object_or_404(BlogPost, id=post_id)

        serializer = UnderlineCreateSerializer(
            data=request.data,
            context={'post_id': post_id, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        underline = serializer.save()

        # Return created underline with full serialization
        response_serializer = UnderlineSerializer(underline)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Delete underline."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
