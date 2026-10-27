from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-input post-textarea',
                'placeholder': "What's happening in your circle today?",
                'rows': 3,
                'required': True
            }),
            'image': forms.FileInput(attrs={'class': 'form-file-input', 'accept': 'image/*'})
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-input comment-input',
                'placeholder': 'Write a polite comment...',
                'required': True
            })
        }