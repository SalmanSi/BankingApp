
from django.db import connection

def get_account_id(u_id):
    with connection.cursor() as cursor:
        # find senders account id
        cursor.execute("select account_AccountID from auth_user_has_account where auth_user_id=%s",[u_id])
        sender_account_id=cursor.fetchone()
        return sender_account_id[0]
    
def get_balance(a_id):
    # check senders balance
    with connection.cursor() as cursor:
        cursor.execute("select Balance from account where AccountID=%s",[a_id])
        sender_balance=cursor.fetchone()
        sender_balance=int(sender_balance[0])
        return sender_balance
    
def get_username_for_valid_aid(a_id):
    with connection.cursor() as inner_cursor:
        # Call the stored procedure with the OUT parameter variable
        inner_cursor.execute('set @u_name = NULL')
        inner_cursor.execute('call valid_AccountID(%s , @u_name)', [a_id])
        # Fetch value
        inner_cursor.execute('select @u_name')
        recipient_u_name=inner_cursor.fetchone()
        return recipient_u_name
    


    '''
        # # with connection.cursor() as cursor:
    # #     cursor.execute('insert into auth_user (password,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)',['salman123',0,"Siddiq Khan","Siddiq","Khan","admin@gmail.com",1,1,timezone.now()])
    # user = User.objects.create_user(
    #     username="Faareh Ahmed",
    #     password="salman123",
    #     first_name="Faareh",
    #     last_name="Ahmed",
    #     email="fahmed@gmail.com"
    # )
    # login(request,user)
    '''