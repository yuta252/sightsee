import os
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


def get_photo_upload_path(self, filename):
        """
            ユーザーごとにアップロードするフォルダパスを変更
        """
        user_dir_path = settings.MEDIA_ROOT + "/postpic/" + str(self.exhibit_id.owner.id) + "/" + str(self.exhibit_id.id)
        if not os.path.exists(user_dir_path):
            os.makedirs(user_dir_path)
        return user_dir_path + "/" + str(self.id) + '.jpg'

def get_thumbnail_path(self, filename):
        """
            ユーザーごとにthumbnailフォルダパスを変更
        """
        user_dir_path = settings.MEDIA_ROOT + "/thumbnail/" + str(self.id)
        if not os.path.exists(user_dir_path):
            os.makedirs(user_dir_path)
        return user_dir_path + "/" + str(self.id) + '.jpg'
class UserManager(BaseUserManager):
    """User Manager"""
    use_in_migration = True

    def _create_user(self, email, password, **extra_fields):
        """Required to register Email address"""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """is_staff(if able to login to admin site) and is_superuser(all authorization) is set to be false"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        return self._create_user(email, password, **extra_fields)


# User class
class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model"""
    class Meta:
        db_table = 'user'

    MAJOR_FIELD_CHOICE = [
        ('00', '-'),
        ('11', '山岳'),
        ('12', '高原・湿原・原野'),
        ('13', '湖沼'),
        ('14', '河川・渓谷'),
        ('15', '滝'),
        ('16', '海岸・岬'),
        ('17', '岩石・洞窟'),
        ('18', '動物'),
        ('19', '植物'),
        ('21', '史跡'),
        ('22', '神社・寺院・教会'),
        ('23', '城跡・宮殿'),
        ('24', '集落・街'),
        ('25', '郷土景観'),
        ('26', '庭園・公園'),
        ('27', '建造物'),
        ('28', '年中行事（祭り・伝統行事）'),
        ('29', '動植物園・水族館'),
        ('30', '博物館・美術館'),
        ('31', 'テーマ公園・テーマ施設'),
        ('32', '温泉'),
        ('33', '食'),
        ('34', '芸能・イベント'),
    ]

    id = models.IntegerField('sight code', primary_key=True)
    email = models.EmailField('email address', unique=True)
    username = models.CharField('user name', max_length=30, help_text='Please enter within 30 characters.')
    thumbnail = models.ImageField('thumbnail', upload_to=get_thumbnail_path, default='./thumbnail/noimage.png')
    # imagekitによるCACHEからの画像参照
    thumbnail_resized = ImageSpecField(source='thumbnail', processors=[ResizeToFill(250, 250)], format='JPEG', options={'quality':60})

    self_intro = models.CharField('introduction', max_length=1000, null=True, blank=True, help_text='Please enter within 1000 characters.')
    major_category = models.CharField('major category', max_length=2, choices=MAJOR_FIELD_CHOICE, default='00')
    address = models.CharField('address', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    tel_number_regex = RegexValidator(regex=r'^[0-9]+$', message=('Tel number must be entered in the format: "09012345678". Up to 15 digits allowed.'))
    telephone = models.CharField('telephone number', max_length=15, validators=[tel_number_regex])
    entrance_fee = models.CharField('entrance fee', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    business_hours = models.CharField('business hours', max_length=100, null=True, blank=True, help_text='Please enter within 100 characters.')
    holiday = models.CharField('holiday', max_length=30, null=True, blank=True, help_text='Please enter within 30 characters.')
    # knn_model = models.FileField('knn model', upload_to=, null=True, blank=True)
    # TODO: 最新の情報（要検討）
    is_staff = models.BooleanField('staff_status', default=False, help_text='管理サイトにログイン可能かどうか指定してください。')
    is_active = models.BooleanField('active', default='True', help_text='ユーザーがアクティブ状態か指定してください。')
    date_joined = models.DateTimeField('date_joined', default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send Email to user"""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username


# Exhibit class
class Exhibit(models.Model):

    class Meta:
        db_table = 'exhibit'
        ordering = ('-upload_date',)

    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='exhibit_owner')
    exhibit_name = models.TextField(max_length=30, help_text='30文字以内で入力しください')
    exhibit_desc = models.TextField(max_length=500, help_text='500文字以内で入力してください')
    exhibit_name_en = models.TextField(max_length=30, null=True, blank=True, default='', help_text='30文字以内で入力しください')
    exhibit_desc_en = models.TextField(max_length=500, null=True, blank=True, default='', help_text='500文字以内で入力してください')
    exhibit_name_zh = models.TextField(max_length=30, null=True, blank=True, default='', help_text='30文字以内で入力しください')
    exhibit_desc_zh = models.TextField(max_length=500, null=True, blank=True, default='', help_text='500文字以内で入力してください')
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.exhibit_name) + '(' + str(self.owner) + ')'

class ExhibitPicture(models.Model):

    class Meta:
        db_table = 'exhibit_picture'
        ordering = ('-upload_date',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exhibit_id = models.ForeignKey(Exhibit, on_delete=models.CASCADE, related_name='exhibit_pk')
    post_pic = models.ImageField(upload_to=get_photo_upload_path, blank=True, null=True)
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.exhibit_id.owner.id) + '/' + str(self.exhibit_id.id) + '/' + str(self.id)


# Other Language model class
class UserLang(models.Model):
    class Meta:
        db_table = 'userlang'

    """Choice field"""
    LANGUAGE_FIELD_CHOICE = [
        ('na', ''),
        ('en', 'English'),
        ('zh', 'Chinese'),
        ('ko', 'Korea')
    ]

    # MAJOR_FIELD_CHOICE = [
    #     ('NA', ''),
    #     ('MU', 'Museum'),
    #     ('AM', 'Art museum'),
    #     ('SH', 'Shrine'),
    #     ('TR', 'temple'),
    #     ('BU', 'Building'),
    #     ('AN', 'Animal and Aquarium')
    # ]

    """User English model"""
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    language = models.CharField('language', max_length=5, choices=LANGUAGE_FIELD_CHOICE, default='NA')
    username = models.CharField('user name', max_length=30, null=True, blank=True, help_text='Please enter within 30 characters.')
    self_intro = models.CharField('introduction', max_length=1000, null=True, blank=True, help_text='Please enter within 1000 characters.')
    address = models.CharField('address', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    entrance_fee = models.CharField('entrance fee', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    business_hours = models.CharField('business hours', max_length=100, null=True, blank=True, help_text='Please enter within 100 characters.')
    holiday = models.CharField('holiday', max_length=30, null=True, blank=True, help_text='Please enter within 30 characters.')
    upload_date = models.DateTimeField(default=timezone.now)

    # major_category = models.CharField('major category', max_length=2, choices=MAJOR_FIELD_CHOICE, default='NA')

    def __str__(self):
        return str(self.owner) + '(' + str(self.language) + ')'


