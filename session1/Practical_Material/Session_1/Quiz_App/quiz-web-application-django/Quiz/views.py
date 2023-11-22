from django.shortcuts import redirect,render
from django.contrib.auth import login,logout,authenticate
from .forms import *
from .models import *
from django.http import HttpResponse

# Create your views here.
def home(request):

    answer = "Wrong. Try asking H-UWE questions abot themselves..."

    if request.method == 'POST':
        submitted_answer = request.POST["answer"]
        questions=QuesModel.objects.all()
        score=0
        wrong=0
        correct=0
        total=0
        for q in questions:
            total+=1
            print(q.question)
            print(submitted_answer)
            
            if submitted_answer == q.answer_1 or submitted_answer == q.answer_2 or submitted_answer == q.answer_3:
                answer = "Correct!"
                score += 10
                
            if submitted_answer == "Kane9" or submitted_answer == "SkyNet" or submitted_answer == "Tay":
                answer = "You're getting close! Remember they might have changed parts of the word or combined it with something else"
                score += 5
                
        context = {
            'score':score,
            'answer':answer,
        }
        return render(request,'Quiz/result.html',context)
    else:
        questions=QuesModel.objects.all()
        context = {
            'questions':questions
        }
        return render(request,'Quiz/home.html',context)

def addQuestion(request):    
    if request.user.is_staff:
        form=addQuestionform()
        if(request.method=='POST'):
            form=addQuestionform(request.POST)
            if(form.is_valid()):
                form.save()
                return redirect('/')
        context={'form':form}
        return render(request,'Quiz/addQuestion.html',context)
    else: 
        return redirect('home') 

def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home') 
    else: 
        form=createuserform()
        if request.method=='POST':
            form=createuserform(request.POST)
            if form.is_valid() :
                user=form.save()
                return redirect('login')
        context={
            'form':form,
        }
        return render(request,'Quiz/register.html',context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
       if request.method=="POST":
        username=request.POST.get('username')
        password=request.POST.get('password')
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
       context={}
       return render(request,'Quiz/login.html',context)

def logoutPage(request):
    logout(request)
    return redirect('/')

