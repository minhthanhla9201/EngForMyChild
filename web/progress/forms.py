"""
Form khu quản lý linh vật & huy hiệu (phụ huynh).

Icon KHÔNG phụ thuộc font. Thứ tự ưu tiên: ảnh upload > SVG tĩnh (icon_static,
mặc định của app, commit theo repo) > emoji (fallback). Dùng ModelForm + class
Bootstrap; nhãn tiếng Việt.
"""

from django import forms

from .models import Badge, PetStage


class PetStageForm(forms.ModelForm):
    """Tạo/sửa một mốc linh vật (ngưỡng sao → icon + tên)."""

    class Meta:
        model = PetStage
        fields = ['threshold', 'name_vi', 'icon_static', 'emoji', 'image', 'order', 'active']
        widgets = {
            'threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'VD: 10'}),
            'name_vi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Chồi non'}),
            'icon_static': forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'VD: icons/pet/tree.svg (SVG mặc định)'}),
            'emoji': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': 'Emoji, VD 🌿 (fallback cuối)'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.Select(attrs={'class': 'form-select'}),
        }


class BadgeForm(forms.ModelForm):
    """Tạo/sửa một huy hiệu (điều kiện mở khoá + icon)."""

    class Meta:
        model = Badge
        fields = ['code', 'name_vi', 'icon_static', 'icon', 'icon_image', 'desc_vi',
                  'kind', 'threshold', 'order', 'active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: stars-10'}),
            'name_vi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Mười ngôi sao'}),
            'icon_static': forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'VD: icons/badge/stars-10.svg (SVG mặc định)'}),
            'icon': forms.TextInput(attrs={'class': 'form-control',
                                           'placeholder': 'Emoji, VD 🌟 (fallback cuối)'}),
            'icon_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'desc_vi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lời khen ngắn'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.Select(attrs={'class': 'form-select'}),
        }
