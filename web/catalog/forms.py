"""
Form khu quản lý nội dung học (phụ huynh): Chủ đề, Từ vựng, Nhập CSV.

Dùng ModelForm + class Bootstrap; nhãn/thông báo tiếng Việt (skill §7).
"""

from django import forms

from .models import Topic, Word


class TopicForm(forms.ModelForm):
    """Tạo/sửa chủ đề. slug tự sinh từ name_en ở view nếu để trống."""

    class Meta:
        model = Topic
        fields = ['name_en', 'name_vi', 'slug', 'icon', 'order', 'active']
        widgets = {
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Animals'}),
            'name_vi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Động vật'}),
            'slug': forms.TextInput(attrs={'class': 'form-control',
                                           'placeholder': 'Để trống để tự sinh từ tên tiếng Anh'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emoji, VD 🐶'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # slug có thể bỏ trống khi tạo mới — view sẽ tự sinh từ name_en.
        self.fields['slug'].required = False


class WordForm(forms.ModelForm):
    """Tạo/sửa từ vựng. phonetic (IPA) để trống sẽ tự sinh ở view."""

    class Meta:
        model = Word
        fields = ['topic', 'text_en', 'text_vi', 'phonetic', 'image', 'level', 'active']
        widgets = {
            'topic': forms.Select(attrs={'class': 'form-select'}),
            'text_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: cat'}),
            'text_vi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: con mèo'}),
            'phonetic': forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': 'Để trống để tự sinh IPA'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'level': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phonetic'].required = False
        # Chỉ cho chọn chủ đề đang dùng.
        self.fields['topic'].queryset = Topic.objects.filter(active='Y')


class WordImportForm(forms.Form):
    """Form upload file CSV để nhập từ hàng loạt."""

    csv_file = forms.FileField(
        label='Tệp CSV',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text='Cột bắt buộc: text_en. Cột tuỳ chọn: topic, text_vi, topic_vi, level, image.',
    )
    make_audio = forms.BooleanField(
        label='Sinh sẵn audio phát âm (chậm hơn, cần TTS)',
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean_csv_file(self):
        f = self.cleaned_data['csv_file']
        if not f.name.lower().endswith('.csv'):
            raise forms.ValidationError('Vui lòng chọn file có đuôi .csv.')
        return f
