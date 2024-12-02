from django.db import models  
from django.contrib.auth.models import User  
from mptt.models import MPTTModel, TreeForeignKey  
from django.core.exceptions import ValidationError  
from django.utils.translation import gettext as _ 

class UserProfile(models.Model):  
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')  
    bio = models.TextField(blank=True, null=True)  
    # profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)  
    phone_number = models.CharField(max_length=15, blank=True, null=True)  
    location = models.CharField(max_length=255, blank=True, null=True)  

    def __str__(self):  
        return f"{self.user.username}'s Profile"  

    class Meta:  
        verbose_name = _("User Profile")  
        verbose_name_plural = _("User Profiles")  
        
    def get_full_name(self):  
        # Combine first name and last name; removes any extra spaces  
        return f"{self.user.first_name} {self.user.last_name}".strip()  

# Signal to create/update a UserProfile automatically when a User is created/updated  
from django.db.models.signals import post_save  
from django.dispatch import receiver  

@receiver(post_save, sender=User)  
def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
        UserProfile.objects.create(user=instance)  

@receiver(post_save, sender=User)  
def save_user_profile(sender, instance, **kwargs):  
    instance.profile.save()

class Question(MPTTModel):  
    SECTOR_CHOICES = [  
        ('general', 'General'),  
        ('environmental', 'Environmental'),  
        ('social', 'Social'),  
        ('economic', 'Economic'),  
        ('physical', 'Physical'),  
    ]  
    
    QUESTION_TYPES = [  
        ('multiple_choice', 'Multiple Choice'),  
        ('multiple_select', 'Multiple Select'),  
        ('text', 'Text'),  
        ('rating', 'Rating'),  
    ]  

    text = models.TextField()  
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='text')  
    options = models.JSONField(blank=True, null=True)  
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES)  
    version = models.PositiveIntegerField(default=1)  
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_questions')  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    user = models.ForeignKey(User, verbose_name=_("Created/Modified by"), on_delete=models.CASCADE, default=1)

    class MPTTMeta:  
        order_insertion_by = ['text']  

    def __str__(self):  
        return self.text  
    
    def clean(self):  
        if not self.text:  
            raise ValidationError('Text field cannot be empty.')  
        if self.question_type not in dict(self.QUESTION_TYPES):  
            raise ValidationError('Invalid question type provided.')  

    @classmethod  
    def active_questions(cls):  
        """Returns all active questions."""  
        return cls.objects.filter(version__gte=1).order_by('created_at')  


class Survey(models.Model): 
    title = models.CharField(max_length=255)  
    description = models.TextField(blank=True, null=True)  
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(_("Status"), default=0, help_text="Set to Zero (0) to stop accepting responses.") # 1=Accepting Responses, 0 = Otherwise

    def __str__(self):  
        return self.title  

    def clean(self):  
        if not self.title:  
            raise ValidationError('Title field cannot be empty.')  
        
    def count_responses(self):  
        return SurveyResponse.objects.filter(survey=self).count()  

class SurveyQuestion(models.Model):  
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)  
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  
    order = models.PositiveIntegerField(default=1)  
    user = models.ForeignKey(User, verbose_name=_("Modified/Added by"), on_delete=models.CASCADE, default=1)

    class Meta:  
        unique_together = ('survey', 'question')  
        ordering = ['order']  

    def __str__(self):  
        return f'{self.question.text} in {self.survey.title}'  

class SurveyResponse(models.Model):  
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)  
    respondent = models.TextField(_("Respondent Name"), null=True, default='Anonymous')
    created_at = models.DateTimeField(auto_now_add=True)  
    # Other fields related to the response...  

    def __str__(self):  
        return f'{self.respondent} in {self.survey.title}'  
    
class Response(models.Model):  
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)  
    respondent = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers', verbose_name=_("Respondent"))  
    answer = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)  

    class Meta:  
        # unique_together = ('survey_question', 'respondent')  
        ordering = ['submitted_at']  

    def __str__(self):  
        return f'Response by {self.respondent} to {self.survey_question.question.text}'  

    def clean(self):  
        if not self.answer:  
            raise ValidationError('Answer field cannot be empty.')  
        
        question_type = self.survey_question.question.question_type  
        
        # Example of type-based validation  
        if question_type == 'multiple_choice' and not self.answer in self.survey_question.question.options.keys():  
            raise ValidationError('Invalid answer: choose a valid option.')
        