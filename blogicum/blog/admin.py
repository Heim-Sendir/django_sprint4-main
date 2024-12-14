from django.contrib import admin
from .models import Category, Post, Location, Comment


class PostInLine(admin.StackedInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = [
        PostInLine
    ]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Post)
admin.site.register(Location)
admin.site.register(Comment)
