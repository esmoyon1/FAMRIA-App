from django.contrib import admin
from .models import Question, Survey, SurveyQuestion, Response, SurveyResponse

# Register your models here.

admin.site.register(Question)  
admin.site.register(Survey)  
admin.site.register(SurveyQuestion)  
admin.site.register(SurveyResponse)
admin.site.register(Response)