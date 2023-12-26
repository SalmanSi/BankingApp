from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import redirect
from django.db import connection
from django.utils import timezone
from django.http import HttpResponse

from . import utils
# Create your views here.

def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request,"bank/user.html")
    

def login_view(request):
    
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request,"bank/login.html",{
                "message":"Invalid credentials."
            })
    return render(request,"bank/login.html")    
        
def logout_view(request):
    logout(request)
    return render(request,"bank/login.html",{
        "message":"Logged Out"
    })

def register_view(request):
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        first_name=request.POST["first_name"]
        last_name=request.POST["last_name"]
        email=request.POST["email"]
        # create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        login(request,user)
        return HttpResponseRedirect(reverse('index'))

    return render(request,"bank/register.html")

def create_account_view(request):

    with connection.cursor() as cursor:
        cursor.execute("select * from branches")
        branches=cursor.fetchall()
        print(branches)
    
    if request.method=="POST":
        B_ID=request.POST["branch"]
        pin=request.POST["pin"]
        
        # Use the authenticated user's username
        username = request.user.username

        # Call the stored procedure
        with connection.cursor() as cursor:
            cursor.callproc('set_Pin_Branch', [username, int(pin), int(B_ID)])
            connection.commit()  # Commit the changes
        return HttpResponseRedirect(reverse('index'))

    return render(request,"bank/create_account.html",{
        'branches':branches
    })


def account_details_view(request):
    status_value='active'
    with connection.cursor() as cursor:
        u_id=request.user.id
        cursor.execute("select account_AccountID from auth_user_has_account where auth_user_id=%s",[u_id])
        a_id=cursor.fetchone()
        cursor.execute("update account set status =%s",[status_value])
        cursor.execute("select * from account where AccountID=%s",[a_id])
        detail=cursor.fetchone() #account details

        
    return render(request,"bank/account_details.html",{
        "detail": detail
    })


def transaction_details_view(request):
    u_id=request.user.id
    recipient_list=[]
    with connection.cursor() as cursor:
        cursor.execute("select account_AccountID from auth_user_has_account where auth_user_id=%s",[u_id])
        a_id=cursor.fetchone()
        cursor.execute("select * from transaction where account_AccountID=%s",[a_id])
        transactions=cursor.fetchall()
        for transaction in transactions:
            recipient_account_id=transaction[6]
            recipient_list.append(utils.get_username_for_valid_aid(recipient_account_id)[0])
        zipped_data = zip(transactions, recipient_list)
    return render(request,'bank/transaction_details.html',{"zipped_data":zipped_data})

def transfer_view(request):
    if request.method=="POST":
        u_id=request.user.id # senders user id
        a_id=utils.get_account_id(u_id)# senders accountID
        amount=int( request.POST["amount"] )
        recipient_account_id=int(request.POST["recipient_account_id"])
        purpose=request.POST["purpose"]
        with connection.cursor() as cursor:
            # find senders account id
            cursor.execute("select account_AccountID from auth_user_has_account where auth_user_id=%s",[u_id])
            sender_account_id=cursor.fetchone()
            
            # check senders balance
            sender_balance=utils.get_balance(sender_account_id)
            print(f"balance:{sender_balance}\n")
            # checking for self transfer
            if recipient_account_id==a_id:
                return render(request,"bank/transfer_funds.html",{"message":"Cant send funds to youself!!"})
            if amount>sender_balance:
                #insufficient balance
                return render(request,"bank/transfer_funds.html",{"message":"Insufficient balance"})
            else:
                with connection.cursor() as inner_cursor:
                    # check if account is valid and get username of recipient
                    recipient_u_name=utils.get_username_for_valid_aid(recipient_account_id)

                    if recipient_u_name[0] is None:
                        return render(request,"bank/transfer_funds.html",{"message":"Invalid Account ID"})
                    # print the name of recipinet and ask user to confirm.
                    # if user confirms, then do the transaction logic
                    return render(request,"bank/transfer_funds.html",{"r_name":recipient_u_name[0],"amount": amount, "recipient_account_id": recipient_account_id, "purpose": purpose})

    return render(request,"bank/transfer_funds.html")


def confirm_transfer_view(request):
    if request.method=="POST":
        u_id=request.user.id # senders user id
        amount=int(request.POST["amount"])
        recipient_account_id=int(request.POST["recipient_account_id"])
        purpose=request.POST["purpose"]
        a_id=utils.get_account_id(u_id) # senders account ID

        with connection.cursor() as cursor:
            #deduct from sender
            sender_balance=utils.get_balance(a_id)
            cursor.execute('update account set Balance =%s where AccountID=%s',[sender_balance-amount,a_id])
            #add to recievers balance
            recipient_balance=utils.get_balance(recipient_account_id)
            cursor.execute('update account set Balance =%s where AccountID=%s',[recipient_balance+amount,recipient_account_id])
            cursor.execute('insert into transaction(account_AccountID,Amount,Type,RecipientID,Purpose) values (%s,%s,%s,%s,%s)',[a_id,amount,"account To account",recipient_account_id,purpose])
        return render(request,"bank/transfer_funds.html",{"message":"Transaction Sucessful"})
    


