"""Form khu tài khoản."""

from django import forms

from .models import ChildProfile


class ChildProfileForm(forms.ModelForm):
    """Form tạo/sửa hồ sơ bé. owner gán ở view (không cho người dùng tự chọn)."""

    class Meta:
        model = ChildProfile
        fields = ['name', 'birth_year', 'avatar']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên bé'}),
            'birth_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'VD: 2018'}),
            'avatar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emoji, vd 🐥'}),
        }
