# apps/meetings/models.py

from django.db import models
from apps.users.models import User
from apps.workspaces.models import Workspace

class Meeting(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'scheduled'
        ONGOING = 'ONGOING', 'ongoing'
        COMPLETED = 'COMPLETED', 'completed'
        CANCELLED = 'CANCELLED', 'cancelled'
    
    class AudienceType(models.TextChoices):
        WORKSPACE_MEMBERS = 'WORKSPACE_MEMBERS', 'Workspace members'
        ALL_STAFF = 'ALL_STAFF', 'All staff'
        SPECIFIC_USERS = 'SPECIFIC_USERS', 'Specific users'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='meetings', null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    
    # For Google Meet integration
    meeting_link = models.URLField(max_length=512, blank=True, null=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)

    # Audience type for the meeting
    audience_type = models.CharField(max_length=20, choices=AudienceType.choices, default=AudienceType.WORKSPACE_MEMBERS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meetings'
        ordering = ['-start_time']

    def __str__(self):
        return self.title

class MeetingAttendee(models.Model):
    class Status(models.TextChoices):
        INVITED = 'INVITED', 'Invited'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_attendances')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INVITED)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meeting_attendees'
        unique_together = ['meeting', 'user']
        ordering = ['user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.meeting.title}"
