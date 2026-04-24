from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import logout as auth_logout
import numpy as np
import joblib
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
import base64
from io import BytesIO
import seaborn as sns

import matplotlib.pyplot as plt
from django.http import JsonResponse

from django.shortcuts import render
import numpy as np




def home(request):
    return render(request, 'users/home.html')

@login_required(login_url='users-register')


def index(request):
    return render(request, 'app/index.html')

class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        # will redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to='/')

        # else process dispatch as it otherwise normally would
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')

            return redirect(to='login')

        return render(request, self.template_name, {'form': form})


# Class based view that extends from the built in login view to add a remember me functionality

class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('users-home')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')

from .models import Profile

def profile(request):
    user = request.user
    # Ensure the user has a profile
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect(to='users-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})



from django.shortcuts import render
from django.http import JsonResponse
# import random
# import json
import numpy as np
# from nltk.tokenize import word_tokenize
# from nltk.stem import WordNetLemmatizer
#from .models import Response, models
from Chatbot.processor import chatbot_response
# Remove the comments to download additional nltk packages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@require_POST
@csrf_exempt
def chatbot_response_view(request):
    if request.method == 'POST':
        the_question = request.POST.get('question', '')

        response = chatbot_response(the_question)
        print(response)

        return JsonResponse({"response": response})
    else:
        
        return JsonResponse({"message": "This endpoint only accepts POST requests."})
 

def logout_view(request):  
    auth_logout(request)
    return redirect('/')




# user Portal 

from django.shortcuts import render
from .models import Job

def job_list(request):
    # Fetch all jobs (latest first)
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'app/job_list.html', {'jobs': jobs})



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Job, Candidate
from .forms import CandidateForm, ResumeForm
import google.generativeai as genai


def start_interview(request, job_id):
    job = Job.objects.get(id=job_id)

    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Check if candidate already exists for this job
            if Candidate.objects.filter(job=job, email=email).exists():
                messages.error(request, "You have already attended this interview.")
                return redirect('job-list')

            candidate = form.save(commit=False)
            candidate.job = job
            candidate.save()
            return redirect('upload_resume', candidate_id=candidate.id)
    else:
        form = CandidateForm()

    return render(request, 'app/start_interview.html', {'form': form, 'job': job})

























    
from django.shortcuts import render, redirect, get_object_or_404
from .models import Candidate
from .forms import ResumeForm

def upload_resume(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES, instance=candidate)

        if form.is_valid():
            candidate.ats_score = None  # Reset old analysis
            candidate.skills = ""
            candidate.recommendation = ""
            candidate.improvement = ""
            form.save()

            return redirect("analyze_resume", candidate_id=candidate.id)

    else:
        form = ResumeForm(instance=candidate)

    return render(request, "app/upload_resume.html", {
        "form": form,
        "candidate": candidate
    })


from django.shortcuts import render, get_object_or_404
from .models import Candidate
import PyPDF2, json, re
from google import genai
from google.api_core.exceptions import ResourceExhausted

# ==========================
# GEMINI CLIENT
# ==========================
client = genai.Client(
    api_key="AIzaSyDAAb3kod7p1hsPzYwfXql1k7U6Pwj0Ydc"
)

# ==========================
# RESUME TEXT EXTRACTION
# ==========================
def extract_text_from_resume(file_path, max_chars=6000):
    text = ""
    try:
        reader = PyPDF2.PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print("PDF ERROR:", e)
        return ""
    return text.strip()[:max_chars]

# ==========================
# SAFE GEMINI RESPONSE PARSING
# ==========================
def extract_json_safe(response):
    """
    Convert Gemini response to a dict safely.
    Handles:
      - dict (full JSON)
      - list of dicts (take first)
      - list of strings (treat as skills)
      - string (parse JSON)
    """
    if isinstance(response, dict):
        return response

    if isinstance(response, list):
        if len(response) > 0 and isinstance(response[0], dict):
            return response[0]
        # Assume list of skills
        return {
            "ats_score": 0,
            "skills": response,
            "recommendation": "Unable to determine recommendation",
            "improvement": "Use ATS-friendly resume format"
        }

    if isinstance(response, str):
        # Try direct JSON parse
        try:
            data = json.loads(response)
            return extract_json_safe(data)  # recursive parse
        except:
            pass
        # Regex fallback
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                data = json.loads(match.group(0))
                return extract_json_safe(data)
            except:
                pass

    # Default fallback
    return {
        "ats_score": 0,
        "skills": [],
        "recommendation": "Use ATS-friendly resume format",
        "improvement": "Upload a readable text-based PDF resume"
    }