def submit_loan_application_view(request):
    if request.method=="POST":
        amount=int(request.POST.get("loan_amount"))
        proof_of_income=request.FILES.get("income_proof")
        description=request.POST.get("additional_info")
        u_id=request.user.id 
        a_id=utils.get_account_id(u_id)  
        with connection.cursor() as cursor:
            #add application 
            cursor.execute('insert into loan_applications(Amount,account_AccountID,files,description) values(%s,%s,%s,%s)',[amount,a_id,proof_of_income,description]) 
            return render(request,"bank/submit_loan_application.html",{"message":"Loan Applied"})
    return render(request,"bank/submit_loan_application.html")

# employee funtionality

def employee_login_view(request):
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        with connection.cursor() as cursor:
            cursor.execute('select is_staff from auth_user where username= %s',[username])
            is_staff=cursor.fetchone()
            if not is_staff[0]:
                 return render(request,"bank/employee/employee_login.html",{
                "message":"Invalid credentials."
            })
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return HttpResponseRedirect(reverse('employee_dashboard'))
        else:
            return render(request,"bank/employee_login.html",{
                "message":"Invalid credentials."
            })
    return render(request,"bank/employee/employee_login.html")

def employee_logout_view(request):
    logout(request)
    return render(request,"bank/employee/employee_login.html",{
        "message":"Logged Out"
    })

def employee_index_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('employee_login'))
    return render(request,"bank/employee/employee_dashboard.html")

def deposit_view(request):
    if request.method=="POST":
        recipient_a_id=int(request.POST["recipientAccountID"])
        sender_account_id=int(request.POST["senderAccountID"])
        amount=int(request.POST["depositAmount"])
        Purpose=request.POST["purpose"]

        #check if valid accounts
        with connection.cursor() as cursor:
            cursor.execute('select * from account where AccountID = %s or AccountID=%s',[sender_account_id,recipient_a_id])
            accounts=cursor.fetchall()
            if len(accounts)>1:
                cursor.execute('UPDATE account SET balance = balance + %s WHERE AccountID = %s',[amount,recipient_a_id])
                return HttpResponseRedirect(reverse('employee_dashboard'))
            else:
                return render(request,"bank/employee/deposit.html",{"message":"Invalid Account Numbers"})
    return render(request,"bank/employee/deposit.html")

def withdrawal_view(request):
    if request.method=="POST":
        a_id=int(request.POST["accountNumber"])
        pin=int(request.POST["pin"])
        withdrawal_amount=int(request.POST["withdrawalAmount"])
        with connection.cursor() as cursor:
            cursor.execute('select AccountPin,Balance from Account where AccountID= %s',[a_id])
            result=cursor.fetchone()
            r_pin=result[0]
            balance=result[1]
            if result is None:
                message="Invalid Account Number"
                return render(request,"bank/employee/withdrawal.html",{"message":message})
            else:#valid account
                if pin != r_pin:#wrong pin
                    message="Invalid Account Pin"
                    return render(request,"bank/employee/withdrawal.html",{"message":message})
                else:
                    if withdrawal_amount>balance:
                        message="Insufficient Account Balance"
                        return render(request,"bank/employee/withdrawal.html",{"message":message})
                    else:
                        cursor.execute('update account set Balance=%s where AccountId=%s',[balance-withdrawal_amount,a_id])
                        message="Withdrawal sucess"
                        return render(request,"bank/employee/withdrawal.html",{"message":message})
    return render(request,"bank/employee/withdrawal.html")


def review_loan_applications_view(request):
    with connection.cursor() as cursor:
        cursor.execute('select * from loan_applications where status=%s',["pending"])
        applications=cursor.fetchall()
        print(applications)
    return render(request,"bank/employee/loan_applications.html",{"applications":applications})


def approve_application_view(request, application_id):
     with connection.cursor() as cursor:   

        # Perform the approval logic (modify this as needed)
        query = "UPDATE loan_applications SET status=%s WHERE application_id = %s"
        cursor.execute(query, ("approved",application_id,))

        return HttpResponseRedirect(reverse('review_loan_applications'))


def reject_application_view(request, application_id):
        with connection.cursor() as cursor:

            # Perform the rejection logic (modify this as needed)
            query = "UPDATE loan_applications SET status=%s WHERE application_id = %s"
            cursor.execute(query, ("rejected",application_id,))

        return HttpResponseRedirect(reverse('review_loan_applications'))



