"""
Django Admin configuration for BookPost models.
"""
from django.contrib import admin
from .models import BlogPost, Paragraph, Idea


class ParagraphInline(admin.TabularInline):
    """Inline admin for paragraphs."""
    model = Paragraph
    extra = 0
    fields = ['paragraph_id', 'text']
    ordering = ['paragraph_id']


class IdeaInline(admin.TabularInline):
    """Inline admin for ideas."""
    model = Idea
    extra = 0
    fields = ['paragraph', 'quote', 'note', 'created_at']
    readonly_fields = ['created_at']


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for BlogPost model."""
    list_display = ['title', 'author', 'created_at', 'paragraph_count']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'author']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ParagraphInline, IdeaInline]

    def paragraph_count(self, obj):
        """Display number of paragraphs."""
        return obj.content.count()
    paragraph_count.short_description = 'Paragraphs'


@admin.register(Paragraph)
class ParagraphAdmin(admin.ModelAdmin):
    """Admin interface for Paragraph model."""
    list_display = ['__str__', 'post', 'paragraph_id', 'text_preview']
    list_filter = ['post']
    search_fields = ['text', 'post__title']
    ordering = ['post', 'paragraph_id']

    def text_preview(self, obj):
        """Show preview of paragraph text."""
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text Preview'


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    """Admin interface for Idea model."""
    list_display = ['__str__', 'post', 'paragraph', 'created_at']
    list_filter = ['created_at', 'post']
    search_fields = ['quote', 'note', 'post__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
