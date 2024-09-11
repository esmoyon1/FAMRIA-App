from django.db import models  
from django.contrib.auth.models import User  
from mptt.models import MPTTModel, TreeForeignKey  

class Question(MPTTModel):  
    SECTOR_CHOICES = [  
        ('environmental', 'Environmental'),  
        ('social', 'Social'),  
        ('economic', 'Economic'),  
        ('physical', 'Physical'),  
    ]  
    
    QUESTION_TYPES = [  
        ('multiple_choice', 'Multiple Choice'),  
        ('text', 'Text'),  
        ('rating', 'Rating'),  
    ]  

    text = models.TextField()  
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)  
    options = models.JSONField(blank=True, null=True)  
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES)  
    version = models.PositiveIntegerField(default=1)  
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_questions')  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  

    class MPTTMeta:  
        order_insertion_by = ['text']  

    def __str__(self):  
        return self.text  


class Survey(models.Model):  
    title = models.CharField(max_length=255)  
    description = models.TextField(blank=True, null=True)  
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):  
        return self.title  


class SurveyQuestion(models.Model):  
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)  
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  
    order = models.PositiveIntegerField()  

    class Meta:  
        unique_together = ('survey', 'question')  
        ordering = ['order']  

    def __str__(self):  
        return f'{self.question.text} in {self.survey.title}'  


class Response(models.Model):  
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)  
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    answer = models.TextField()  
    submitted_at = models.DateTimeField(auto_now_add=True)  

    class Meta:  
        unique_together = ('survey_question', 'user')  
        ordering = ['submitted_at']  

    def __str__(self):  
        return f'Response by {self.user.username} to {self.survey_question.question.text}'