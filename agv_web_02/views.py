from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from database.models import Member, MemberForm
from .forms import *
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from .mongodb import MongoDB


def index(request):
    return render(request, 'index.html')

def dashboard(request):
    #ถ้ายังไม่มีค่า id ในเซสชัน แสดงว่ายังไม่เข้าสู่ระบบ
    #ก็ให้ย้ายไปที่เพจ การเข้าสู่ระบบ
    if 'id' not in request.session:
        return redirect(reverse('member_login'))
    
    id = request.session['id']
    name = request.session['name']

    return render(request, 'dashboard.html', {
        'id':id, 'name':name})

def member_signout(request):
    if 'id' in request.session:
        del request.session['id']
        del request.session['name']

        if 'user_plant' in request.session:
            del request.session['user_plant']

    return redirect(reverse('dashboard'))

@csrf_exempt
def member_login(request):
    #ถ้าในขณะนั้นได้เข้าสู่ระบบแล้ว 
    #ก็ไปยังเพจหลักของสมาชิกได้ทันที
    if 'id' in request.session:
        return redirect(reverse('dashboard'))

    #ถ้าโพสต์ข้อมูลเข้ามา 
    err_msg = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        user = request.POST.get('user', '')
        password = request.POST.get('password', '')
        save = request.POST.get('save', False)

        #นำอีเมลและรหัสผ่านไปตรวจสอบว่ามีในฐานข้อมูลหรือไม่
        #ถ้ามี ก็เก็บค่า id และชื่อไว้ในเซสชัน เพื่อบ่งชี้ว่า เข้าสู่ระบบแล้ว
    
        row = Member.objects.filter(
                Q(user=user) & Q(password=password))

   

        id, user_plant = MongoDB().match_user(user, password)


        if id != False:
            request.session['id'] = id
            request.session['name'] = user
            if 'user_plant' not in request.session:
                request.session['user_plant'] = user_plant

            #สร้างออบเจ็กต์ HttpResponse เพื่อส่งข้อมูลกลับไปและจัดการคุกกี้
            tmp = loader.get_template('dashboard.html')
            data = {'name':user}
            response = HttpResponse(tmp.render(data))

            #ถ้าเลือกบันทึกข้อมูลไว้ในเครื่อง ก็จัดเก็บในแบบคุกกี้ โดยกำหนดอายุ 1 วัน
            #แต่ถ้าไม่เลือก ก็ให้ลบออกจากคุกกี้ (เผื่อจะเก็บไว้ก่อนแล้ว)
            if save:
                age = 60*60*24
                response.set_cookie('user', value=user, max_age=age)
                response.set_cookie('password', value=password, max_age=age)
                response.set_cookie('save', value=save, max_age=age)
            else:
                response.delete_cookie('user')
                response.delete_cookie('password')
                response.delete_cookie('save')

            return response
            
        else:
            err_msg = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง'

    #ถ้าเปิดเพจ และมีข้อมูลจัดเก็บในแบบคุกกี้เอาไว้แล้ว
    #ให้อ่านค่า จากนั้นนำไปเติมเป็นค่าล่วงหน้าให้แก่ฟอร์ม
    elif 'user' in request.COOKIES:
        user = request.COOKIES.get('user', '')
        password = request.COOKIES.get('password', '')
        save = request.COOKIES.get('save', False)
        form = LoginForm(
            initial={'user':user, 'password':password, 'save':save}
        )

    else:
        form = LoginForm()
    
    return render(
        request, 
        'member-login.html', 
        {'form':form, 'err_msg':err_msg})

@csrf_exempt
def add_queue(request):
    #check session
    if 'id' not in request.session:
        return redirect(reverse('member_login'))

    err_msg = None
    data_dict = {}
    if request.method == 'POST':
        form = AddQueueForm(request.POST)
        job_num = request.POST.get('job_num', '')
        job_qty = request.POST.get('job_qty', 0)
        station_send = request.POST.get('station_send', ())
        station_recv = request.POST.get('station_recv', ())
        user_plant = request.session['user_plant']
        sid, sname = MongoDB().get_all_station(user_plant)
        user = request.session['name']
        from_station = sname[sid.index(int(station_send))]
        to_station  = sname[sid.index(int(station_recv))]
        agv_num = MongoDB().get_mapping_agv(user_plant)
        queue_num = int(MongoDB().get_queue_number_max_agv(agv_num)) + 1
        data_dict = {
            "user": user, 
            "job": job_num, 
            "quantity": job_qty, 
            "from": from_station, 
            "to": to_station,
            "queue": queue_num}
        if from_station == to_station:
            err_msg = "ไม่สามารถเลือกสถานีส่งและสถานีรับเหมือนกันได้"
        else:    
            ret = MongoDB().add_queue(agv_num, data_dict)
            err_msg = None

    form = AddQueueForm()

    return render(
        request, 
        'add-queue.html', 
        {'form':form, 'err_msg':err_msg, 'data_dict':data_dict})

@csrf_exempt
def del_queue(request):
    err_msg = None
    user = request.session['name']
    user_plant = request.session['user_plant']
    agv_num = MongoDB().get_mapping_agv(user_plant)
    #check session
    if 'id' not in request.session:
        return redirect(reverse('member_login'))

    if request.method == 'POST':
        form = DelQueueForm(request.POST)
        del_index = request.POST.get('delete_list', None)
        data = MongoDB().get_queue_agv(agv_num, user)
        del_id = data[int(del_index)]["_id"]
        res = MongoDB().del_queue(agv_num, del_id)

    else:
        form = DelQueueForm()

    return render(request, 'del-queue.html', {'form':form, 'err_msg':err_msg})

def del_2(request):
    user = request.session['name']
    user_plant = request.session['user_plant']
    agv_num = MongoDB().get_mapping_agv(user_plant)
    data = MongoDB().get_queue_agv(agv_num, user)
    if request.method == 'POST':
        print("s")

        #res = MongoDB().del_queue(agv_num, del_id)

    return render(request, 'del-q2.html', {'data':data})