# ==========================
# ANALYZE RESUME VIEW
# ==========================
def analyze_resume(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    job = candidate.job

    # Already analyzed
    if candidate.ats_score is not None:
        if candidate.ats_score >= 60:
            return render(request, "app/analysis_success.html", {"candidate": candidate})
        return render(request, "app/analysis_feedback.html", {"candidate": candidate})

    # Extract resume text
    resume_text = extract_text_from_resume(candidate.resume.path)
    if len(resume_text.strip()) < 100:
        candidate.ats_score = 0
        candidate.recommendation = "Invalid resume"
        candidate.improvement = "Upload a readable text-based PDF resume"
        candidate.save()
        return render(request, "app/analysis_feedback.html", {"candidate": candidate})

    # Gemini prompt
    prompt = f"""
STRICT RULES:
- Return ONLY valid JSON
- Do NOT add explanation
- ats_score must be NUMBER (0-100)

Job Title:
{job.title}

Job Description:
{job.description}

Resume:
{resume_text}

RETURN JSON FORMAT:
{{
  "ats_score": 75,
  "skills": ["Python", "Django", "REST"],
  "recommendation": "Proceed to aptitude",
  "improvement": "Add measurable project outcomes"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # ==========================
        # SAFE PARSING
        # ==========================
        analysis = extract_json_safe(response.text)
        print("Parsed Analysis:", analysis)  # Debug

        # ATS score
        ats_raw = analysis.get("ats_score", 0)
        try:
            ats = int(float(ats_raw))
        except:
            ats = 0
        candidate.ats_score = max(0, min(ats, 100))

        # Skills
        candidate.skills = ", ".join(analysis.get("skills", []))

        # Recommendation & Improvement
        candidate.recommendation = analysis.get(
            "recommendation",
            "Use ATS-friendly resume format"
        )
        candidate.improvement = analysis.get(
            "improvement",
            "Upload a readable text-based PDF resume"
        )

        candidate.save()

    except ResourceExhausted:
        candidate.ats_score = 0
        candidate.recommendation = "API quota exceeded"
        candidate.improvement = "Try again after some time"
        candidate.save()

    except Exception as e:
        print("ANALYSIS ERROR:", e)
        candidate.ats_score = 0
        candidate.recommendation = "Resume analysis failed"
        candidate.improvement = "Use ATS-friendly resume format"
        candidate.save()

    # Result page
    if candidate.ats_score >= 60:
        return render(request, "app/analysis_success.html", {"candidate": candidate})

    return render(request, "app/analysis_feedback.html", {"candidate": candidate})















def extract_json(text):
    if not text:
        return None

    text = text.strip()

    # Try direct JSON
    try:
        return json.loads(text)
    except:
        pass

    # Match JSON array
    array_match = re.search(r"\[[\s\S]*\]", text)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except:
            pass

    # Match JSON object
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except:
            pass

    return None
import random

DEFAULT_QUESTIONS = [

    {
        "question": "What is the next number in the series: 2, 6, 12, 20, ?",
        "options": ["30", "28", "32", "24"],
        "answer": "30"
    },
    {
        "question": "If a train travels 60 km in 1 hour, how far will it travel in 30 minutes?",
        "options": ["15 km", "20 km", "25 km", "30 km"],
        "answer": "30 km"
    },
    {
        "question": "If A can complete a work in 10 days and B in 20 days, how many days together?",
        "options": ["6.67", "7.5", "5", "10"],
        "answer": "6.67"
    },
    {
        "question": "What is the average of first 10 natural numbers?",
        "options": ["4.5", "5", "5.5", "6"],
        "answer": "5.5"
    },
    {
        "question": "If the cost price is ₹200 and selling price is ₹250, what is the profit %?",
        "options": ["20%", "25%", "30%", "15%"],
        "answer": "25%"
    },

    {
        "question": "Which data structure uses FIFO principle?",
        "options": ["Stack", "Queue", "Tree", "Graph"],
        "answer": "Queue"
    },
    {
        "question": "Which keyword is used to define a function in Python?",
        "options": ["function", "def", "func", "define"],
        "answer": "def"
    },
    {
        "question": "What does HTTP stand for?",
        "options": [
            "HyperText Transfer Protocol",
            "High Transfer Text Protocol",
            "Hyper Transfer Text Process",
            "Host Transfer Protocol"
        ],
        "answer": "HyperText Transfer Protocol"
    },
    {
        "question": "Which SQL command is used to remove all records from a table?",
        "options": ["DELETE", "REMOVE", "TRUNCATE", "DROP"],
        "answer": "TRUNCATE"
    },
    {
        "question": "Which symbol is used for comments in Python?",
        "options": ["//", "/* */", "#", "<!-- -->"],
        "answer": "#"
    },

    # ---------- MORE MIXED ----------
    {
        "question": "Time complexity of binary search?",
        "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "answer": "O(log n)"
    },
    {
        "question": "Which is NOT a valid Python data type?",
        "options": ["list", "tuple", "map", "array"],
        "answer": "array"
    },
    {
        "question": "What is 15% of 200?",
        "options": ["25", "30", "35", "40"],
        "answer": "30"
    },
    {
        "question": "Which method is used to add an element to a list?",
        "options": ["add()", "insert()", "append()", "push()"],
        "answer": "append()"
    },
    {
        "question": "Which protocol is used for secure web communication?",
        "options": ["HTTP", "FTP", "HTTPS", "SMTP"],
        "answer": "HTTPS"
    },
    {
        "question": "If x + y = 10 and x = 4, what is y?",
        "options": ["4", "5", "6", "10"],
        "answer": "6"
    },
    {
        "question": "Which loop is guaranteed to execute at least once?",
        "options": ["for", "while", "do-while", "foreach"],
        "answer": "do-while"
    },
    {
        "question": "Which language is primarily used for Django?",
        "options": ["Java", "PHP", "Python", "C#"],
        "answer": "Python"
    },
    {
        "question": "Which operator is used for exponentiation in Python?",
        "options": ["^", "**", "//", "%"],
        "answer": "**"
    },
    {
        "question": "Which sorting algorithm is fastest on average?",
        "options": ["Bubble Sort", "Insertion Sort", "Quick Sort", "Selection Sort"],
        "answer": "Quick Sort"
    },
]


def start_aptitude(request, candidate_id):
    candidate = Candidate.objects.get(id=candidate_id)
    job = candidate.job

    if candidate.ats_score < 60:
        return redirect("analyze_resume", candidate_id=candidate.id)

    skills = candidate.skills or "general aptitude"

    prompt = f"""
Return ONLY valid JSON array.

Generate 20 aptitude MCQs.

Job: {job.title}
Skills: {skills}

FORMAT:
[
  {{
    "question": "string",
    "options": ["A","B","C","D"],
    "answer": "A"
  }}
]
"""

    questions = []

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        questions = extract_json(response.text)

        if not isinstance(questions, list) or len(questions) < 20:
            raise ValueError("Invalid Gemini response")

    except Exception as e:
        print("⚠️ GEMINI FAILED, USING DEFAULT QUESTIONS:", e)

        # ✅ SHUFFLE & PICK 20 DEFAULT QUESTIONS
        shuffled = DEFAULT_QUESTIONS.copy()
        random.shuffle(shuffled)
        questions = shuffled[:20]

    # ✅ STORE IN SESSION
    request.session["aptitude_questions"] = questions

    return render(
        request,
        "app/aptitude_test.html",
        {
            "candidate": candidate,
            "questions": questions,
        }
    )



from django.views.decorators.csrf import csrf_exempt
from .models import InterviewResult


@csrf_exempt
def submit_aptitude(request, candidate_id):
    candidate = Candidate.objects.get(id=candidate_id)

    if request.method == "POST":

        questions = request.session.get("aptitude_questions", [])
        correct = 0

        for i, q in enumerate(questions):
            user_answer = request.POST.get(f"q{i}")

            correct_option_letter = q.get("answer")  # "A", "B", "C", "D"
            options = q.get("options", [])

            # Convert letter → index
            index_map = {"A": 0, "B": 1, "C": 2, "D": 3}

            if correct_option_letter in index_map:
                correct_option_text = options[index_map[correct_option_letter]]

                if user_answer == correct_option_text:
                    correct += 1

        aptitude_score = int((correct / len(questions)) * 100) if questions else 0

        status = "Coding Round" if aptitude_score >= 0 else "Rejected"

        InterviewResult.objects.update_or_create(
            candidate=candidate,
            defaults={
                "ats_score": candidate.ats_score,
                "aptitude_score": aptitude_score,
                "status": status,
            }
        )

        request.session.pop("aptitude_questions", None)

        return redirect("final_feedback", candidate_id=candidate.id)



from django.shortcuts import render, redirect, get_object_or_404
from .models import Candidate, InterviewResult
def final_feedback(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    result = InterviewResult.objects.filter(candidate=candidate).first()

    return render(
        request,
        "app/apptitude_feedback.html",
        {
            "candidate": candidate,
            "result": result,
        }
    )















# views.py
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# JDOODLE_CLIENT_ID = "1ccaa61767f01e35930f686a541e89c9"
# JDOODLE_CLIENT_SECRET = "76a545bce91e201a99e5c542ba6953233688c0bce0cba043592044a43e7d2f25"


from django.shortcuts import render, get_object_or_404
from .models import Candidate

def compiler_page(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    return render(request, "app/compiler.html", {"candidate": candidate})



@csrf_exempt
def run_compiler(request):
    if request.method == "POST":
        code = request.POST.get("code", "")
        input_data = request.POST.get("input", "")

        url = "https://api.jdoodle.com/v1/execute"

        payload = {
            "clientId": JDOODLE_CLIENT_ID,
            "clientSecret": JDOODLE_CLIENT_SECRET,
            "script": code,
            "language": "python3",
            "versionIndex": "4",
            "stdin": input_data
        }

        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        return JsonResponse({
            "output": result.get("output", ""),
            "error": result.get("error", ""),
        })











import json
import requests
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Candidate

# JDoodle API keys
JDOODLE_CLIENT_ID = "f992a01b19449cfa00321a26e2a1be60"
JDOODLE_CLIENT_SECRET = "ddefbc927332570e5db3b5d855e5af4d03270f4abe8a6aef90ee1a5a06e94fcf"

# ------------------------
# Coding Round Page
# ------------------------
def coding_round(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    # Two questions with multiple test cases
    questions = [
        {
            "id": 1,
            "title": "Reverse a String",
            "description": "Read a string and print its reverse.",
            "test_cases": [
                {"input": "hello", "output": "olleh"},
                {"input": "ai", "output": "ia"},
                {"input": "django", "output": "ognajd"},
            ]
        },
        {
            "id": 2,
            "title": "Sum of Even Numbers",
            "description": "Read N and print sum of even numbers from 1 to N.",
            "test_cases": [
                {"input": "10", "output": "30"},
                {"input": "6", "output": "12"},
                {"input": "1", "output": "0"},
            ]
        }
    ]

    return render(request, "app/multi_question.html", {
        "candidate": candidate,
        "questions": questions
    })


# ------------------------
# JDoodle Execution Function
# ------------------------
def run_code_jdoodle(code, input_data):
    url = "https://api.jdoodle.com/v1/execute"
    payload = {
        "clientId": JDOODLE_CLIENT_ID,
        "clientSecret": JDOODLE_CLIENT_SECRET,
        "script": code,
        "language": "python3",
        "versionIndex": "4",
        "stdin": input_data
    }
    response = requests.post(url, json=payload, timeout=10)
    return response.json()





import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .views import run_code_jdoodle  # your JDoodle execution function

@csrf_exempt
def run_compiler_ajax(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid method"}, status=400)

        data = json.loads(request.body.decode('utf-8'))
        code = data.get("code", "")
        test_cases = data.get("test_cases", [])
        expected_outputs = data.get("expected_outputs", [])

        results = []
        passed_count = 0

        for idx, tc in enumerate(test_cases):
            jd_result = run_code_jdoodle(code, tc)

            # Safe extraction with defaults
            output = jd_result.get("output")
            if output is None:
                output = ""
            else:
                output = output.strip()

            error = jd_result.get("error")
            if error is None:
                error = ""
            else:
                error = error.strip()

            # Determine what to show in output
            if error:
                result_output = error
                passed = False
            else:
                result_output = output
                passed = output == expected_outputs[idx]
                if passed:
                    passed_count += 1

            results.append({
                "input": tc,
                "expected": expected_outputs[idx],
                "output": result_output,
                "passed": passed
            })

        return JsonResponse({
            "results": results,
            "passed_count": passed_count,
            "total": len(test_cases)
        })

    except Exception as e:
        # Catch any unexpected exception and return as JSON
        return JsonResponse({"error": str(e)}, status=500)

from django.shortcuts import render, redirect, get_object_or_404
from .models import Candidate

def coding_result(request, candidate_id):
    """
    Show candidate result percentage.
    If >= 50%, allow proceed to Technical HR
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)

    # Ensure percentage comes as GET param
    percentage = request.GET.get("percentage")
    if percentage is None:
        return redirect("/")  # safety fallback

    try:
        percentage = int(percentage)
    except ValueError:
        percentage = 0  # fallback if invalid input

    # Proceed if >=50%
    proceed = percentage >= 50

    return render(request, "app/coding_result.html", {
        "candidate": candidate,
        "percentage": percentage,
        "proceed": proceed
    })




