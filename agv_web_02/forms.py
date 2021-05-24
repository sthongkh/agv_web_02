from django import forms

class SigninForm(forms.Form):
    email = forms.EmailField(label='อีเมล')
    password = forms.CharField(
        label='รหัสผ่าน', 
        widget=forms.PasswordInput(render_value=True)
    )
    save = forms.BooleanField(label='บันทึกไว้ในเครื่องนี้', required=False)