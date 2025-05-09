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
    u_id = request.user.id
    recipient_list_sent = []
    recipient_list_received = []
    a_id = utils.get_account_id(u_id)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM transaction WHERE account_AccountID = %s OR RecipientID = %s", [a_id, a_id])
        transactions = cursor.fetchall()

        for transaction in transactions:
            recipient_account_id = transaction[6]
            recipient_username = utils.get_username_for_valid_aid(recipient_account_id)[0]

            if transaction[1] == a_id:
                # Sent transaction
                recipient_list_sent.append((transaction, recipient_username))
            elif recipient_account_id == a_id:
                # Received transaction
                recipient_list_received.append((transaction, recipient_username))

    return render(request, 'bank/transaction_details.html', {
        "recipient_list_sent": recipient_list_sent,
        "recipient_list_received": recipient_list_received,
    })


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
        description=request.POST.get("additional_info")
        rdate=request.POST.get("returnDate")
        u_id=request.user.id 
        a_id=utils.get_account_id(u_id)  
        with connection.cursor() as cursor:
            cursor.execute('select * from loan_applications where account_AccountID=%s and status=%s',[a_id,"pending"])
            applications=cursor.fetchone()
            if applications is not None:# already applied and pending
                message="Already pending application, Cant Apply more"
                print(applications)
                return render(request,"bank/submit_loan_application.html",{"message":message})
            else:
                #add application 
                cursor.execute('insert into loan_applications(Amount,account_AccountID,description,ReturnDate) values(%s,%s,%s,%s)',[amount,a_id,description,rdate]) 
                return render(request,"bank/submit_loan_application.html",{"message":"Loan Applied Sucessfully"})

            
    return render(request,"bank/submit_loan_application.html")

def cus_loan_information(request):
    u_id=request.user.id
    a_id=utils.get_account_id(u_id)
    with connection.cursor() as cursor:
        cursor.execute('select * from loans where account_AccountID=%s',[a_id])
        loans=cursor.fetchall()
        return render(request,"bank/loan_information.html",{"loans":loans})



def loan_payment_view(request):
    if request.method=="POST":
        u_id=request.user.id
        a_id=utils.get_account_id(u_id)
        l_id=request.POST["loanId"]
        amount_to_pay=int(request.POST["amount"])
        with connection.cursor() as cursor:
            cursor.execute('select amount from loans where amount >%s and account_AccountID=%s and loanID=%s',[0,a_id,l_id])
            loan=cursor.fetchone()
            if loan is not None and loan[0] >0: # loan exist for that user
                balance=utils.get_balance(a_id)
                if balance<amount_to_pay:
                    return render(request,"bank/loan_payment.html",{"message":"Insufficient Balance"})
                else:
                    loan_amount=loan[0]
                    if amount_to_pay>loan_amount:
                        amount_to_pay=loan_amount
                    #start
                    balance=balance-amount_to_pay   
                    loan_amount-=amount_to_pay
                    cursor.execute('update account set Balance=%s where AccountID=%s',[balance,a_id])
                    cursor.execute('update loans set Amount =%s where loanID=%s',[loan_amount,l_id])      

                    return render(request,"bank/loan_payment.html",{"message":"Loan Payment Sucessful"})
            else:
                message="Loan does not exist"
                return render(request,"bank/loan_payment.html",{"message":message})

    return render(request,"bank/loan_payment.html")
# employee funtionality

def employee_login_view(request):
    if request.method=="POST":
        print("request received")
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
        # get account id from application id
        cursor.execute('select account_AccountID from loan_applications where application_id=%s',[application_id])
        a_id=cursor.fetchone()[0]
        #get loan amount
        cursor.execute('select Amount from loan_applications where application_id=%s',[application_id])
        loan_amount=cursor.fetchone()[0]       
        # Perform the approval logic (modify this as needed)
        query = "UPDATE loan_applications SET status=%s WHERE application_id = %s"
        cursor.execute(query, ("approved",application_id,))
        #old balance
        cursor.execute('select Balance from account where AccountID=%s ',[a_id])
        balance=cursor.fetchone()[0]
        #add balance    
        cursor.execute('update account set Balance=%s where AccountID=%s',[balance+loan_amount,a_id])
        return HttpResponseRedirect(reverse('review_loan_applications'))


def reject_application_view(request, application_id):
        with connection.cursor() as cursor:

            # Perform the rejection logic (modify this as needed)
            query = "UPDATE loan_applications SET status=%s WHERE application_id = %s"
            cursor.execute(query, ("rejected",application_id,))

        return HttpResponseRedirect(reverse('review_loan_applications'))


def loan_information_view(request):

    with connection.cursor() as cursor:
        cursor.execute('select * from loans')
        loans=cursor.fetchall()
    return render(request,"bank/employee/loan_information.html",{"loans":loans})



def account_view(request):
            
    with connection.cursor() as cursor:
        cursor.execute('select * from account_view')
        results=cursor.fetchall()
    return render(request,"bank/employee/freeze_account.html",{"result":results})

def freeze_account_view(request,account_id):
    if request.method=="POST":
        with connection.cursor() as cursor:
            cursor.execute('update account set Status =%s where AccountID=%s',["inactive",account_id])
            
    with connection.cursor() as cursor:
        cursor.execute('select * from account_view')
        results=cursor.fetchall()
    return render(request,"bank/employee/freeze_account.html",{"result":results})

def unfreeze_account_view(request,account_id):
    if request.method=="POST":
        with connection.cursor() as cursor:
            cursor.execute('update account set Status =%s where AccountID=%s',["active",account_id])
            
    with connection.cursor() as cursor:
        cursor.execute('select * from account_view')
        results=cursor.fetchall()
    return render(request,"bank/employee/freeze_account.html",{"result":results})