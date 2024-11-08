from django.shortcuts import render, redirect, get_object_or_404  
from django.contrib.auth.decorators import login_required
from .models import Survey, Question, Response, SurveyQuestion, SurveyResponse
from .forms import QuestionForm, SurveyForm
from django.contrib import messages
from django.db.models import Count  
from django.views import View  
from django.core.files.storage import FileSystemStorage  
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
import csv  
import json  
from django.core.exceptions import ValidationError 
from django.views.decorators.http import require_POST  

# Create your views here.

def dashboard(request):  
    return render(request, 'dashboard.html')  

def survey_list(request):  
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
     
    
    return render(request, 'surveys/survey_list.html', {'survey_data': survey_data, 'responses_count': responses_count})  
    # return render(request, 'surveys/survey_list.html', {'surveys': surveys})

# Create a new survey  
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

def survey_response(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    assigned_questions = survey.surveyquestion_set.all()  

    if request.method == "POST":  
        # Get respondent's name, default to 'Anonymous' if not provided  
        respondent_name = request.POST.get('respondent_name', 'Anonymous')  
        if assigned_questions:
            # Create and save SurveyResponse instance  
            survey_response = SurveyResponse.objects.create(survey=survey, respondent=respondent_name)  

        # Iterate over assigned questions and save individual responses  
        for sq in assigned_questions:  
            answer = request.POST.get(str(sq.id))  
            if answer:  
                Response.objects.create(  
                    survey_question=sq,  
                    respondent=survey_response,  # Link to the SurveyResponse instance  
                    answer=answer  
                )   
        
        return redirect('survey-thanks')  # Redirect to a thank you page or result page  

    return render(request, 'surveys/survey_response_form.html', {  
        'survey': survey,  
        'assigned_questions': assigned_questions,  
    })  

def OLD_survey_response(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    assigned_questions = survey.surveyquestion_set.all()  

    if request.method == "POST":  
        for sq in assigned_questions:  
            answer = request.POST.get(str(sq.id))  
            if answer:  
                Response.objects.create(  
                    survey_question=sq,  
                    # user=request.user,  
                    answer=answer  
                ) 
        # SurveyResponse.objects.create() 
        return redirect('survey-thanks')  # Redirect to thank you page or result page  

    return render(request, 'surveys/survey_response_form.html', {  
        'survey': survey,  
        'assigned_questions': assigned_questions,  
    })

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

    
def survey_response_detail(request, id):  
    survey_response = get_object_or_404(SurveyResponse, id=id)  
    return render(request, 'surveys/survey_response_detail.html', {  
        'survey_response': survey_response,  
    })   

def oldsurvey_responses(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    responses = SurveyResponse.objects.filter(survey_question__survey=survey).select_related('survey_question')  

    return render(request, 'surveys/survey_responses.html', {  
        'survey': survey,  
        'responses': responses,  
    })  

def survey_thanks(request):  
    return render(request, 'surveys/survey_thanks.html')  

# Update an existing question  
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

# Delete a Survey  
def survey_delete(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  
    if request.method == 'POST':  
        survey.delete()  
        messages.success(request, 'Survey deleted successfully!')
        return redirect('survey-list')  
    return render(request, 'surveys/survey_confirm_delete.html', {'survey': survey})

@require_POST  
def reorder_questions(request, survey_id):  
    order = request.POST.getlist('order[]')  # This will give you an ordered list of the question IDs  
    
    for index, question_id in enumerate(order):  
        SurveyQuestion.objects.filter(id=question_id).update(order=index)  
        
    return JsonResponse({'status': 'success'})  # Return a JSON response

@login_required
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

def Oldimport_responses(request, survey_id):  
    survey = get_object_or_404(Survey, id=survey_id)  

    if request.method == 'POST' and request.FILES['csv_file']:  
        csv_file = request.FILES['csv_file']  
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()  
        reader = csv.DictReader(decoded_file)  

        for row in reader:  
            respondent_name = row['respondent']  
            survey_question_id = row['survey_question_id']  
            answer = row['answer']  

            # Create or get the SurveyResponse  
            survey_response, created = SurveyResponse.objects.get_or_create(  
                survey=survey,  
                respondent=respondent_name  
            )  

            try:  
                # Get the SurveyQuestion using the provided ID  
                survey_question = get_object_or_404(SurveyQuestion, id=survey_question_id, survey=survey)  

                # Create the Response  
                response = Response(  
                    survey_question=survey_question,  
                    respondent=survey_response,  
                    answer=answer  
                )  
                response.clean()  # Call the clean method to validate the response  
                response.save()  # Save the response to the database  

            except ValidationError as e:  
                return HttpResponseBadRequest(f"Validation error for respondent '{respondent_name}': {str(e)}")  
            except Exception as e:  
                return HttpResponseBadRequest(f"An error occurred: {str(e)}")  

        return redirect('survey-detail', survey_id=survey.id)  

    return HttpResponseBadRequest("Invalid request method.", status=400) 

# Create a new question  
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
            
            file_path = "C:\\Moyon\Dev\\FAMRIA App\\famria_proj\\survey\\physical.csv"
            
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
def question_list(request):  
    questions = Question.objects.all().order_by('id')  
    return render(request, 'questions/question_list.html', {'questions': questions})  

# Update an existing question  
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
def delete_question(request, question_id):  
    question = get_object_or_404(Question, id=question_id)  
    if request.method == 'POST':  
        question.delete()  
        messages.success(request, 'Question deleted successfully!')
        return redirect('question-list')  
    return render(request, 'questions/question_confirm_delete.html', {'question': question})

