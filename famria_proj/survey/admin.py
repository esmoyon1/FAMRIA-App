from django.contrib import admin
from .models import Question, Survey, SurveyQuestion, Response, SurveyResponse, UserRole

# Register your models here.
from .models import UserProfile  

@admin.register(UserProfile)  
class UserProfileAdmin(admin.ModelAdmin):  
    list_display = ('user', 'bio', 'phone_number', 'location','role')  
    search_fields = ('user__username', 'bio', 'phone_number')  

admin.site.register(Question)  
admin.site.register(Survey)  
admin.site.register(SurveyQuestion)  
admin.site.register(SurveyResponse)
admin.site.register(Response)
admin.site.register(UserRole)