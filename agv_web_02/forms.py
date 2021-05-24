from django import forms
from .mongodb import MongoDB


class SigninForm(forms.Form):
    email = forms.EmailField(label='อีเมล')
    password = forms.CharField(
        label='รหัสผ่าน', 
        widget=forms.PasswordInput(render_value=True)
    )
    save = forms.BooleanField(label='บันทึกไว้ในเครื่องนี้', required=False)

class LoginForm(forms.Form):
    user = forms.CharField(label='ชื่อผู้ใช้')
    password = forms.CharField(
        label='รหัสผ่าน', 
        widget=forms.PasswordInput(render_value=True)
    )
    save = forms.BooleanField(label='บันทึกไว้ในเครื่องนี้', required=False)


class AddQueueForm(forms.Form):
    station_list = ((1, 'Option=1'),(2, 'Option=2'),)
    rest = MongoDB().get_all_station(4)
    station_select = forms.CharField(
        label='ส่งจากสถานี', 
        widget=forms.Select(choices=station_list))