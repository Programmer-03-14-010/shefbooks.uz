from django import forms
from .models import BlogCommentModel

class CommentForm(forms.ModelForm):
    class Meta:
        model = BlogCommentModel
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'placeholder': 'Your Message…', 'rows': 5}),
        }