import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, DetailView, FormView
from django.views.generic.edit import ModelFormMixin, UpdateView

from .forms import ExhibitForm, SignupForm, LoginForm, UserEditForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm, EmailChangeForm, ContactForm
from .models import User, Exhibit

User = get_user_model()


# Dashboard
class DashboardView(TemplateView):
    template_name = 'analysis/dashboard.html'


# Exhibit list admin page
class IndexView(ListView, ModelFormMixin):

    model = Exhibit
    form_class = ExhibitForm
    paginate_by = 10
    template_name = 'analysis/upload.html'

    def get_queryset(self):
        queryset = Exhibit.objects.filter(owner=self.request.user)

        # Search form
        keyword = self.request.GET.get('keyword')
        if keyword:
            queryset = queryset.filter(Q(exhibit_name__icontains=keyword) | Q(exhibit_desc__icontains=keyword))

        return queryset

    # Set post form
    def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """If is_valid is True, put user info into required owner before saving"""
        owner = self.request.user
        obj = form.save(commit=False)
        obj.owner = owner
        # TO DO : データベース保存に例外処理追加
        obj.save()
        return redirect('analysis:index')


class EditView(View, ModelFormMixin):

    model = Exhibit
    form_class = ExhibitForm

    def get(self, request, *args, **kwargs):
        return redirect('analysis:index')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        exhibit_pk = request.POST['exhibit_pk']
        if form.is_valid():
            return self.form_valid(form, exhibit_pk)
        else:
            return self.form_invalid(form)

    def form_valid(self, form, pk):
        """If is_valid is True, put user info into required owner before saving"""
        owner = self.request.user
        obj = Exhibit.objects.filter(id=pk)[0]
        print(obj)

        obj.owner = owner
        obj.exhibit_name = form.cleaned_data['exhibit_name']
        obj.exhibit_desc = form.cleaned_data['exhibit_desc']
        obj.post_pic = form.cleaned_data['post_pic']
        # TO DO : データベース保存に例外処理追加
        obj.save()
        return redirect('analysis:index')


# AJAX to edit exhibit data
class EditAJAXView(View):
    def get(self, request, *args, **kwargs):
        exhibit_pk = request.GET.get('exhibit_pk')
        obj = Exhibit.objects.filter(id=exhibit_pk)[0]

        data = {
            'exhibit_pk': exhibit_pk,
            'exhibit_name': obj.exhibit_name,
            'exhibit_desc': obj.exhibit_desc,
        }
        data = json.dumps(data)
        return HttpResponse(data, content_type='application/json')


class DeleteView(View):

    model = Exhibit

    def get(self, request, *args, **kwargs):
        return redirect('analysis:index')

    def post(self, request, *args, **kwargs):
        exhibit_pk = request.POST['exhibit_pk']
        # 例外処理の追加
        Exhibit.objects.filter(id=exhibit_pk).delete()
        return redirect('analysis:index')

# Mypage settings
class MypageView(TemplateView):
    template_name = 'analysis/mypage.html'

class SettingView(UpdateView):
    template_name = 'analysis/setting.html'
    model = User
    form_class = UserEditForm
    success_url = reverse_lazy('analysis:mypage')
    """
    def get_url_success(self):
        return reverse_lazy('analysis:mypage', kwargs={"pk", self.kwargs["pk"]})
    """

# Password change
class PasswordChange(PasswordChangeView):
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('analysis:password_change_done')
    template_name = 'analysis/password_change.html'

class PasswordChangeDone(PasswordChangeDoneView):
    template_name = 'analysis/password_change_done.html'

# Email Change
class EmailChange(FormView):
    template_name = 'analysis/email_change_form.html'
    form_class = EmailChangeForm

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['email']

        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol':'https' if self.request.is_secure() else 'http',
            'domain':domain,
            'token':dumps(new_email),
            'user':user,
        }

        subject = render_to_string('analysis/mail_template/email_change/subject.txt', context)
        message = render_to_string('analysis/mail_template/email_change/message.txt', context)
        send_mail(subject, message, None, [new_email])

        return redirect('analysis:email_change_done')

class EmailChangeDone(TemplateView):
    template_name = 'analysis/email_change_done.html'

