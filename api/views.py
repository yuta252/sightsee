import json
import random

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from analysis.models import User, UserLang, Exhibit, ExhibitPicture
from .models import AppUser, Review
from .recognize.classification import run

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

    # DEBUG_URL = 'http://192.168.43.36/'
    DEBUG_URL = 'http://10.0.2.2:80/'

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('gl')
        country = request.GET.get('hl')
        search_word = request.GET.get('s')

        # TO Do: 他の言語も含めて拡張性のある仕様にする
        if lang == 'ja':
            data = self.get_json_ja(lang, search_word)
        else:
            data = self.get_json_other(lang, search_word)
        

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, lang, search):
        data = {}
        data["Search"] = []

        # 初期の状態(all)の場合のみ全て抽出
        if(search == 'all'):
            spot_list = User.objects.all().order_by('date_joined').reverse()
        else:
            spot_list = User.objects.filter(username__icontains=search)
        
        for spot in spot_list:
            # TODO: 本番環境では画像処理変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)
            print(url_join)

            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':self.DEBUG_URL + url_join,
                'spotpk':spot.pk
            }
            data["Search"].append(spot_dict)
        return data

    def get_json_other(self, lang, search):
        data = {}
        data["Search"] = []
        
        # 英語対応か他言語対応かは観光地による
        # ユーザーにsettingから言語を変更してもらう
        if(search == 'all'):
            spot_list = UserLang.objects.filter(language=lang)
        else:
            spot_list = UserLang.objects.filter(username__icontains=search, language=lang)
        
        for spot in spot_list:
            # TODO: 本番環境では画像処理変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)
            print(url_join)

            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':self.DEBUG_URL + url_join,
                'spotpk':spot.owner.pk
            }
            data["Search"].append(spot_dict)
        return data


class Mapapi(View):

    #DEBUG_URL = 'http://192.168.43.36/'
    DEBUG_URL = 'http://10.0.2.2:80/'

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('gl')

        # TO Do: 他の言語も含めて拡張性のある仕様にする
        if lang == 'ja':
            data = self.get_json_ja(lang)
        else:
            data = self.get_json_other(lang)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, lang):
        data = {}
        data["Search"] = []

        spot_list = User.objects.all().order_by('date_joined').reverse()

        for spot in spot_list:
            # TODO: 本番環境では画像処理変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)
            print(url_join)

            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':self.DEBUG_URL + url_join,
                'spotpk':spot.pk,
                'lat':spot.latitude,
                'lon':spot.longitude,
            }
            data["Search"].append(spot_dict)
        return data

    def get_json_other(self, lang):
        data = {}
        data["Search"] = []
        
        # 英語対応か他言語対応かは観光地による
        # ユーザーにsettingから言語を変更してもらう
        spot_list = UserLang.objects.filter(language=lang)

        for spot in spot_list:
            # TODO: 本番環境では画像処理変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)
            print(url_join)

            spot_dict = {
                'Title':spot.username,
                'Major_category':spot.major_category,
                'Thumbnail':self.DEBUG_URL + url_join,
                'spotpk':spot.owner.pk,
                'lat':spot.latitude,
                'lon':spot.longitude,
            }
            data["Search"].append(spot_dict)
        return data


class SpotDetailapi(View):
    # DEBUG_URL = 'http://192.168.43.36/'
    DEBUG_URL = 'http://10.0.2.2:80/'

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('gl')
        spot_id = request.GET.get('i')

        # TO Do: 他の言語も含めて拡張性のある仕様にする
        if lang == 'ja':
            data = self.get_json_ja(lang, spot_id)
        else:
            data = self.get_json_other(lang, spot_id)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, lang, spot_id):
        spot = User.objects.get(id=spot_id)

        # TODO: 本番環境では画像処理変更
        thumbnail_url = spot.thumbnail.url
        url_split = thumbnail_url.split('/')[-4:]
        url_join = '/'.join(url_split)
        print(url_join)
        
        data = {
            'Title':spot.username,
            'Category':spot.major_category,
            'Thumbnail':self.DEBUG_URL + url_join,
            'Information':spot.self_intro,
            'Address':spot.address_prefecture + spot.address_city + spot.address_street,
            'Telephone':spot.telephone,
            'EntranceFee':spot.entrance_fee,
            'BusinessHours':spot.business_hours,
            'Holiday':spot.holiday,
        }
        return data

    def get_json_other(self, lang, spot_id):
        spot = User.objects.get(id=spot_id)
        spotlang = spot.userlang_set.filter(language=lang)[0]

        # TODO: 本番環境では画像処理変更
        thumbnail_url = spot.thumbnail.url
        url_split = thumbnail_url.split('/')[-4:]
        url_join = '/'.join(url_split)
        print(url_join)

        data = {
            'Title':spotlang.username,
            'Category':spotlang.major_category,
            'Thumbnail':self.DEBUG_URL + url_join,
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

    # TODO : デバッグ用のURL
    #DEBUG_URL = 'http://192.168.43.36/'
    DEBUG_URL = 'http://10.0.2.2:80/'

    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)

        email = json_request["email"]
        # TODO: Android側にもJSON実装
        spotid = json_request["spot_id"]
        # 50次元の配列を取得
        result = json_request["result"]
        print(result)
        print(type(result))
        # TODO: 関数でKNNを組み込む
        # spotid: integer
        spotid = int(spotid)
        spot = User.objects.get(id=spotid)

        # path objectをstr
        path_knn = str(spot.knn_model)
        path_csv = str(spot.exhibit_csv)
        
        # 推論プロセス
        exhibit_list = run(result, spotid, path_knn, path_csv)

        # TODO : DBへの履歴登録（トレースする）
        # JSON responseの生成
        data = {}
        data["Result"] = []
        for exhibit_pk in exhibit_list:
            exhibit = Exhibit.objects.get(id=exhibit_pk)

            # exhibitの外部キーによりExhibitの全ての投稿写真の中から一つ選択する
            exhibit_image_url = exhibit.exhibit_pk.all()[0].post_pic.url
            # TODO: Modelのフォルダパス変更後に変更する必要あり
            url_split = exhibit_image_url.split('/')[-5:]
            url_join = '/'.join(url_split)
            print(url_join)

            exhibit_dict = {
                'exhibit_id':exhibit_pk,
                'exhibit_name':exhibit.exhibit_name,
                'exhibit_desc':exhibit.exhibit_desc,
                'exhibit_image': self.DEBUG_URL + url_join,
            }
            data["Result"].append(exhibit_dict)
        print(data)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CameraResult, self).dispatch(*args, **kwargs)