from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Candidate
import google.generativeai as genai
import os

# ==================================================
# GEMINI 2.5 API KEY
# ==================================================
GEMINI_API_KEY = "AIzaSyAR9tkcxx2bH9YO6r28LaZanNGM0bJpLGs"
genai.configure(api_key=GEMINI_API_KEY)


# ==================================================
# Read resume text
# ==================================================
def get_resume_text(candidate):
    """
    Read candidate resume text from file if exists,
    fallback to skills/recommendation/improvement fields.
    """
    if candidate.resume:
        try:
            path = candidate.resume.path
            ext = os.path.splitext(path)[1].lower()
            text = ""
            if ext in ['.txt']:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            # Add PDF reader logic if needed
            return text.strip()
        except Exception:
            pass
    # fallback
    fallback_text = "Skills: {}\nRecommendation: {}\nImprovement: {}".format(
        candidate.skills, candidate.recommendation, candidate.improvement
    )
    return fallback_text


# ==================================================
# Generate Technical Questions from Resume
# ==================================================
def generate_questions_from_resume(resume_text):
    prompt = f"""
You are a senior technical interviewer.

Based on the following resume, generate exactly 3 technical interview questions.
Questions must be strictly based on skills, projects, and experience.
Do not add explanations.
Return only a numbered list.

Resume:
{resume_text}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        questions = []
        if response and response.text:
            for line in response.text.split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    questions.append(line.split(".", 1)[1].strip())

        if len(questions) < 3:
            raise Exception("Incomplete AI response")

        return questions[:3]

    except Exception:
        # fallback questions
        return [
            "Explain a major technical project from your resume.",
            "What technical challenges have you faced in your experience?",
            "Which technologies are you strongest in and why?"
        ]


# ==================================================
# Technical HR Round
# ==================================================
def technical_hr(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    resume_text = get_resume_text(candidate)
    questions = generate_questions_from_resume(resume_text)

    request.session["technical_hr_questions"] = questions
    request.session["candidate_id"] = candidate.id

    return render(request, "app/technical_hr.html", {
        "candidate": candidate,
        "questions": questions,
        "total_questions": len(questions)
    })


# ==================================================
# Submit Technical HR Round
# ==================================================
def submit_technical_hr(request, candidate_id):
    if request.method == "POST":
        total_questions = int(request.POST.get("total_questions", 0))
        answered = int(request.POST.get("answered", 0))

        percentage = (answered / total_questions) * 100 if total_questions else 0
        percentage = round(percentage, 2)

        request.session["technical_hr_percentage"] = percentage

        if percentage >= 0:
            return redirect("final_hr", candidate_id=candidate_id)
        else:
            return redirect("hr_failed", candidate_id=candidate_id)

    return redirect("technical_hr", candidate_id=candidate_id)


# ==================================================
# Final HR Page
# ==================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Candidate
import google.generativeai as genai

# ================= GEMINI 2.5 API =================
GEMINI_API_KEY = "AIzaSyC7kAy5mvawIDl1ri1fawD9LYIOdAXZizg"
genai.configure(api_key=GEMINI_API_KEY)


# ---------------- Generate Final HR Questions ----------------
def generate_final_hr_questions(candidate):
    prompt = f"""
