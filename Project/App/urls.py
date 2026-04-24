"""
URL configuration for Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .views import home,index, RegisterView,logout_view,compiler_page,run_compiler,coding_round, run_compiler_ajax
from .import views

urlpatterns = [
    path('', home, name='users-home'),
    path('profile/', views.home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile1/', views.profile, name='users-profile'),
    path('chatbot/', views.chatbot_response_view,name='chatbot'),
    path('logout_view/',logout_view,name='logout_view'),
    
    


    path('jobs/', views.job_list, name='job-list'),
    path('jobs/<int:job_id>/start/', views.start_interview, name='start-interview'),
    path('candidate/<int:candidate_id>/upload/', views.upload_resume, name='upload_resume'),
    path('candidate/<int:candidate_id>/analyze/', views.analyze_resume, name='analyze_resume'),
    path("candidate/<int:candidate_id>/submit-aptitude/",views.submit_aptitude,name="submit_aptitude"),
    
     path("candidate/<int:candidate_id>/aptitude/", views.start_aptitude, name="start_aptitude"),
     path("candidate/<int:candidate_id>/final-feedback/",views.final_feedback,name="final_feedback"),
   
    path("candidate/<int:candidate_id>/compiler/", compiler_page, name="compiler_page"),
    path("run-compiler/", run_compiler, name="run_compiler"),
    path("candidate/<int:candidate_id>/coding/", coding_round, name="coding_round"),
    path("run-compiler-ajax/", run_compiler_ajax, name="run_compiler_ajax"),
    path("coding-result/<int:candidate_id>/", views.coding_result, name="coding_result"),
    path("technical-hr/<int:candidate_id>/", views.technical_hr, name="technical_hr"),
    path("submit-technical-hr/<int:candidate_id>/", views.submit_technical_hr, name="submit_technical_hr"),
    path("final-hr/<int:candidate_id>/", views.final_hr, name="final_hr"),
    path("hr-failed/<int:candidate_id>/", views.hr_failed, name="hr_failed"),
    path('submit-final-hr/<int:candidate_id>/', views.submit_final_hr, name='submit_final_hr'),


   














    
    path('admin-register/', views.admin_register, name='admin-register'),
    path('admin-login/', views.admin_login, name='admin-login'),
    path('admin-logout/', views.admin_logout, name='admin-logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin-dashboard/job/<int:job_id>/candidates/', views.view_candidates, name='view-candidates'),
    path('admin/post-job/', views.post_job, name='post-job'),

]
