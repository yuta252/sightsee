from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


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

    email = models.EmailField('email address', unique=True)
    username = models.CharField('user name', max_length=30, help_text='Please enter within 30 characters.')
    thumbnail = models.ImageField('thumbnail', upload_to='thumbnail', default='./thumbnail/noimage.png')
    self_intro = models.CharField('introduction', max_length=1000, null=True, blank=True, help_text='Please enter within 1000 characters.')

    MAJOR_FIELD_CHOICE = [
        ('NA', '-'),
        ('MU', '博物館'),
        ('AM', '美術館'),
        ('SH', '神社'),
        ('TR', '寺'),
        ('BU', '建築物'),
        ('AN', '動物園・水族館')
    ]
    major_category = models.CharField('major category', max_length=2, choices=MAJOR_FIELD_CHOICE, default='NA')
    address = models.CharField('address', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')

    tel_number_regex = RegexValidator(regex=r'^[0-9]+$', message=('Tel number must be entered in the format: "09012345678". Up to 15 digits allowed.'))
    telephone = models.CharField('telephone number', max_length=15, validators=[tel_number_regex])
    entrance_fee = models.CharField('entrance fee', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    business_hours = models.CharField('business hours', max_length=100, null=True, blank=True, help_text='Please enter within 100 characters.')
    holiday = models.CharField('holiday', max_length=30, null=True, blank=True, help_text='Please enter within 30 characters.')
    """
    TO DO:
    星の数（レビューの集計）
    最新の情報（要検討）
    英語ver
    """
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
    # To do : フォルダ単位でアップロードするように変更。さらにアップロードフォルダがわかるようにusernameで格納
    post_pic = models.ImageField(upload_to='postpic/%Y/%m/%d', blank=True)
    exhibit_name_en = models.TextField(max_length=30, null=True, blank=True, default='', help_text='30文字以内で入力しください')
    exhibit_desc_en = models.TextField(max_length=500, null=True, blank=True, default='', help_text='500文字以内で入力してください')
    exhibit_name_zh = models.TextField(max_length=30, null=True, blank=True, default='', help_text='30文字以内で入力しください')
    exhibit_desc_zh = models.TextField(max_length=500, null=True, blank=True, default='', help_text='500文字以内で入力してください')
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.exhibit_name) + '(' + str(self.owner) + ')'


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

    MAJOR_FIELD_CHOICE = [
        ('NA', ''),
        ('MU', 'Museum'),
        ('AM', 'Art museum'),
        ('SH', 'Shrine'),
        ('TR', 'temple'),
        ('BU', 'Building'),
        ('AN', 'Animal and Aquarium')
    ]

    """User English model"""
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    language = models.CharField('language', max_length=5, choices=LANGUAGE_FIELD_CHOICE, default='NA')
    username = models.CharField('user name', max_length=30, null=True, blank=True, help_text='Please enter within 30 characters.')
    self_intro = models.CharField('introduction', max_length=1000, null=True, blank=True, help_text='Please enter within 1000 characters.')
    major_category = models.CharField('major category', max_length=2, choices=MAJOR_FIELD_CHOICE, default='NA')
    address = models.CharField('address', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    entrance_fee = models.CharField('entrance fee', max_length=150, null=True, blank=True, help_text='Please enter within 150 characters.')
    business_hours = models.CharField('business hours', max_length=100, null=True, blank=True, help_text='Please enter within 100 characters.')
    holiday = models.CharField('holiday', max_length=30, null=True, blank=True, help_text='Please enter within 30 characters.')
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.owner) + '(' + str(self.language) + ')'