You are a senior HR interviewer.

Generate exactly 3 final HR interview questions for the following candidate.
Questions should be simple and basic, related to candidate's resume.

Candidate Name: {candidate.name}
Skills: {candidate.skills}
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        questions = []
        if response and response.text:
            for line in response.text.split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    questions.append(line.split(".", 1)[1].strip())
        if len(questions) < 3:
            raise Exception("Incomplete AI response")
        return questions[:3]
    except:
        # fallback questions
        return [
            "Tell me about yourself.",
            "What are your strengths?",
            "Where do you see yourself in 5 years?"
        ]


# ---------------- Final HR Page ----------------
def final_hr(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    # Generate questions
    questions = generate_final_hr_questions(candidate)
    request.session["final_hr_questions"] = questions
    request.session["candidate_id"] = candidate.id

    return render(request, "app/final_hr.html", {
        "candidate": candidate,
        "questions": questions,
        "total_questions": len(questions)
    })
import re

def submit_final_hr(request, candidate_id):
    if request.method == "POST":

        answers = [
            request.POST.get("answer1", "").strip(),
            request.POST.get("answer2", "").strip(),
            request.POST.get("answer3", "").strip(),
        ]

        candidate = get_object_or_404(Candidate, id=candidate_id)
        questions = request.session.get("final_hr_questions", [])

        scores = []

        for q, a in zip(questions, answers):

            # If answer is empty → small penalty, not zero
            if not a:
                scores.append(20)   # lenient minimum
                continue

            prompt = f"""
You are an HR evaluator.

Evaluate the answer leniently.
Even partial, simple, or informal answers should get marks.

Question:
{q}

Answer:
{a}

Give a score from 0 to 100.
Only return a single number.
"""

            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)

                # Extract first number safely
                match = re.search(r"\d+", response.text)
                score = int(match.group()) if match else 50

                # Clamp score to avoid weird outputs
                score = max(20, min(score, 95))

                scores.append(score)

            except Exception:
                scores.append(50)  # fallback = lenient average

        # Final HR percentage
        final_hr_score = round(sum(scores) / len(scores), 2) if scores else 0
        request.session["final_hr_score"] = final_hr_score

        # ✅ LENIENT RESULT LOGIC
        if final_hr_score >= 40:
            result = "Shortlisted ✅"
        else:
            result = "Better luck next time ❌"

        aptitude_score = candidate.aptitude_score or 0
        coding_score = 100 if candidate.coding_passed else 0
        technical_hr_score = request.session.get("technical_hr_percentage", 0)
        ats_score = candidate.ats_score or 0

        final_hr_answer_scores = list(zip(answers, scores))

        return render(request, "app/final_hr_result.html", {
            "candidate": candidate,
            "result": result,
            "final_hr_score": final_hr_score,
            "aptitude_score": aptitude_score,
            "coding_score": coding_score,
            "technical_hr_score": technical_hr_score,
            "final_hr_answer_scores": final_hr_answer_scores,
            "ats_score": ats_score
        })

    return redirect("final_hr", candidate_id=candidate_id)


