from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from database.models import Member, MemberForm
from .forms import SigninForm
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader


def index(request):
    return render(request, 'index.html')


#ฟังก์ชันสำหรับตรวจสอบล็อกอินว่าซ้ำกับของคนอื่นหรือไม่
def check_email_exist(eml):
    row = Member.objects.filter(email=eml)
    if row.count() == 0:
        return False
    else:
        return True


def member_signup(request):
    #ถ้าส่งอีเมลเข้ามาแบบ AJAX ก็ตรวจสอบว่าซ้ำกับคนอื่นหรือไม่
    if request.is_ajax():
        email = request.GET.get('email', '')
        exist = check_email_exist(email)
        return JsonResponse({'exist':exist})
    
    #ถ้าเปิดเพจนี้หลังจากที่ได้เข้าสู่ระบบแล้ว ให้ไปยังเพจหลักของสมาชิก
    if 'id' in request.session:
        return redirect(reverse('member_home'))

    #ถ้าโพสต์ข้อมูลจากฟอร์มเข้ามา
    err_msg = ''
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            #ถ้าอีเมลไม่ซ้ำ ก็บันทึกข้อมูลลงในฐานข้อมูล
            if not check_email_exist(request.POST['email']):
                r = form.save()

                #หลังการบันทึก ให้เข้าสู่ระบบทันที
                #โดยเก็บข้อมูลบางอย่างไว้ในเซสชัน
                request.session['id'] = r.id
                request.session['name'] = r.firstname   
                return redirect(reverse('member_home'))
            else:
                err_msg = 'อีเมลนี้มีผู้ใช้แล้ว'
        else:
            err_msg = 'ข้อมูลไม่ถูกต้อง'
        
    else:
        form = MemberForm()
        action = reverse('member_signup')

    #ฟังก์ชันและพาธนี้ ใช้สำหรับการรับข้อมูลเพื่อสมัครสมาชิกใหม่
    #ซึ่งเราต้องส่งพาธที่ใช้คู่กับฟังก์ชันนี้ไปยังเท็มเพลต
    #เพื่อกำหนดให้แก่แอตทริบิวต์ action ของฟอร์ม 
    return render(request, 'member-signup.html', {'form':form, 'action':action, 'err_msg':err_msg})


#ต้องใช้ csrf_exampt เพราะเราจะใช้คุกกี้ 
#ร่วมกับการส่งข้อมูลด้วยเมธอด post
@csrf_exempt
def member_signin(request):
    #ถ้าในขณะนั้นได้เข้าสู่ระบบแล้ว 
    #ก็ไปยังเพจหลักของสมาชิกได้ทันที
    if 'id' in request.session:
        return redirect(reverse('member_home'))

    #ถ้าโพสต์ข้อมูลเข้ามา 
    err_msg = None
    if request.method == 'POST':
        form = SigninForm(request.POST)
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        save = request.POST.get('save', False)

        #นำอีเมลและรหัสผ่านไปตรวจสอบว่ามีในฐานข้อมูลหรือไม่
        #ถ้ามี ก็เก็บค่า id และชื่อไว้ในเซสชัน เพื่อบ่งชี้ว่า เข้าสู่ระบบแล้ว
        row = Member.objects.filter(
                Q(email=email) & Q(password=password))

        if row.count() == 1:
            request.session['id'] = row[0].id
            request.session['name'] = row[0].firstname

            #สร้างออบเจ็กต์ HttpResponse เพื่อส่งข้อมูลกลับไปและจัดการคุกกี้
            tmp = loader.get_template('member-home.html')
            data = {'name':row[0].firstname}
            response = HttpResponse(tmp.render(data))

            #ถ้าเลือกบันทึกข้อมูลไว้ในเครื่อง ก็จัดเก็บในแบบคุกกี้ โดยกำหนดอายุ 1 วัน
            #แต่ถ้าไม่เลือก ก็ให้ลบออกจากคุกกี้ (เผื่อจะเก็บไว้ก่อนแล้ว)
            if save:
                age = 60*60*24
                response.set_cookie('email', value=email, max_age=age)
                response.set_cookie('password', value=password, max_age=age)
                response.set_cookie('save', value=save, max_age=age)
            else:
                response.delete_cookie('email')
                response.delete_cookie('password')
                response.delete_cookie('save')

            return response
            
        else:
            err_msg = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง'

    #ถ้าเปิดเพจ และมีข้อมูลจัดเก็บในแบบคุกกี้เอาไว้แล้ว
    #ให้อ่านค่า จากนั้นนำไปเติมเป็นค่าล่วงหน้าให้แก่ฟอร์ม
    elif 'email' in request.COOKIES:
        email = request.COOKIES.get('email', '')
        password = request.COOKIES.get('password', '')
        save = request.COOKIES.get('save', False)
        form = SigninForm(
            initial={'email':email, 'password':password, 'save':save}
        )

    else:
        form = SigninForm()
    
    return render(request, 'member-signin.html', {'form':form, 'err_msg':err_msg})


