"""Form khu tài khoản."""

from django import forms

from .models import ChildProfile

# Widget chung cho ô passcode (số, ẩn ký tự).
_PASS_WIDGET = forms.PasswordInput(attrs={
    'class': 'form-control', 'inputmode': 'numeric', 'autocomplete': 'off',
})


class ManageUnlockForm(forms.Form):
    """Nhập passcode để mở khoá khu quản lý."""

    passcode = forms.CharField(label='Passcode', widget=_PASS_WIDGET)

    def __init__(self, *args, passcode_obj=None, **kwargs):
        # passcode_obj: bản ghi ManagePasscode để kiểm mã ngay trong form.
        self.passcode_obj = passcode_obj
        super().__init__(*args, **kwargs)

    def clean_passcode(self):
        raw = self.cleaned_data['passcode']
        if not (self.passcode_obj and self.passcode_obj.check_passcode(raw)):
            raise forms.ValidationError('Passcode chưa đúng.')
        return raw


class _SetPasscodeBase(forms.Form):
    """Phần chung: nhập mã mới + nhập lại, kiểm 4–6 chữ số và khớp nhau."""

    passcode1 = forms.CharField(label='Passcode mới', widget=_PASS_WIDGET)
    passcode2 = forms.CharField(label='Nhập lại passcode mới', widget=_PASS_WIDGET)

    def clean_passcode1(self):
        raw = self.cleaned_data['passcode1']
        if not (raw.isdigit() and 4 <= len(raw) <= 6):
            raise forms.ValidationError('Passcode phải gồm 4–6 chữ số.')
        return raw

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('passcode1'), cleaned.get('passcode2')
        if p1 and p2 and p1 != p2:
            self.add_error('passcode2', 'Nhập lại chưa khớp.')
        return cleaned


class SetPasscodeForm(_SetPasscodeBase):
    """Đặt passcode lần đầu (DB chưa có)."""


class ChangePasscodeForm(_SetPasscodeBase):
    """Đổi passcode: phải nhập đúng passcode hiện tại trước."""

    current = forms.CharField(label='Passcode hiện tại', widget=_PASS_WIDGET)

    def __init__(self, *args, passcode_obj=None, **kwargs):
        self.passcode_obj = passcode_obj
        super().__init__(*args, **kwargs)

    def clean_current(self):
        raw = self.cleaned_data['current']
        if not (self.passcode_obj and self.passcode_obj.check_passcode(raw)):
            raise forms.ValidationError('Passcode hiện tại chưa đúng.')
        return raw

    # field order: hiện tại → mới → nhập lại
    field_order = ['current', 'passcode1', 'passcode2']


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