# ==================================================
# Failed Page
# ==================================================
def hr_failed(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    return render(request, "app/hr_failed.html", {
        "candidate": candidate,
        "percentage": request.session.get("technical_hr_percentage", 0)
    })








































































































































































from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AdminUser
from .forms import AdminRegisterForm, AdminLoginForm

def admin_register(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            # Save new admin
            admin_user = form.save(commit=False)
            admin_user.password = form.cleaned_data['password']
            admin_user.save()
            messages.success(request, "Admin account created successfully.")
            return redirect('admin-login')
    else:
        form = AdminRegisterForm()
    return render(request, 'admin_templates/admin_register.html', {'form': form})


def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                admin_user = AdminUser.objects.get(username=username, password=password)
                request.session['admin_user_id'] = admin_user.id
                
                return redirect('admin-dashboard')
            except AdminUser.DoesNotExist:
                messages.error(request, "Invalid username or password.")
    else:
        form = AdminLoginForm()
    return render(request, 'admin_templates/admin_login.html', {'form': form})


def admin_logout(request):
    if 'admin_user_id' in request.session:
        del request.session['admin_user_id']
    messages.success(request, "Admin logged out successfully.")
    return redirect('admin-login')





from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Job, Candidate, InterviewResult
from .forms import JobForm


def post_job(request):
    if 'admin_user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('admin-login')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.admin_id = request.session['admin_user_id']
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect('admin-dashboard')
    else:
        form = JobForm()

    return render(request, 'admin_templates/post_job.html', {'form': form})






from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Job, Candidate, InterviewResult

def admin_dashboard(request):
    if 'admin_user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('admin-login')

    admin_id = request.session['admin_user_id']
    jobs = Job.objects.filter(admin_id=admin_id).order_by('-created_at')

    context = {
        'jobs': jobs,
    }
    return render(request, 'admin_templates/admin_dashboard.html', context)

def view_candidates(request, job_id):
    if 'admin_user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('admin-login')

    job = get_object_or_404(Job, id=job_id)
    candidates = Candidate.objects.filter(job=job)

    candidate_data = []
    for c in candidates:
        interview = getattr(c, 'interview_result', None)

        # Get scores or None if not attended
        ats = getattr(interview, 'ats_score', None)
        aptitude = getattr(interview, 'aptitude_score', None)
        coding = getattr(interview, 'coding_score', None)
        technical = getattr(interview, 'technical_score', None)
        final_hr = getattr(interview, 'final_hr_score', None)

        # Determine result for each round
        def result(score, passing=50):
            if score is None:
                return "-"  # Not attended
            elif score >= passing:
                return "Selected"
            else:
                return "Rejected"

        overall_result = ""
        # Check rounds sequentially
        if ats is None:
            overall_result = "-"
        elif ats < 50:
            overall_result = "Rejected"
        elif aptitude is None:
            overall_result = "-"
        elif aptitude < 50:
            overall_result = "Rejected"
        elif coding is None:
            overall_result = "-"
        elif coding < 50:
            overall_result = "Rejected"
        elif technical is None:
            overall_result = "-"
        elif technical < 50:
            overall_result = "Rejected"
        elif final_hr is None:
            overall_result = "-"
        elif final_hr < 50:
            overall_result = "Rejected"
        else:
            overall_result = "Selected"

        candidate_data.append({
            'name': c.name,
            'email': c.email,
            'ats_score': ats if ats is not None else "-",
            'aptitude_score': aptitude if aptitude is not None else "-",
            'coding_score': coding if coding is not None else "-",
            'technical_hr_score': technical if technical is not None else "-",
            'final_hr_score': final_hr if final_hr is not None else "-",
            'overall_result': overall_result,
        })

    context = {
        'job': job,
        'candidate_data': candidate_data,
    }

    return render(request, 'admin_templates/view_candidates.html', context)
