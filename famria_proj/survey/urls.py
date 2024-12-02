from django.urls import path  
from .views import * 
from . import views

urlpatterns = [  
    path('', dashboard, name='dashboard'),  # Set dashboard as the landing page 
    path('surveys/', survey_list, name='survey-list'),  # Survey list URL 
    path('surveys/create/', survey_create, name='survey-create'),  # Create a question  
    path('surveys/<int:survey_id>/', survey_detail, name='survey-detail'),  # Survey detail URL 
    path('survey/<int:survey_id>/answer/', survey_response, name='survey-response'),  # Answer the questions in the survey
    path('survey/thanks/', survey_thanks, name='survey-thanks'),  # Surevy Complete Page
    path('survey/<int:survey_id>/analytics/', survey_analytics, name='survey-analytics'),  # Surevy Complete Page
    # path('survey/<int:survey_id>/responses/', survey_responses, name='survey-responses'),
    
    path('surveys/responses/', survey_responses, name='survey-responses'),  
    path('surveys/responses/<int:id>', survey_response_detail, name='survey-response-detail'),  
    path('surveys/<int:survey_id>/responses/', survey_responses, name='survey-specific-responses'),  

    path('surveys/update/<int:survey_id>/', survey_update, name='survey-update'),  # Update a question  
    path('surveys/delete/<int:survey_id>/', survey_delete, name='survey-delete'),  # Delete a question  
    path('surveys/<int:survey_id>/reorder-questions/', reorder_questions, name='reorder-questions'), 
    path('surveys/<int:survey_id>/import-questions/', import_questions, name='import-questions'),  
    path('surveys/<int:survey_id>/import-responses/', import_responses, name='import-responses'),  
    
    path('questions/', question_list, name='question-list'),  # List all questions  
    path('questions/import/', QuestionImportView.as_view(), name='question-import'), 
    path('questions/create/', create_question, name='create-question'),  # Create a question  
    path('questions/update/<int:question_id>/', update_question, name='update-question'),  # Update a question  
    path('questions/delete/<int:question_id>/', delete_question, name='delete-question'),  # Delete a question  

    path('users/', users_list, name='users-list'),  
    path('register/', register, name='register'),  
    path('profile/', profile, name='profile'),  
    path('profile/edit/', edit_profile, name='edit_profile'),  
    path('accounts/login/', user_login, name='login'),  
    path('logout/', user_logout, name='logout'), 
]  