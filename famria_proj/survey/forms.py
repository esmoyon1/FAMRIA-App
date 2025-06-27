import json
from django import forms
from .models import Question
from django.contrib.auth.models import User
from .models import UserProfile, UserRole
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
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.all(),
        required=True,
        empty_label=None
    )

    class Meta:  
        model = UserProfile  
        fields = ['bio', 'phone_number', 'location', 'role']  

    first_name = forms.CharField(max_length=30, required=True)  
    last_name = forms.CharField(max_length=30, required=True)

class SurveyForm(forms.ModelForm):  
    class Meta:  
        model = Survey  
        fields = ['title', 'description', 'status']  

class QuestionForm(forms.ModelForm):  
    class Meta:  
        model = Question  
        fields = ['text', 'question_type', 'options', 'sector', 'parent']  

    def __init__(self, *args, **kwargs):  
        super().__init__(*args, **kwargs)  
        if not self.instance.pk or self.instance.options is None:  
            self.fields['options'].initial = '[]'  # Initialize as an empty JSON array  

    def clean_options(self):  
        question_type = self.cleaned_data.get('question_type')  
        options = self.cleaned_data.get('options')  

        # Log the raw options to verify the input  
        print(f"Raw options input: {options}")  # For debugging  

        if question_type == 'multiple_choice':  
            if options is None: # or (isinstance(options, str) and options.strip() == ''):  
                raise ValidationError('You must provide choices for multiple choice questions.')  

            if isinstance(options, list):  
                # If options is already a list, convert it to a JSON string  
                
                print(options)
                return json.dumps(options)  

            # try:  
            #     # Ensure options is treated as a string if it's not a list  
            #     if not isinstance(options, str):  
            #         raise ValidationError('Options must be a JSON string.')  

            #     # Strip leading or trailing spaces  
            #     options = options.strip()  

            #     # Attempt to parse the JSON. Use json.loads to ensure correct format.  
            #     options_list = json.loads(options)  
            #     print(options_list)
            #     # Check if parsed result is a list of strings  
            #     if not isinstance(options_list, list) or not all(isinstance(choice, str) for choice in options_list):  
            #         raise ValidationError('Options must be a JSON array of strings.')  

            #     # Convert list back into JSON string for storage  
            #     return json.dumps(options_list)  

            # except json.JSONDecodeError:  
            #     raise ValidationError('Enter a valid JSON array for options.')  
            # except Exception as e:  # Catch any potential edge cases  
            #     raise ValidationError(f'An error occurred: {str(e)}')  
        
        print(options)
        # print(options_list)
        return options   

class ResponseForm(forms.ModelForm):  
    class Meta:  
        model = Response  
        fields = ['survey_question', 'respondent', 'answer']