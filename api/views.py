import json
import random

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from analysis.models import User, UserLang
from .models import AppUser, Review


User = get_user_model()


class AuthMailView(View):

    def get(self, request, *args, **kwargs):
        print("yes get")
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        print("yes post")
        json_request = json.loads(request.body)
        email = json_request["email"]

        auth_code = random.randrange(1000, 9999)

        is_exist = AppUser.objects.filter(email=email).exists()
        print(is_exist)
        # データベースへの登録重複判定
        if (is_exist):
            data = {
                'auth_code':0,
                'message':True,
            }
        else:
            # 認証メール送信
            context = {
                'email':email,
                'auth_code':auth_code,
            }

            # TO DO: ユーザーによって各言語のメールを返すようにする
            subject = render_to_string('api/mail_template/email_auth/subject.txt', context)
            content = render_to_string('api/mail_template/email_auth/message.txt', context)
            send_mail(subject, content, 'no-reply@sight.com', [email])

            # DBへの新規登録
            AppUser.objects.create(email=email, is_active=False)

            # JSON response
            data = {
                'auth_code':auth_code,
                'message':False,
            }

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AuthMailView, self).dispatch(*args, **kwargs)


# API response for android app
class Spotapi(View):

    DEBUG_URL = 'http://10.0.2.2:80'

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('lang')
        search_word = request.GET.get('s')

        # TO Do: 他の言語も含めて拡張性のある仕様にする

        if lang == 'ja_JP':
            data = self.get_json_ja(lang, search_word)
        elif lang == 'en_US':
            data = self.get_json_other(lang, search_word)
        else:
            data = self.get_json_other(lang, search_word)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, lang, search):
        data = {}
        data["Search"] = []
        spot_list = User.objects.filter(username__icontains=search)
        for spot in spot_list:
            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':self.DEBUG_URL + spot.thumbnail.url,
                'spotpk':spot.pk
            }
            data["Search"].append(spot_dict)
        return data

    def get_json_other(self, lang, search):
        data = {}
        data["Search"] = []
        spot_list = UserLang.objects.filter(username__icontains=search, language='en')
        for spot in spot_list:
            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':self.DEBUG_URL + spot.owner.thumbnail.url,
                'spotpk':spot.owner.pk
            }
            data["Search"].append(spot_dict)
        return data


class SpotDetailapi(View):
    DEBUG_URL = 'http://10.0.2.2:80'

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('lang')
        spot_id = request.GET.get('i')

        # TO Do: 他の言語も含めて拡張性のある仕様にする
        if lang == 'ja_JP':
            data = self.get_json_ja(lang, spot_id)
        elif lang == 'en_US':
            data = self.get_json_other(lang, spot_id)
        else:
            data = self.get_json_other(lang, spot_id)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, lang, spot_id):
        spot = User.objects.get(id=spot_id)
        data = {
            'Title':spot.username,
            'Category':spot.major_category,
            'Thumbnail':self.DEBUG_URL + spot.thumbnail.url,
            'Information':spot.self_intro,
            'Address':spot.address,
            'Telephone':spot.telephone,
            'EntranceFee':spot.entrance_fee,
            'BusinessHours':spot.business_hours,
            'Holiday':spot.holiday,
        }
        return data

    def get_json_other(self, lang, spot_id):
        spot = User.objects.get(id=spot_id)
        spotlang = spot.userlang_set.filter(language='en')[0]
        data = {
            'Title':spotlang.username,
            'Category':spotlang.major_category,
            'Thumbnail':self.DEBUG_URL + spot.thumbnail.url,
            'Information':spotlang.self_intro,
            'Address':spotlang.address,
            'Telephone':spot.telephone,
            'EntranceFee':spotlang.entrance_fee,
            'BusinessHours':spotlang.business_hours,
            'Holiday':spotlang.holiday,
        }
        return data

class PostReview(View):

    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)

        writer = json_request["email"]
        writer_email = AppUser.objects.filter(email=writer)[0]
        spot = json_request["spotId"]
        print(spot)
        spot_email = User.objects.filter(id=spot)[0]
        lang = json_request["lang"]
        review_post = json_request["reviewPost"]
        rating_post = json_request["ratingPost"]

        # DBへの新規登録
        Review.objects.create(writer=writer_email, spot=spot_email, lang=lang, review_post=review_post, review_rating=rating_post)

        # JSON response
        data = {
        }

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(PostReview, self).dispatch(*args, **kwargs)


class Reviewapi(View):

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('lang')
        spot_id = request.GET.get('s')

        #TODo: 他の言語も含めて拡張性のある仕様にする

        data = self.get_json(lang, spot_id)
        print(data)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json(self, lang, spot_id):
        data = {}
        data["Review"] = []
        spot = User.objects.get(id=spot_id)
        # TO DO : 各言語でのレビューのみ抽出するように修正
        review_list = spot.review_target.filter(lang=lang)

        for review in review_list:
            review_dict = {
                'Username':review.writer.email,
                'Review_rating':review.review_rating,
                'Review_content':review.review_post,
            }
            data["Review"].append(review_dict)
        return data


class CameraResult(View):

    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)

        email = json_request["email"]
        # 50次元の配列を取得
        result = json_request["result"]
        print(result)
        # TODO: 関数でKNNを組み込む

        # DBへの新規登録
        # Review.objects.create(writer=writer_email, spot=spot_email, lang=lang, review_post=review_post, review_rating=rating_post)

        # JSON response
        # KNNでの結果に対象物と対象の説明を返す（言語別）
        data = {
        }

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CameraResult, self).dispatch(*args, **kwargs)

