# apps/notifications/models.py

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.users.models import User

class Notification(models.Model):
    # Kimga yuborilgani
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Kim tomonidan (ixtiyoriy, masalan "Tizim" bo'lishi mumkin)
    actor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='actions')
    
    # Harakatning tavsifi
    verb = models.CharField(max_length=255)
    
    # Harakat obyekti (masalan, yangi Task yoki Meeting)
    action_object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    action_object_id = models.PositiveIntegerField(null=True, blank=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_id')

    # Qo'shimcha obyekt (masalan, Workspace)
    target_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_notifications')
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_id')
    
    # O'qilganmi yoki yo'q
    is_read = models.BooleanField(default=False)
    
    # To'liq matn (qulaylik uchun)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'notifications'

    def __str__(self):
        return f"To: {self.recipient.email} - {self.verb}"