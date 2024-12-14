from django.shortcuts import get_object_or_404, redirect
from blog.models import Post, Category, Comment
from django.utils import timezone
from django.views.generic import (CreateView, ListView,
                                  DetailView, UpdateView, DeleteView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.http import Http404
from django.utils import timezone


from .forms import PostForm, CommentForm

User = get_user_model()


# ----------- INDEX VIEW -----------


class IndexView(ListView):
    template_name = 'blog/index.html'
    model = Post
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.select_related(
            'location',
            'category',
            'author'
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comment'))


# ----------- PROFILE VIEW -----------


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object
        user_posts = Post.objects.none()
        if self.request.user == profile_user:
            user_posts = Post.objects.select_related(
                'location',
                'category',
                'author'
            ).filter(
                author=profile_user,
            ).order_by('-pub_date').annotate(comment_count=Count('comment'))
        else:
            user_posts = Post.objects.select_related(
                'location',
                'category',
                'author'
            ).filter(
                author=profile_user,
                is_published=True
            ).order_by('-pub_date').annotate(comment_count=Count('comment'))
        paginator = Paginator(user_posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    fields = [
        'first_name',
        'last_name',
        'username',
        'email'
    ]

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.request.user.is_authenticated:
            return redirect('blog:index')
        if obj.username != self.request.user.username:
            return redirect('blog:profile', username=request.user.username)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


# ----------- POST VIEW -----------


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        self.obj = get_object_or_404(Post, pk=kwargs['pk'])
        if self.obj.author != self.request.user:
            return redirect('blog:post_detail', pk=self.obj.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'pk'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        self.obj = self.get_object()
        if self.obj.author != self.request.user:
            return redirect('blog:post_detail', pk=self.obj.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def dispatch(self, request, *args, **kwargs):
        self.obj = get_object_or_404(Post, pk=kwargs['pk'])
        if self.obj.author == self.request.user:
            return super().dispatch(request, *args, **kwargs)
        elif self.obj.is_published:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise Http404('Пост не найден.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.all().filter(
            post_id=self.kwargs['pk']
        ).order_by('created_at')
        return context

# ---------------------- COMMENT VIEW ----------------------


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.obj = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.obj.id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.obj.id})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.obj = get_object_or_404(Comment, id=kwargs['comment_id'])
        if self.obj.author != self.request.user:
            return redirect('blog:index')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs['comment_id'])
        return obj

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.obj.post_id})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.obj = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if self.obj.author != self.request.user:
            return redirect('blog:post_detail', pk=self.obj.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs['comment_id'])
        return obj

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.obj.post_id})


# ---------------------- CATEGORY VIEW ----------------------


class CategoryView(DetailView):
    model = Category
    template_name = 'blog/category.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'category'

    def get_object(self):
        queryset = self.get_queryset()
        self.obj = get_object_or_404(queryset.filter(is_published=True),
                                     slug=self.kwargs['category_slug'])
        return self.obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_posts = Post.objects.select_related(
            'category',
        ).filter(
            category=self.obj.id,
            category__is_published=True,
            is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date').annotate(comment_count=Count('comment'))
        paginator = Paginator(user_posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context
