from django.shortcuts import render
from blog.models import Category


def about(request):
    template = 'pages/about.html'
    return render(request, template)


def rules(request):
    template = 'pages/rules.html'
    return render(request, template)


def category(request):
    template = 'pages/categories.html'
    categories = Category.objects.all().filter(
        is_published=True
    )
    context = {'categories': categories}
    return render(request, template, context)
