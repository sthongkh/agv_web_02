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

    sid, sname = MongoDB().get_all_station(4)#TBD
    data = ()
    txt = ""
    for i in sid:
        txt += "('{}','{}') ".format(sid[i], sname[i])

    res = "({})".format(txt.strip().replace(" ",","))
    data = eval(res)
    station_list = data
    job_num = forms.CharField(label='หมายเลขงาน')
    job_qty = forms.IntegerField(label='จำนวนชิ้นงาน')
    station_send = forms.CharField(
        label='ส่งจากสถานี', 
        widget=forms.Select(choices=station_list))

    station_recv = forms.CharField(
        label='ไปยังสถานี', 
        widget=forms.Select(choices=station_list))

class DelQueueForm(forms.Form):
  
    agv_num = 1#TBD
    user = "atm"#TBD
    data = MongoDB().get_queue_agv(agv_num, user)
    txt = ""
    for i in data:
        num = data.index(i)
        txt += "('{}','Job:{}-Qty:{}') ".format(num, i["job"], i["quantity"])
    
    ret = eval("({})".format(txt.strip().replace(" ", ",")))
    delete_list = forms.MultipleChoiceField(label="รายการจัดส่งของคุณ",
        widget=forms.RadioSelect(), choices=ret)
