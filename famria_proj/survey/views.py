from django.shortcuts import render, redirect, get_object_or_404  
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout  
from django.contrib import messages
from .decorators import role_required, has_permission
from django.contrib.auth.forms import UserCreationForm
from django.views import View  
from django.views.decorators.http import require_POST  
from django.core.files.storage import FileSystemStorage  
from django.core.exceptions import ValidationError 
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.db.models import Count, Prefetch
import csv, json  
from .models import * #Survey, Question, Response, SurveyQuestion, SurveyResponse
from .forms import * #QuestionForm, S xxxxurveyForm
from dotenv import load_dotenv
import os

load_dotenv()
from openai import OpenAI
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key= os.getenv("OPENAI_API_KEY") 
)
import openai
# Create your views here.

@login_required
@role_required(['admin', 'staff'])
def register(request):
    # Check if the current user is an admin
    if not request.user.is_superuser:
        messages.error(request, 'Only administrators can register new users.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            # Store the current admin user
            admin_user = request.user
            
            # Create the new user
            user = form.save()
            
            # Delete existing profile if it exists
            UserProfile.objects.filter(user=user).delete()
            
            # Create new profile
            profile = profile_form.save(commit=False)
            profile.user = user
            
            # Set default role as respondent if not specified
            if not profile.role:
                profile.role = UserRole.objects.get(name='respondent')
            profile.save()
            
            # Don't log in the new user, keep admin logged in
            messages.success(
                request,
                f'User {user.username} has been successfully created with role: {profile.role.name}'
            )
            # Clear the forms for a new registration
            form = UserCreationForm()
            profile_form = UserProfileForm(initial={'role': UserRole.objects.get(name='respondent')})
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
        profile_form = UserProfileForm(initial={'role': UserRole.objects.get(name='respondent')})
    
    return render(request, 'user/register.html', {
        'form': form,
        'profile_form': profile_form,
        'title': 'Register New User'
    })

@login_required  
def profile(request):  
    user_profile = get_object_or_404(UserProfile, user=request.user)  
    return render(request, 'user/profile.html', {'profile': user_profile})  

@login_required  
def edit_profile(request):  
    # Check if admin is editing another user's profile
    user_id = request.GET.get('user_id')
    if user_id and request.user.is_superuser:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST':  
        user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)  
        if user_form.is_valid():  
            # Save the User info (first_name, last_name)  
            user.first_name = user_form.cleaned_data.get('first_name')  
            user.last_name = user_form.cleaned_data.get('last_name')  
            user.save()  
            # Save the User Profile info (bio, phone_number, location)  
            user_profile.bio = user_form.cleaned_data.get('bio')  
            user_profile.phone_number = user_form.cleaned_data.get('phone_number')  
            user_profile.location = user_form.cleaned_data.get('location')  
            if request.user.is_superuser:  # Only admin can change roles
                user_profile.role = user_form.cleaned_data.get('role')
            user_profile.save()  
            
            messages.success(request, 'Profile updated successfully!')
            if request.user.is_superuser and user_id:  # If admin editing another user
                return redirect('users-list')
            return redirect('profile')  # Redirect to the profile page after saving  
    else:  
        user_form = UserProfileForm(initial={  
            'bio': user_profile.bio,  
            'phone_number': user_profile.phone_number,  
            'location': user_profile.location,  
            'first_name': request.user.first_name,  
            'last_name': request.user.last_name,  
        })  
  
    return render(request, 'user/edit_profile.html', {'form': user_form})  

def user_login(request):  
    if request.method == 'POST':  
        username = request.POST['username']  
        password = request.POST['password']  
        user = authenticate(request, username=username, password=password)  
        if user is not None:  
            login(request, user)  
            return redirect('profile')  # Redirect to the profile page  
        else:  
            # Invalid login  
            return render(request, 'user/login.html', {'error': 'Invalid credentials'})  
    return render(request, 'user/login.html')  

def user_logout(request):  
    logout(request)  
    return redirect('login')  # Redirect to the login page 

