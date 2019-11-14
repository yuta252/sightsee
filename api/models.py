from django.db import models
from django.utils import timezone

from analysis.models import User


class AppUser(models.Model):

    class Meta:
        db_table = 'appuser'
        ordering = ('-date_joined',)

    email = models.EmailField('email address', unique=True)
    is_active = models.BooleanField('active', default='false')
    date_joined = models.DateTimeField('date_joined', default=timezone.now)

    def __str__(self):
        return str(self.email)

class Review(models.Model):

    class Meta:
        db_table = 'review'
        ordering = ('-date_posted',)

    spot = models.ForeignKey(User, on_delete=models.PROTECT, related_name='review_target')
    writer = models.ForeignKey(AppUser, on_delete=models.PROTECT, related_name='review_writer')
    lang = models.CharField('language', max_length=5, default='NA')
    review_post = models.TextField('review', max_length=140, null=True, blank=True, help_text='Please enter within 140 characters.')
    review_rating = models.FloatField('rating', null=True, blank=True)
    date_posted = models.DateTimeField('date posted', default=timezone.now)

    def __str__(self):
        return str(self.spot) + '(written by' + str(self.writer) + ')'