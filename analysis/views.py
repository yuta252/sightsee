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

from .forms import ExhibitForm, SignupForm, LoginForm, UserEditForm, UserLangEditForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm, EmailChangeForm, ContactForm
from .models import User, Exhibit, UserLang

User = get_user_model()


# Dashboard
class DashboardView(TemplateView):
    template_name = 'analysis/dashboard.html'


# Exhibit list admin page
class UploadView(ListView, ModelFormMixin):

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
        return redirect('analysis:upload')


class EditView(UpdateView):

    model = Exhibit
    form_class = ExhibitForm
    template_name = 'analysis/upload_edit.html'
    success_url = reverse_lazy('analysis:upload')

class DeleteView(View):

    model = Exhibit

    def get(self, request, *args, **kwargs):
        return redirect('analysis:upload')

    def post(self, request, *args, **kwargs):
        exhibit_pk = request.POST['exhibit_pk']
        # 例外処理の追加
        Exhibit.objects.filter(id=exhibit_pk).delete()
        return redirect('analysis:upload')

# Mypage settings
class MypageView(ListView, ModelFormMixin):
    template_name = 'analysis/mypage.html'
    model = UserLang
    form_class = UserLangEditForm

    def get_queryset(self):
        queryset = UserLang.objects.filter(owner=self.request.user)
        print(queryset)
        return queryset

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
        return redirect('analysis:mypage')


class SettingView(UpdateView):
    template_name = 'analysis/setting.html'
    model = User
    form_class = UserEditForm
    success_url = reverse_lazy('analysis:mypage')
    """
    def get_url_success(self):
        return reverse_lazy('analysis:mypage', kwargs={"pk", self.kwargs["pk"]})
    """

# Other language
class UserLangEditView(View, ModelFormMixin):

    model = UserLang
    form_class = UserLangEditForm

    def get(self, request, *args, **kwargs):
        return redirect('analysis:mypage')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        userlang_pk = request.POST['userlang_pk']
        # TO DO : Validation 追加。同じ言語を選択した場合登録させないようにする。Language Uniqueにする
        if form.is_valid():
            return self.form_valid(form, userlang_pk)
        else:
            return self.form_invalid(form)

    def form_valid(self, form, pk):
        """If is_valid is True, put user info into required owner before saving"""
        owner = self.request.user
        obj = UserLang.objects.filter(id=pk)[0]

        obj.owner = owner
        obj.language = form.cleaned_data['language']
        obj.username = form.cleaned_data['username']
        obj.self_intro = form.cleaned_data['self_intro']
        obj.major_category = form.cleaned_data['major_category']
        obj.address = form.cleaned_data['address']
        obj.entrance_fee = form.cleaned_data['entrance_fee']
        obj.business_hours = form.cleaned_data['business_hours']
        obj.holiday = form.cleaned_data['holiday']

        # TO DO : データベース保存に例外処理追加
        obj.save()
        return redirect('analysis:mypage')


class UserLangEditAJAXView(View):
    def get(self, request, *args, **kwargs):
        userlang_pk = request.GET.get('userlang_pk')
        obj = UserLang.objects.filter(id=userlang_pk)[0]

        data = {
            'userlang_pk': userlang_pk,
            'userlang_language':obj.language,
            'userlang_username': obj.username,
            'userlang_self_intro': obj.self_intro,
            'userlang_major_category':obj.major_category,
            'userlang_address':obj.address,
            'userlang_entrance_fee':obj.entrance_fee,
            'userlang_business_hours':obj.business_hours,
            'userlang_holiday':obj.holiday,
        }
        data = json.dumps(data)
        return HttpResponse(data, content_type='application/json')

class UserLangDeleteView(View):

    model = UserLang

    def get(self, request, *args, **kwargs):
        return redirect('analysis:mypage')

    def post(self, request, *args, **kwargs):
        userlang_pk = request.POST['userlang_pk']
        # 例外処理の追加
        UserLang.objects.filter(id=userlang_pk).delete()
        return redirect('analysis:mypage')


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


# # API response for android app
# class Spotapi(View):

#     DEBUG_URL = 'http://10.0.2.2:80'

#     def get(self, request, *args, **kwargs):
#         lang = request.GET.get('lang')
#         search_word = request.GET.get('s')

#         # TO Do: 他の言語も含めて拡張性のある仕様にする

#         if lang == 'ja_JP':
#             data = self.get_json_ja(lang, search_word)
#         elif lang == 'en_US':
#             data = self.get_json_other(lang, search_word)
#         else:
#             data = self.get_json_other(lang, search_word)

#         data = json.dumps(data, indent=5, ensure_ascii=False)
#         return HttpResponse(data, content_type='application/json')

#     def get_json_ja(self, lang, search):
#         data = {}
#         data["Search"] = []
#         spot_list = User.objects.filter(username__icontains=search)
#         for spot in spot_list:
#             spot_dict = {
#                 'Title':spot.username,
#                 'Major_category':spot.major_category,
#                 'Thumbnail':self.DEBUG_URL + spot.thumbnail.url,
#                 'spotpk':spot.pk
#             }
#             data["Search"].append(spot_dict)
#         return data

#     def get_json_other(self, lang, search):
#         data = {}
#         data["Search"] = []
#         spot_list = UserLang.objects.filter(username__icontains=search, language='en')
#         for spot in spot_list:
#             spot_dict = {
#                 'Title':spot.username,
#                 'Major_category':spot.major_category,
#                 'Thumbnail':self.DEBUG_URL + spot.owner.thumbnail.url,
#                 'spotpk':spot.owner.pk
#             }
#             data["Search"].append(spot_dict)
#         return data
# class SpotDetailapi(View):
#     DEBUG_URL = 'http://10.0.2.2:80'

#     def get(self, request, *args, **kwargs):
#         lang = request.GET.get('lang')
#         spot_id = request.GET.get('i')

#         # TO Do: 他の言語も含めて拡張性のある仕様にする
#         if lang == 'ja_JP':
#             data = self.get_json_ja(lang, spot_id)
#         elif lang == 'en_US':
#             data = self.get_json_other(lang, spot_id)
#         else:
#             data = self.get_json_other(lang, spot_id)

#         data = json.dumps(data, indent=5, ensure_ascii=False)
#         return HttpResponse(data, content_type='application/json')

#     def get_json_ja(self, lang, spot_id):
#         spot = User.objects.get(id=spot_id)
#         data = {
#             'Title':spot.username,
#             'Category':spot.major_category,
#             'Thumbnail':self.DEBUG_URL + spot.thumbnail.url,
#             'Information':spot.self_intro,
#             'Address':spot.address,
#             'Telephone':spot.telephone,
#             'EntranceFee':spot.entrance_fee,
#             'BusinessHours':spot.business_hours,
#             'Holiday':spot.holiday,
#         }
#         return data

#     def get_json_other(self, lang, spot_id):
#         spot = User.objects.get(id=spot_id)
#         spotlang = spot.userlang_set.filter(language='en')[0]
#         data = {
#             'Title':spotlang.username,
#             'Category':spotlang.major_category,
#             'Thumbnail':self.DEBUG_URL + spot.thumbnail.url,
#             'Information':spotlang.self_intro,
#             'Address':spotlang.address,
#             'Telephone':spot.telephone,
#             'EntranceFee':spotlang.entrance_fee,
#             'BusinessHours':spotlang.business_hours,
#             'Holiday':spotlang.holiday,
#         }
#         return data




