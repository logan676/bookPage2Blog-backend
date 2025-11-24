"""
URL routing for BookPost API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet, IdeaViewSet, UnderlineViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'posts', BlogPostViewSet, basename='blogpost')
router.register(r'ideas', IdeaViewSet, basename='idea')
router.register(r'underlines', UnderlineViewSet, basename='underline')

urlpatterns = [
    path('', include(router.urls)),
]
