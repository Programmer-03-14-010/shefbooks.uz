from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView

from blogs.forms import CommentForm
from blogs.models import BlogModel, BlogCategoryModel


class BlogListView(ListView):
    template_name = 'blogs/blog-list.html'
    model = BlogModel
    context_object_name = 'blogs'
    paginate_by = 5

    def get_queryset(self):
        return BlogModel.objects.all().order_by('-created_at')


def blog_detail(request, pk):
    blog = get_object_or_404(BlogModel, pk=pk)
    related = BlogModel.objects.exclude(pk=pk).order_by('-created_at')[:3]
    comments = blog.comments.all()
    form = CommentForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('users:login')}?next={request.path}")
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
            return redirect('blogs:blog_detail', pk=pk)

    return render(request, 'blogs/blog-detail.html', {
        'blog': blog,
        'related_blogs': related,
        'comments': comments,
        'form': form,
    })