@login_required
@role_required(['admin'])
def users_list(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        if action == 'delete' and user_id:
            user = get_object_or_404(User, id=user_id)
            if not user.is_superuser:  # Prevent deletion of superusers
                user.delete()
                messages.success(request, 'User deleted successfully!')
            else:
                messages.error(request, 'Cannot delete superuser accounts!')
        return redirect('users-list')
    
    users = User.objects.all() #filter(is_superuser=False)  # Exclude superusers from the list
    return render(request, 'user/users_list.html', {'users': users})  

def dashboard(request):  
    
    surveys = Survey.objects.all()  
    # Prepare a list to hold survey data along with question and response counts  
    survey_data = []  
    
    responses_count = SurveyResponse.objects.count() 
    for survey in surveys:  
        # Count the number of questions associated with the survey  
        question_count = survey.surveyquestion_set.count()  
        
        # Count the number of responses related to the questions in this survey  
        response_count = survey.count_responses() 
        
        survey_data.append({  
            'survey': survey,  
            'question_count': question_count,  
            'response_count': response_count,  
        }) 
    
    return render(request, 'dashboard.html', {'survey_data': survey_data, 'responses_count': responses_count})  
    
    # return render(request, 'dashboard.html')  

theprompt = "give me list of sci-fi moview related to cyber-security"
# @login_required
# @role_required(['admin', 'staff', 'enumerator', 'respondent'])
def survey_list(request):  
    surveys = Survey.objects.all()  
    # response = client.responses.create(
    #     model="gpt-4.1",
    #     input=theprompt #"Write a one-sentence bedtime story about a pink cow."

    # )

    # print(response.output_text)
    # Prepare a list to hold survey data along with question and response counts  
    survey_data = []  
    
    responses_count = SurveyResponse.objects.count() 
    for survey in surveys:  
        # Count the number of questions associated with the survey  
        question_count = survey.surveyquestion_set.count()  
        
        # Count the number of responses related to the questions in this survey  
        response_count = survey.count_responses() 
        
        survey_data.append({  
            'survey': survey,  
            'question_count': question_count,  
            'response_count': response_count,  
            # 'chatresponses': response.output_text,
        }) 
     
    
    return render(request, 'surveys/survey_list.html', {'survey_data': survey_data, 'responses_count': responses_count})  
    # return render(request, 'surveys/survey_list.html', {'surveys': surveys})

# Create a new survey 
@login_required
@role_required(['admin', 'staff'])
def survey_create(request):  
    if request.method == 'POST':  
        form = SurveyForm(request.POST)  
        if form.is_valid():  
            form.save()  
            messages.success(request, 'Survey created successfully!')
            return redirect('survey-list')  
    else:  
        form = SurveyForm()  
    return render(request, 'surveys/survey_form.html', {'form': form})  

@login_required
@role_required(['admin', 'staff', 'enumerator'])
def survey_detail(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
        
    if request.method == "POST":  
        if 'add_question' in request.POST:  
            question_id = request.POST.get('question_id')  
            question = get_object_or_404(Question, id=question_id)  
            SurveyQuestion.objects.get_or_create(survey=survey, question=question)  
        elif 'remove_question' in request.POST:  
            question_id = request.POST.get('question_id')  
            question = get_object_or_404(Question, id=question_id)  
            SurveyQuestion.objects.filter(survey=survey, question=question).delete()  
    
    # questions = Question.active_questions()  
    assigned_questions = survey.surveyquestion_set.all() 
    questions = Question.objects.exclude(id__in=assigned_questions.values_list('question_id', flat=True))

    # Count questions and responses  
    question_count = assigned_questions.count()  
    # response_count = Response.objects.filter(survey_question__survey=survey).count()  # Adjust if your Response model is different  
    response_count = survey.count_responses()
    # # Count responses grouped by respondent  
    # response_count = (  
    #     Response.objects.filter(survey_question__survey=survey)  
    #     .values('user')  
    #     .annotate(response_count=Count('id'))  
    #     .order_by('user')  
    # )  
    return render(request, 'surveys/survey_detail.html', {  
        'survey': survey,  
        'questions': questions,  
        'assigned_questions': assigned_questions,  
        'question_count': question_count,  
        'response_count': response_count,  
    })

# @login_required
# @role_required(['admin', 'staff', 'enumerator', 'respondent'])
def survey_response(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    assigned_questions = survey.surveyquestion_set.all()  

    if request.method == "POST":  
        respondent_name = request.POST.get('respondent_name', 'Anonymous')  
        if assigned_questions:  
            survey_response = SurveyResponse.objects.create(survey=survey, respondent=respondent_name)  
            for sq in assigned_questions:  
                answer = request.POST.getlist(str(sq.id))  # Use getlist for multi-select  
                if answer:  
                    # Join answers if they are multiple choices  
                    for ans in answer:  
                        Response.objects.create(  
                            survey_question=sq,  
                            respondent=survey_response,  
                            answer=ans  
                        )  
        
        return redirect('survey-thanks')    # Redirect to a thank you page or result page  

    # Prepare questions and load options  
    for sq in assigned_questions:  
        # Parse the options from JSON  
        options = sq.question.options  # Get the options field directly  
        if options:  # Ensure options is not None or empty  
            try:  
                # Attempt to load the JSON; try to clean string if necessary  
                if isinstance(options, str):  # Check if it's stored as a string  
                    options = json.loads(options)  # Try to parse it as JSON  
                
                # If options is still a string after parsing, attempt to parse it again  
                if isinstance(options, str):  
                    options = json.loads(options.replace("\\\"", "\""))  # Clean up escaped quotes  

            except (json.JSONDecodeError, TypeError) as e:  
                options = []  # Set to an empty list if there's an error  

        else:  
            options = []  # If options is null, set to an empty list  
        
        sq.question.options = options  # Update question object with valid options      

    return render(request, 'surveys/survey_response_form.html', {  
        'survey': survey,  
        'assigned_questions': assigned_questions,  
    })  

@login_required
@role_required(['admin', 'staff', 'enumerator'])
def survey_responses(request, survey_id=None):  
    # Get all SurveyResponse instances or filter by the specific survey  
    if survey_id:  
        survey_responses = SurveyResponse.objects.filter(survey__id=survey_id).prefetch_related('answers')  
        survey = Survey.objects.get(id=survey_id)  # Get the specific survey  
    else:  
        survey_responses = SurveyResponse.objects.all().prefetch_related('answers')  
        survey = None  # No specific survey  

    return render(request, 'surveys/survey_responses.html', {  
        'survey_responses': survey_responses,  
        'survey': survey,  
    })  

@login_required
@role_required(['admin', 'staff'])
def survey_response_detail(request, id):  
    survey_response = get_object_or_404(SurveyResponse, id=id)  
    return render(request, 'surveys/survey_response_detail.html', {  
        'survey_response': survey_response,  
    })   

def survey_thanks(request):  
    return render(request, 'surveys/survey_thanks.html')  

@login_required
@role_required(['admin', 'staff'])
def survey_analytics(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    
    # Get all responses for the survey  
    responses = SurveyResponse.objects.filter(survey=survey)  
    
    # Get all questions for this survey  
    survey_questions = SurveyQuestion.objects.filter(survey=survey)  

    # Initialize filtering variable  
    selected_question = request.GET.get('question')  
    # print(selected_question)
    if selected_question:  
        # Filter responses based on selected question  
        responses = responses.filter(answers__survey_question__id=selected_question)  
    
    # Prepare analytics data  
    analytics_data = {  
        'total_responses': responses.count(),  
        'questions': [],  # 'gpt_analysis': generated_output  # Include the generated analysis from GPT  
    }  
    for survey_question in survey.surveyquestion_set.all():  
        question_data = {  
            'question': survey_question.question.text,  
            'responses': {},  
            'response_count': 0  
        }  
        
        # Gather responses for each question  
        for response in responses:  
            try:  
                answer = Response.objects.get(survey_question=survey_question, respondent=response)  
                question_data['responses'][answer.answer] = question_data['responses'].get(answer.answer, 0) + 1  
                question_data['response_count'] += 1  
            except Response.DoesNotExist:  
                continue  
        
        analytics_data['questions'].append(question_data)  
    # print(analytics_data)
    # Prepare the prompt for the API  
    prompt = f"""  
    You are an expert data and language analyst. You are provided with a collection of open-ended survey responses written in both English and Tagalog.

    Your task is to analyze the responses and generate a clear, structured summary that includes:
    - Identification of recurring themes and key insights across responses.
    - Sentiment analysis (e.g., strongly positive, neutral, concerns, etc.).
    - Relevant statistical patterns, estimates, and comparative highlights.
    - A concise executive summary of key findings for stakeholders.
    - Use Markdown formatting with appropriate headings, bullet points, and tables for easy presentation and readability.

    Survey Title: {survey.title}
    Description: {survey.description}
    Survey Responses: {analytics_data} 
    """  
    # print("Prompt:---: ", prompt)
    try: 
        response = client.responses.create(
            model="gpt-4.1",
            input= prompt#"Write a one-sentence bedtime story about a pink cow."
        )

        print(dir(response))
        generated_output = response.output[0].content[0].text
        # generated_output = "This is the AI generated Response"

    # except openai.error.OpenAIError as e:  # Ensure that OpenAIError is available  
    #     generated_output = f"Error communicating with OpenAI: {str(e)}"  
    except Exception as e:  # Catch other unexpected errors  
        generated_output = f"An unexpected error occurred: {str(e)}"  
    
    # print("ChatGPT Response: ", generated_output)

    analytics_data.setdefault('gpt_analysis', []).append(generated_output)

    #### Deep Seek Starts Here #####
    # for backward compatibility, you can still use `https://api.deepseek.com/v1` as `base_url`.
    # client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")

    # response = client.chat.completions.create(
    #     model="deepseek-chat",
    #     messages=[
    #         {"role": "system", "content": prompt},
    #         {"role": "user", "content": "Hello"},
    # ],
    #     max_tokens=1024,
    #     temperature=0.7,
    #     stream=False
    # )
    # deepSeek = response.choices[0].message.content
    # print("DeepSeek Response: ", deepSeek )

    #### Deep Seek Ends Here #####
    import markdown

    if isinstance(analytics_data.get("gpt_analysis"), list):
        analysis_raw = analytics_data["gpt_analysis"][0]
    else:
        analysis_raw = analytics_data["gpt_analysis"]
    
    # Convert markdown to HTML
    analytics_data["gpt_analysis"] = markdown.markdown(analysis_raw)
    print(analytics_data)
    context = {  
        'survey': survey,  
        'analytics_data': analytics_data,  
        'survey_questions': survey_questions,  
        'selected_question': selected_question,  
        # 'deepSeek': deepSeek,  
    }  
    return render(request, 'surveys/survey_analytics.html', context)  

# Update an existing question  
@login_required
@role_required(['admin', 'staff', 'enumerator'])
def survey_update(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    if request.method == 'POST':  
        form = SurveyForm(request.POST, instance=survey)  
        if form.is_valid():  
            form.save()  
            messages.success(request, 'Survey updated successfully!')
            return redirect('survey-list')  
    else:  
        form = SurveyForm(instance=survey)  
    return render(request, 'surveys/survey_form.html', {'form': form})  

@login_required
@role_required(['admin', 'staff', 'enumerator'])
def edit_profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=request.user.profile)
    return render(request, 'user/edit_profile.html', {'profile_form': profile_form})  

# Delete a Survey  
@login_required
@role_required(['admin', 'staff'])
def survey_delete(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    if request.method == 'POST':  
        survey.delete()  
        messages.success(request, 'Survey deleted successfully!')
        return redirect('survey-list')  
    return render(request, 'surveys/survey_confirm_delete.html', {'survey': survey})

@require_POST
@role_required(['admin', 'staff'])
def reorder_questions(request, survey_id):  
    order = request.POST.getlist('order[]')  # This will give you an ordered list of the question IDs  
    
    for index, question_id in enumerate(order):  
        SurveyQuestion.objects.filter(id=question_id).update(order=index)  
        
    return JsonResponse({'status': 'success'})  # Return a JSON response

@login_required
@role_required(['admin', 'staff'])
def import_questions(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  

    if request.method == 'POST' and request.FILES['csv_file']:  
        csv_file = request.FILES['csv_file']  
        
        # Read the CSV file  
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()  
        reader = csv.DictReader(decoded_file)  

        for row in reader:  
            question_text = row['text']  
            question_type = row['question_type']  
            sector = row['sector']  
            options = row['options']  

            # Print for debugging purposes (you may want to remove these later)  
            print(f"Row: {row}")  # Debugging line  
            print(f"Options before JSON decode: '{options}'")  # Debugging line  

            # Handle the options parsing safely  
            options_data = None  
            if options:  
                try:  
                    options_data = json.loads(options)  
                except json.JSONDecodeError as e:  
                    print(f"JSON decode error: {e}")  # For debugging  
                    return HttpResponseBadRequest(f"Invalid options format for question '{question_text}': {options}")  

            try:  
                # Check and add the Question  
                question, created = Question.objects.get_or_create(  
                    text=question_text,  
                    question_type=question_type,  
                    sector=sector,  
                    defaults={'options': options_data, 'user': request.user}  
                )  

                # Create SurveyQuestion instance  
                SurveyQuestion.objects.get_or_create(survey=survey, question=question, user=request.user)  

            except ValidationError as e:  
                print(f"Validation error: {e}")  # For debugging  
                return HttpResponseBadRequest(f"Validation error: {str(e)}")  

        return redirect('survey-detail', survey_id=survey.id)  

    return HttpResponseBadRequest("Invalid request method.", status=400)

@login_required  
@role_required(['admin', 'staff'])
def import_responses(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  

    if request.method == 'POST' and request.FILES['csv_file']:  
        csv_file = request.FILES['csv_file']  
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()  
        reader = csv.DictReader(decoded_file)  

        for row in reader:  
            respondent_name = row['respondent']  

            # Create or get the SurveyResponse for the respondent  
            survey_response = SurveyResponse.objects.create(  
                survey=survey,  
                respondent=respondent_name  
            )  

            for question_column, answer in row.items():  
                if question_column == 'respondent':  
                    continue  # Skip the respondent column  
                
                # Replace blank answers with "N/A"  
                if not answer.strip():  # Check if answer is blank  
                    answer = "None"  
                try:  
                    # Fetch the corresponding SurveyQuestion  
                    survey_question = get_object_or_404(SurveyQuestion, survey=survey, id=question_column) #survey_question_id, question__text=question_column)  

                    # Create the Response  
                    response = Response(  
                        survey_question=survey_question,  
                        respondent=survey_response,  
                        answer=answer
                    )  
                    response.clean()  # Validate the response  
                    response.save()  # Save it to the database  

                except ValidationError as e:  
                    return HttpResponseBadRequest(f"Validation error for respondent '{respondent_name}': {str(e)}")  
                except Exception as e:  
                    return HttpResponseBadRequest(f"An error occurred: {str(e)}")  

        return redirect('survey-detail', survey_id=survey.id)  

    return HttpResponseBadRequest("Invalid request method.", status=400)

# Create a new question  
@login_required
@role_required(['admin', 'staff'])
def create_question(request):  
    if request.method == 'POST':  
        form = QuestionForm(request.POST)  
        if form.is_valid():  
            form.save()  
            messages.success(request, 'Question created successfully!')
            return redirect('question-list')  
    else:  
        form = QuestionForm()  
    return render(request, 'questions/question_form.html', {'form': form})  
 
class QuestionImportView(View):  
    def get(self, request):  
        return render(request, 'questions/import_questions.html')  

    def post(self, request):  
        if request.method == 'POST' and request.FILES['csv_file']:  
            csv_file = request.FILES['csv_file']  
            fs = FileSystemStorage()  
            filename = fs.save(csv_file.name, csv_file)  
            file_path = fs.url(filename)  # You can change how you handle the path.  
            
            # file_path = "C:\\Moyon\Dev\\FAMRIA App\\famria_proj\\survey\\physical.csv"
            
            # Import logic here  
            try:
                print(filename)
                print(file_path)
                print(csv_file)
                with open(file_path, 'r', encoding='utf-8-sig') as csv_file:  
                    reader = csv.DictReader(csv_file)  
                    
                    print(reader)
                    for row in reader: 
                        print(row) 
                        print(row['sector']) 
                        # Prepare data for the Question model  
                        question_text = row['question_text']  
                        question_type = row['question_type']  
                        options = row['options']  
                        sector = row['sector']  
                        version = int(row['version'])  
                        # parent_id = row['parent'].strip() or None  

                        options_data = json.loads(options) if options else None  

                        # parent = None  
                        # if parent_id:  
                        #     parent_id = int(parent_id)  
                        #     try:  
                        #         parent = Question.objects.get(id=parent_id)  
                        #     except Question.DoesNotExist:  
                        #         continue  # or handle as needed  

                        Question.objects.create(  
                            text=question_text,  
                            question_type=question_type,  
                            options=options_data,  
                            sector=sector,  
                            version=version
                            # parent=parent  
                        )  
                    
                    return redirect('question-list')  # Redirect after import  

            except Exception as e:  
                return HttpResponse(f"An error occurred: {str(e)}")  

        return render(request, 'questions/import_questions.html')  

# Read (list) all questions  
@login_required
@role_required(['admin', 'staff', 'enumerator'])
def question_list(request):  
    questions = Question.objects.prefetch_related(
        Prefetch(
            'surveyquestion_set',
            queryset=SurveyQuestion.objects.select_related('survey'),
            to_attr='related_surveys'
        )
    )  

    return render(request, 'questions/question_list.html', {'questions': questions})  

# Update an existing question  
@login_required
@role_required(['admin', 'staff'])
def update_question(request, question_id):  
    question = get_object_or_404(Question, id=question_id)  
    if request.method == 'POST':  
        form = QuestionForm(request.POST, instance=question)  
        if form.is_valid():  
            form.save()  
            messages.success(request, 'Question updated successfully!')  
            return redirect('question-list')  
    else:  
        form = QuestionForm(instance=question)  
    return render(request, 'questions/question_form.html', {'form': form})  

# Delete a question  
@login_required
@role_required(['admin', 'staff'])
def delete_question(request, question_id):  
    question = get_object_or_404(Question, id=question_id)  
    if request.method == 'POST':  
        question.delete()  
        messages.success(request, 'Question deleted successfully!')
        return redirect('question-list')  
    return render(request, 'questions/question_confirm_delete.html', {'question': question})

