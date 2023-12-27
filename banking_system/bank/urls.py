from django.urls import path
from . import views
from django.urls import path



urlpatterns=[
    path("",views.index,name="index"),
    path("login/",views.login_view,name="login"),
    path("user/",views.index,name='user'),
    path("logout/",views.logout_view,name="logout"),
    path("register/",views.register_view,name="register"),
    path("account/",views.create_account_view,name="create_account"),
    path("details/",views.account_details_view,name="account_details"),
    path("transactions/",views.transaction_details_view,name="transaction_details"),
    path("transfer/",views.transfer_view,name="transfer_funds"),
    path("transfer/confirm",views.confirm_transfer_view,name="confirm_transfer"),
    path("loan/application",views.submit_loan_application_view,name="submit_loan_application"),
    path("loan/information",views.cus_loan_information,name="cus_loan_information"),
    path("loan/payement",views.loan_payment_view,name="loan_payment"),
    path("employee/login/",views.employee_login_view,name="employee_login"),
    path("employee/logout",views.employee_logout_view,name="employee_logout"),
    path("employee/dashboard",views.employee_index_view,name="employee_dashboard"),
    path("employee/dashboard/deposit",views.deposit_view,name="deposit"),
    path("employee/dashboard/withdrawal",views.withdrawal_view,name="withdrawal"),
    path("employee/dashboard/loan/applications",views.review_loan_applications_view,name="review_loan_applications"),
    path('approve_application/<int:application_id>/', views.approve_application_view, name='approve_application'),
    path('reject_application/<int:application_id>/', views.reject_application_view, name='reject_application'),
    path('employee/dashboard/loan/information',views.loan_information_view,name="loan_information"),
    path('employee/dashboard/freezeAccount',views.account_view,name="view_account"),
    path('freeze_account/<int:account_id>/', views.freeze_account_view, name='freeze_account'),
    path('unfreeze_account/<int:account_id>/', views.unfreeze_account_view, name='unfreeze_account'),
    #path("employee/customers",views.see_customers_view,name="customer_view")

]