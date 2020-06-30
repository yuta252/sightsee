import os

from django.conf import settings
from django.db import models
from django.utils import timezone

from analysis.models import User


def get_thumbnail_path(self, filename):
    """
        ユーザーごとにthumbnailフォルダパスを変更
    """
    user_dir_path = settings.MEDIA_ROOT + "/userthumbnail/" + str(self.id)
    if not os.path.exists(user_dir_path):
        os.makedirs(user_dir_path)
    return user_dir_path + "/" + str(self.id) + '.jpg'
    # TODO : 本番環境のときpath入れ替え
    # return "/thumbnail/" + str(self.id) + '.jpg'


class AppUser(models.Model):

    class Meta:
        db_table = 'appuser'
        ordering = ('-date_joined',)

    email = models.EmailField('email address', unique=True)
    password = models.CharField('password', max_length=100)
    apikey = models.CharField('api key', max_length=150, null=True, blank=True)
    username = models.CharField('user name', max_length=100, default="未設定")
    thumbnail = models.ImageField(upload_to=get_thumbnail_path, default='./userthumbnail/noimage.png')
    sex = models.IntegerField('sex', default=0)
    birth = models.IntegerField('birth', default=0)
    country = models.CharField('country', null=True, blank=True, max_length=5)
    language = models.CharField('language', default='OT', max_length=5)
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
    review_post = models.TextField('review', max_length=500, null=True, blank=True, help_text='Please enter within 140 characters.')
    review_rating = models.FloatField('rating', null=True, blank=True)
    date_posted = models.DateTimeField('date posted', default=timezone.now)

    def __str__(self):
        return str(self.spot) + '(written by' + str(self.writer) + ')'


class Like(models.Model):
    class Meta:
        db_table = 'like'
        ordering = ('-date_posted',)

    apikey = models.CharField('api key', max_length=150, null=True, blank=True)
    spot = models.ForeignKey(User, on_delete=models.PROTECT, related_name='like_target')
    date_posted = models.DateTimeField('date posted', default=timezone.now)
