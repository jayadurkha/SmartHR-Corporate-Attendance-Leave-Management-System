from django.contrib import admin
from django.urls import path, include
from employees.views import dashboard
from employees import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name="dashboard"),
    path('accounts/', include('django.contrib.auth.urls')),  
    path("leave-request/", views.leave_request, name="leave_request"),
    path("manage-leaves/", views.manage_leaves, name="manage_leaves"),
    path("leave-action/<int:leave_id>/<str:action>/",views.update_leave_status,name="update_leave_status"),



]
