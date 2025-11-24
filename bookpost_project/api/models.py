"""
Django models for BookPost application.
Aligned with React types.ts structure.
"""
from django.db import models
from django.contrib.auth.models import User


class BlogPost(models.Model):
    """
    Main blog post model containing metadata and reference to uploaded image.
    Maps to React BlogPost interface.
    """
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, default='Anonymous')
    image = models.ImageField(upload_to='book_pages/', null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True)  # For cloud storage URLs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    @property
    def publish_date(self):
        """Format publish date to match React interface."""
        return self.created_at.strftime('%B %d, %Y')


class Paragraph(models.Model):
    """
    Individual paragraph extracted from the book page.
    Maps to React Paragraph interface.
    """
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='content'
    )
    paragraph_id = models.IntegerField()  # Order/position in the document
    text = models.TextField()

    class Meta:
        ordering = ['paragraph_id']
        unique_together = ['post', 'paragraph_id']
        verbose_name = 'Paragraph'
        verbose_name_plural = 'Paragraphs'

    def __str__(self):
        return f"Paragraph {self.paragraph_id} of {self.post.title}"

    @property
    def id_for_frontend(self):
        """Return paragraph_id for frontend compatibility."""
        return self.paragraph_id


class Idea(models.Model):
    """
    User thoughts/ideas linked to specific paragraphs.
    Maps to React Idea interface.
    """
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='ideas'
    )
    paragraph = models.ForeignKey(
        Paragraph,
        on_delete=models.CASCADE,
        related_name='ideas'
    )
    quote = models.TextField(help_text='The specific text highlighted/underlined')
    note = models.TextField(help_text='User\'s thought or commentary')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Idea'
        verbose_name_plural = 'Ideas'

    def __str__(self):
        return f"Idea on '{self.quote[:50]}...'"

    @property
    def timestamp(self):
        """Return ISO format timestamp for frontend."""
        return self.created_at.isoformat()

    @property
    def paragraph_id(self):
        """Return paragraph_id for frontend compatibility."""
        return self.paragraph.paragraph_id
