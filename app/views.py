from django.shortcuts import render, redirect
from .models import User, Post, Category, Comment
from .forms import PostForm, RegisterForm, UpdateUserForm, UpdateCommentForm
from django.contrib.auth import login
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.core.serializers import serialize
from django.http import JsonResponse
from django.template.defaultfilters import timesince_filter
import json

# Create your views here.
def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def sign_up(request):
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    context = {'form':form}
    return render(request, 'registration/sign_up.html', context)

def update_user(request):
    user = request.user
    form = UpdateUserForm(instance = user)
    if request.method == 'POST':
        form = UpdateUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('home', 1)
    context = {'form':form}
    return render(request, 'app/update-user.html', context)


def profile(request,id):
    user = User.objects.get(id =id)
    posts = user.post_set.all()
    comments = user.comment_set.all()
    context = {'user':user, 'posts':posts, 'comments':comments}
    return render(request, 'app/profile.html', context)


def redirect_to_home(request):
    return redirect('home', 1)

    
def home(request, page):
    if request.GET.get('q'):
        q = request.GET.get('q')
    else:
        q = ''
    
    categories = Category.objects.all()
    posts = Post.objects.filter(
        Q(title__icontains=q) |
        Q(body__icontains=q) |
        Q(category__name__icontains=q) |
        Q(author__name__icontains=q)    
    )
    comments = Comment.objects.filter(
        Q(user__name__icontains = q) |
        Q(body__icontains = q) |
        Q(post__category__name__icontains = q)   
    )
    
    paginator = Paginator(posts, per_page=3)
    page_object = paginator.get_page(page)
    
    context = {
        'posts':posts, 
        'categories':categories,
        'comments':comments,  
        'page_object':page_object,
        'q':q,

    }   
    if is_ajax(request):
        posts = []
        for post in page_object:
            data = {
                'title':post.title,
                'body':post.body,
                'photo':post.photo.url,
                'author_name':post.author.name,
                'avatar':post.author.avatar.url,
                'category':post.category.name,
                'created_at':timesince_filter(post.created_at),
                'post_id':post.id
            }
            posts.append(data)
        return JsonResponse({'posts':posts})
    return render(request, 'app/home.html', context)
    

@login_required(login_url='login')
def create_post(request):
    if request.user.is_superuser:
        form = PostForm()
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.title = post.title.capitalize()
                post.save()
                return redirect('home', 1)
        context = {'form':form}
        return render(request, 'app/create-post.html', context)
    else:
        return HttpResponse('You are not allowed to make a post ')

@login_required(login_url='login')
def get_post(request, pk):
    post = Post.objects.get(id=pk)
    if is_ajax(request):
        if request.method == 'POST':
            data = json.loads(request.body)
            print(data)
            message = Comment.objects.create (
                user = request.user,
                body = data,
                post = post
            )
            message.save()
            comment = {
                'body':message.body,
                'user_avatar':message.user.avatar.url,
                'user_name':message.user.name,
                'created_at':timesince_filter(message.created_at),
                'user_id':message.user.id,
                'id':message.id
            }
            return JsonResponse({'message':comment})
    comments = post.comment_set.all()
    context = {'post':post, 'comments':comments}
    return render(request,'app/get-post.html', context)

@login_required
def add_category(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            category = request.POST['category']
            Category.objects.create(name=category)
            return redirect('home', 1)
        
        return render(request, 'app/add_category.html')

@login_required(login_url='login')
def update_post(request, pk):
    post = Post.objects.get(id=pk)  
    form = PostForm(instance=post)
    if post.author == request.user:
        if request.method == 'POST':
            form = PostForm(request.POST,request.FILES, instance=post)
            if form.is_valid():
                post = form.save(commit=False)
                post.title = post.title.capitalize()
                post.save()
                return redirect('get_post', pk=post.id)
    context = {'form':form}
    return render(request, 'app/update-post.html', context)

@login_required(login_url='login')
def update_comment(request, pk):
    comment = Comment.objects.get(id=pk)
    form = UpdateCommentForm(instance=comment)
    if request.method == 'POST':
        form = UpdateCommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.save()
            return redirect('get_post', pk=comment.post.pk)
    return render(request, 'app/update_comment.html', {'form':form})


def delete_post(request, pk):
    page = request.GET.get('page')
    post = Post.objects.get(id=pk) 
    if post.author == request.user:
        if request.method == 'POST':
            post.delete()
            return redirect('home', 1)
    return render(request, 'app/delete.html', {'obj':post.title})


def delete_comment(request, pk):
    comment = Comment.objects.get(id=pk) 
    if comment.user == request.user:
        if request.method == 'POST':
            comment.delete()
            return redirect('get_post', pk=comment.post.id)
    return render(request, 'app/delete.html', {'obj':comment})







