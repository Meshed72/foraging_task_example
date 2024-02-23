"""
URL configuration for foraging_task project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from foraging_task.views import foraging_task, report_task_data, oci_questionnaire, dass_questionnaire, aaq_questionnaire, welcome_screen, finish_screen, foraging_task_preview

urlpatterns = [    
    path('', welcome_screen, name='welcome_screen'),
    path('foraging_task_preview', foraging_task_preview, name='foraging_task_preview'),
    path('oci_questionnaire', oci_questionnaire, name='oci_questionnaire'),
    path('dass_questionnaire', dass_questionnaire, name='dass_questionnaire'),
    path('aaq_questionnaire', aaq_questionnaire, name='aaq_questionnaire'),
    path('foraging_task', foraging_task, name='foraging_task'),
    path('report_task_data', report_task_data, name='report_task_data'),
    path('finish_screen', finish_screen, name='finish_screen'),
]