class EmailChangeComplete(TemplateView):
    template_name = 'analysis/email_change_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            new_email = loads(token, max_age=self.timeout_seconds)
        except SignatureExpired:
            return HttpResponseBadRequest()
        except BadSignature:
            return HttpResponseBadRequest()
        else:
            User.objects.filter(email=new_email, is_active=False).delete()
            request.user.email = new_email
            request.user.save()
            return super().get(request, **kwargs)


# Contact form
class ContactView(FormView):
    template_name = 'analysis/contact_form.html'
    form_class = ContactForm

    def form_valid(self, form):
        user = self.request.user

        contact_title = form.cleaned_data['contact_title']
        contact_content = form.cleaned_data['contact_content']

        context = {
            'contact_title':contact_title,
            'contact_content':contact_content,
            'user':user
        }

        subject = render_to_string('analysis/mail_template/contact/subject.txt', context)
        message = render_to_string('analysis/mail_template/contact/message.txt', context)

        send_mail(
            subject,
            message,
            user.email,
            ['nakano.yuta252@gmail.com'],
        )
        return redirect('analysis:contact_done')

class ContactDone(TemplateView):
    template_name = 'analysis/contact_done.html'



# Sign up
class SignupView(CreateView):
    """User temporary registration"""
    form_class = SignupForm
    template_name = 'analysis/signup.html'

    # TO DO : 文字数の少ないpassword入力時はじかれるためvalidationが必要

    def form_valid(self, form):
        """
            Temporary registration and main registration
            Switch temp to main by is_active(boolean)
        """
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Send Email with URL to activate account
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol':self.request.scheme,
            'domain':domain,
            'token':dumps(user.pk),
            'user':user
        }

        subject = render_to_string('analysis/mail_template/create/subject.txt', context)
        message = render_to_string('analysis/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('analysis:signup_done')

class SignupDone(TemplateView):
    template_name = 'analysis/signup_done.html'

class SignupComplete(TemplateView):
    """After accessing URL attached with Email, go on to main registration"""
    template_name = 'analysis/signup_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

    def get(self, request, **kwargs):
        """If token is TRUE, register"""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)
        except SignatureExpired:
            return HttpResponseBadRequest()
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)
        return HttpResponseBadRequest()

# Login page
class Login(LoginView):
    form_class = LoginForm
    template_name = 'analysis/login.html'

# Logout page
class Logout(LogoutView):
    template_name = 'analysis/login.html'

# Password reset
class PasswordReset(PasswordResetView):
    subject_template_name = 'analysis/mail_template/password_reset/subject.txt'
    email_template_name = 'analysis/mail_template/password_reset/message.txt'
    template_name = 'analysis/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('analysis:password_reset_done')

class PasswordResetDone(PasswordResetDoneView):
    template_name = 'analysis/password_reset_done.html'

class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = MySetPasswordForm
    success_url = reverse_lazy('analysis:password_reset_complete')
    template_name = 'analysis/password_reset_confirm.html'

class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'analysis/password_reset_complete.html'


class Spotapi(View):

    def get(self, request, *args, **kwargs):
        search_word = request.GET.get('s')
        spot_list = User.objects.filter(username__icontains=search_word)

        # TO DO : デプロイ時にURL変更
        DEBUG_URL = 'http://10.0.2.2:80'
        data = {}

        data["Search"] = []

        for spot in spot_list:
            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':DEBUG_URL + spot.thumbnail.url,
                'spotpk':spot.pk
            }
            data["Search"].append(spot_dict)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

class SpotDetailapi(View):

    def get(self, request, *args, **kwargs):
        search_word = request.GET.get('i')
        spot = User.objects.filter(id=search_word)[0]
        print(spot)
        # TO DO : デプロイ時にURL変更
        DEBUG_URL = 'http://10.0.2.2:80'
        data = {
            'Title':spot.username,
            'Category':spot.major_category,
            'Thumbnail':DEBUG_URL + spot.thumbnail.url,
            'Information':spot.self_intro,
            'Address':spot.address,
            'Telephone':spot.telephone,
            'EntranceFee':spot.entrance_fee,
            'BusinessHours':spot.business_hours,
            'Holiday':spot.holiday,
        }

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')




