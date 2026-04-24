from django.db import models
from django.contrib.auth.models import User
from PIL import Image


# =========================
# USER PROFILE
# =========================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.avatar.path)
        if img.height > 100 or img.width > 100:
            img.thumbnail((100, 100))
            img.save(self.avatar.path)


# =========================
# ADMIN USER
# =========================
class AdminUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


# =========================
# JOB MODEL
# =========================
from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=50)
    job_type = models.CharField(max_length=50, choices=(
        ('Full-Time', 'Full-Time'),
        ('Part-Time', 'Part-Time'),
        ('Internship', 'Internship'),
    ))
    salary = models.DecimalField(max_digits=10, decimal_places=2)  # Add this line
    description = models.TextField()
    admin_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# =========================
# CANDIDATE MODEL (UPDATED ✅)
# =========================
class Candidate(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    dob = models.DateField()
    degree = models.CharField(max_length=100)
    standing_arrears = models.IntegerField(default=0)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    # 🔥 RESUME ANALYSIS (GEMINI)
    ats_score = models.IntegerField(null=True, blank=True)
    skills = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    improvement = models.TextField(blank=True)

    # 🔥 ROUND STATUS
    aptitude_score = models.IntegerField(null=True, blank=True)
    aptitude_passed = models.BooleanField(default=False)
    coding_passed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'email')  # one attempt per job

    def __str__(self):
        return f"{self.name} ({self.email})"


# =========================
# INTERVIEW RESULT
# =========================
from django.db import models
class InterviewResult(models.Model):
    candidate = models.OneToOneField(
        "Candidate",
        on_delete=models.CASCADE,
        related_name="interview_result"
    )

    ats_score = models.IntegerField(default=0)
    aptitude_score = models.IntegerField(default=0)
    coding_score = models.IntegerField(default=0)        # <-- Add this
    technical_score = models.IntegerField(default=0)    # <-- Add this
    final_hr_score = models.IntegerField(default=0)     # <-- Optional, for final HR

    status = models.CharField(
        max_length=50,
        choices=[
            ("Aptitude", "Aptitude"),
            ("Coding Round", "Coding Round"),
            ("Technical HR", "Technical HR"),
            ("Final HR", "Final HR"),
            ("Rejected", "Rejected"),
            ("Selected", "Selected"),
        ],
        default="Aptitude"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