def member_home(request):
    #ถ้ายังไม่มีค่า id ในเซสชัน แสดงว่ายังไม่เข้าสู่ระบบ
    #ก็ให้ย้ายไปที่เพจ การเข้าสู่ระบบ
    if 'id' not in request.session:
        return redirect(reverse('member_signin'))
    
    id = request.session['id']
    name = request.session['name']

    return render(request, 'member-home.html', {'id':id, 'name':name})


def member_signout(request):
    if 'id' in request.session:
        del request.session['id']
        del request.session['name']
        
    return redirect(reverse('member_signin'))


def member_resign(request):
    if 'id' in request.session:
        id = request.session['id']
        Member.objects.get(id=id).delete()
        del request.session['id']
        del request.session['name']
    
    return redirect(reverse('index'))


def member_update(request):
    #ถ้าส่งข้อมูลเข้ามาแบบ AJAX
    #แสดงว่า ต้องการตรวจสอบอีเมลว่าซ้ำหรือไม่
    #เราสามารถเรียกฟังก์ชันที่สร้างไว้แล้วขึ้นมาใช้งานได้
    if request.is_ajax():
        email = request.GET.get('email', '')
        exist = check_email_exist(email)
        return JsonResponse({'exist':exist})

    #ถ้าเปิดเพจนี้ โดยที่ยังไม่ได้เข้าสู่ระบบ ให้ไปที่เพจเข้าสู่ระบบ
    if 'id' not in request.session:
        return redirect(reverse('member_signin'))
    
    id = request.session['id']

    #ถ้าโพสต์ข้อมูลจากฟอร์มเข้ามา
    #เราก็นำไปอัปเดตหรือแทนที่ข้อมูลเดิมในแถวนั้น
    if request.method == 'POST':
        row = Member.objects.get(id=id)
        form = MemberForm(instance=row, data=request.POST)
        if form.is_valid():
            form.save()

            #เนื่องจากข้อมูลอาจถูกแก้ไข ดังนั้น เราควรอัปเดตค่าในเซสชันใหม่
            request.session['name'] = row.firstname

        #ย้อนกลับไปยังเพจหลักของสมาชิก    
        return redirect(reverse('member_home'))

    #ถ้าเป็นการเปิดเพจเพื่อแก้ไขข้อมูล ให้อ่านข้อมูลเดิมในแถวนั้น
    #แล้วนำไปกำหนดเป็นค่าเริ่มต้นให้กับฟอร์ม
    #ซึ่งสมาชิกสามารถเลือกแก้ไขเฉพาะฟิลด์ที่ต้องการ
    #ส่วนฟิลด์ที่ไม่ได้แก้ไข ก็ยังเป็นค่าเดิม
    else:
        row = Member.objects.get(id=id)
        form = MemberForm(initial=row.__dict__)
        action = reverse('member_update')
        err_msg = ''

        return render(request, 'member-signup.html', {'form': form, 'action':action, 'err_msg':err_msg})
