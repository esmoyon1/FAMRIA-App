from django import forms
from .models import Question
from crispy_forms.helper import FormHelper  
from crispy_forms.layout import Submit  

# class QuestionForm(forms.ModelForm):
#     class Meta:
#         model = Question
#         fields = ('text', 'question_type', 'options', 'sector')
#         help_texts = {
#             'text': 'Enter the question text',
#             'question_type': 'Select the question type',
#             'options': 'Enter the question options (if applicable)',
#             'sector': 'Select the sector',
#         }
#         widgets = {
#             'options': forms.Textarea(attrs={'rows': 4}),
#         }

#     save_as_new_version = forms.BooleanField(label='Save as new version', required=False, help_text='Check to save as a new version of the question')

#     def __init__(self, *args, **kwargs):  
#         super().__init__(*args, **kwargs)  
#         self.helper = FormHelper()  
#         self.helper.form_method = 'post'  
#         self.helper.add_input(Submit('submit', 'Save'))  

from django import forms  
from .models import * #Survey, Question, Response  

class UserProfileForm(forms.ModelForm):  
    first_name = forms.CharField(max_length=30, required=True)  
    last_name = forms.CharField(max_length=30, required=True)
    class Meta:  
        model = UserProfile  
        fields = ['bio', 'phone_number', 'location']  

class SurveyForm(forms.ModelForm):  
    class Meta:  
        model = Survey  
        fields = ['title', 'description']  

class QuestionForm(forms.ModelForm):  
    class Meta:  
        model = Question  
        fields = ['text', 'question_type', 'options', 'sector', 'parent']  

    # Override the __init__ method to change the options field based on question type  
    def __init__(self, *args, **kwargs):  
        super().__init__(*args, **kwargs)  
        # Initial options field is rendered as JSON if it's not already in the instance  
        if not self.instance.pk or self.instance.options is None:  
            self.fields['options'].initial = {}  

    # Add clean method to validate options based on the question type  
    def clean_options(self):  
        question_type = self.cleaned_data.get('question_type')  
        options = self.cleaned_data.get('options')  

        if question_type == 'multiple_choice':  
            if not options or not isinstance(options, dict) or 'choices' not in options:  
                raise forms.ValidationError('You must provide choices for multiple choice questions.')  

        # You can add more validation for different question types here...  
        
        return options   

class ResponseForm(forms.ModelForm):  
    class Meta:  
        model = Response  
        fields = ['survey_question', 'respondent', 'answer']