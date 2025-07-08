# apps/meetings/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Meeting, MeetingAttendee
from .google_api import create_google_meet_event
from apps.users.models import User

@receiver(post_save, sender=Meeting)
def handle_new_meeting(sender, instance, created, **kwargs):
    # Bu signal faqat yangi Meeting obyekti yaratilganda ishlaydi
    if created:
        # --- 1-QISM: Qatnashuvchilarni aniqlash va bazaga yozish ---
        
        # Barcha ehtimoliy qatnashuvchilarni yig'ish uchun bo'sh QuerySet
        attendee_users_qs = User.objects.none()

        if instance.audience_type == Meeting.AudienceType.WORKSPACE_MEMBERS and instance.workspace:
            attendee_users_qs = User.objects.filter(workspace_memberships__workspace=instance.workspace, is_active=True)
        elif instance.audience_type == Meeting.AudienceType.ALL_STAFF:
            attendee_users_qs = User.objects.filter(user_type__in=['STAFF', 'ADMIN'], is_active=True)
        
        # Unikal foydalanuvchilar email'larini yig'ish
        attendees_emails = set(attendee_users_qs.values_list('email', flat=True))

        # Tadbir tashkilotchisining o'zini ham ro'yxatga qo'shish
        if instance.organizer and instance.organizer.email:
            attendees_emails.add(instance.organizer.email)
        
        final_attendee_emails = list(attendees_emails)

        # Ma'lumotlar bazasiga `MeetingAttendee` yozuvlarini yaratish
        with transaction.atomic():
            attendee_users = User.objects.filter(email__in=final_attendee_emails)
            attendees_to_create = [
                MeetingAttendee(meeting=instance, user=user) for user in attendee_users
            ]
            if attendees_to_create:
                MeetingAttendee.objects.bulk_create(attendees_to_create, ignore_conflicts=True)

        # --- 2-QISM: Google Calendar'da tadbir yaratish ---
        
        # Agar tadbirda hali Google Event ID bo'lmasa va qatnashuvchilar topilgan bo'lsa
        if not instance.google_event_id and final_attendee_emails:
            print(f"✅ Google Event (to'liq) yaratishga harakat. Qatnashuvchilar: {final_attendee_emails}")
            
            link, event_id = create_google_meet_event(
                instance.title,
                instance.description,
                instance.start_time,
                instance.end_time,
                final_attendee_emails  # To'plangan email'lar ro'yxati
            )
            
            # Agar link va ID muvaffaqiyatli olinsa, bazani yangilash
            if link and event_id:
                # Signal qayta ishga tushmasligi uchun `post_save.disconnect` va `connect` ishlatish mumkin,
                # lekin `update` metodi signalni ishga tushirmaydi, shuning uchun bu xavfsiz.
                Meeting.objects.filter(pk=instance.pk).update(
                    meeting_link=link,
                    google_event_id=event_id
                )