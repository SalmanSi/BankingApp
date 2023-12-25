from django.urls import path
from . import views
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
]