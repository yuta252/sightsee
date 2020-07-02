import hashlib
import json
from logging import DEBUG, Formatter, FileHandler, getLogger
import math
import os
import random
import uuid

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Q
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from analysis.models import User, Exhibit, ExhibitPicture, UserLang
from api.models import AppUser, Review, Like
from api.recognize.classification import run

User = get_user_model()

logger = getLogger(__name__)
log_fmt = Formatter('%(asctime)s %(name)s %(lineno)d [%(levelname)s][%(funcName)s] %(message)s')
path_apilog = os.path.dirname(os.path.abspath(__file__))
handler = FileHandler(os.path.join(path_apilog, 'log/views.py.log'), 'a')
handler.setLevel('INFO')
handler.setFormatter(log_fmt)
logger.setLevel(DEBUG)
logger.addHandler(handler)

category_list = {
    '00': '-', '11': '山岳', '12': '高原・湿原・原野', '13': '湖沼',
    '14': '河川・渓谷', '15': '滝', '16': '海岸・岬', '17': '岩石・洞窟',
    '18': '動物', '19': '植物', '21': '史跡', '22': '神社・寺院・教会',
    '23': '城跡・宮殿', '24': '集落・街', '25': '郷土景観', '26': '庭園・公園',
    '27': '建造物', '28': '年中行事（祭り・伝統行事）', '29': '動植物園・水族館', '30': '博物館・美術館',
    '31': 'テーマ公園・テーマ施設', '32': '温泉', '33': '食', '34': '芸能・イベント'
}

category_list_en = {
    '00': '-', '11': 'Mountains', '12': 'Plateau・Wetlands・Wilderness', '13': 'Lake',
    '14': 'River・Valley', '15': 'Waterfall', '16': 'Beach・Cape', '17': 'Rocks・Cave',
    '18': 'Animal', '19': 'Plant', '21': 'Historic site', '22': 'Religious building',
    '23': 'Castle ruins・Palace', '24': 'Village・Town', '25': 'Local landscape', '26': 'Garden・Park',
    '27': 'Building', '28': 'Annual event（festival・traditional event）', '29': 'Zoo・Botanical garden・Aquarium', '30': 'Museum・Art museum',
    '31': 'Theme facility', '32': 'Hot spring', '33': 'Food', '34': 'Entertainment・Event'
}
# TODO: 言語ごとにカテゴリーリストを定義
category_list_other = {
    '00': '-', '11': 'Mountains', '12': 'Plateau・Wetlands・Wilderness', '13': 'Lake',
    '14': 'River・Valley', '15': 'Waterfall', '16': 'Beach・Cape', '17': 'Rocks・Cave',
    '18': 'Animal', '19': 'Plant', '21': 'Historic site', '22': 'Religious building',
    '23': 'Castle ruins・Palace', '24': 'Village・Town', '25': 'Local landscape', '26': 'Garden・Park',
    '27': 'Building', '28': 'Annual event（festival・traditional event）', '29': 'Zoo・Botanical garden・Aquarium', '30': 'Museum・Art museum',
    '31': 'Theme facility', '32': 'Hot spring', '33': 'Food', '34': 'Entertainment・Event'
}


def ImageUrl():
    """
        開発環境用の画像ファイル参照用Path
        1. ローカル検証　is_Simulator = True
        2. 実機検証　is_Simulator = False
    """
    is_Simulator = False
    if is_Simulator:
        return 'http://0.0.0.0:80/'
    else:
        return 'http://startlens.local/'


class AuthMailView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        email = json_request["auth"]["email"]
        password = json_request["auth"]["password"]
        language = json_request["auth"]["language"]
        country = json_request["auth"]["country"]

        user = AppUser.objects.filter(email=email)
        if user.exists():
            # メールアドレスが既に登録されている、かつ認証済みの場合
            if not user[0].is_active:
                data["error"] = {"message": "入力されたメールアドレスは既に登録済みです"}
                data["result"] = {"authcode": 0}
            else:
                # メールアドレスが既に登録されている、かつ認証されていない場合
                auth_code = random.randrange(1000, 9999)
                self.send_mail(email=email, authcode=auth_code, language=language)
                self.save_database(email=email, password=password, language=language, country=country)
                # JSON response
                data["error"] = {"message": ""}
                data["result"] = {"authcode": auth_code}
        else:
            # メールが登録されていない新規登録もしくは認証されていない場合
            auth_code = random.randrange(1000, 9999)
            self.send_mail(email=email, authcode=auth_code, language=language)
            self.save_database(email=email, password=password, language=language, country=country)
            # JSON response
            data["error"] = {"message": ""}
            data["result"] = {"authcode": auth_code}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def send_mail(self, email, authcode, language):
        """
            1. 日本語メールの送信
            2. 英語メールの送信
            3. 多言語メールの送信（ファイルが存在しない場合はデフォルトで英語メールを送信）
        """
        context = {
            'email': email,
            'auth_code': authcode,
        }

        try:
            if language == "ja":
                subject = render_to_string('api/mail_template/email_auth/ja_subject.txt', context)
                content = render_to_string('api/mail_template/email_auth/ja_message.txt', context)
            elif language == "en":
                subject = render_to_string('api/mail_template/email_auth/en_subject.txt', context)
                content = render_to_string('api/mail_template/email_auth/en_message.txt', context)
            else:
                subject = render_to_string('api/mail_template/email_auth/{}_subject.txt'.format(language), context)
                content = render_to_string('api/mail_template/email_auth/{}_message.txt'.format(language), context)
        except FileNotFoundError:
            logger.info("メッセージ言語ファイルが存在しません。")
            subject = render_to_string('api/mail_template/email_auth/en_subject.txt', context)
            content = render_to_string('api/mail_template/email_auth/en_message.txt', context)
        except Exception as e:
            logger.info("メッセージ言語ファイルが存在しません。\n error:{}".format(e))
            print("メールを送信できませんでした\nerror:{}".format(e))
            subject = render_to_string('api/mail_template/email_auth/en_subject.txt', context)
            content = render_to_string('api/mail_template/email_auth/en_message.txt', context)
        # TODO: 本番環境用にメールアドレスを更新
        send_mail(subject, content, 'no-reply@startlens.com', [email])

    def save_database(self, email, password, language, country):
        """
            パスワードをハッシュ化してデータベースに登録する
            データベースに登録できなかった場合はエラーを返す
        """
        try:
            hashedpassword = hashlib.md5(password.encode()).hexdigest()
            AppUser.objects.create(email=email, password=hashedpassword, language=language, country=country, is_active=False)
        except IntegrityError as e:
            print("データベースに登録できませんでした\nerror:{}".format(e))
            logger.info("データベースに登録できませんでした\n user:%s \n error: %s", email, e)
        except Exception as e:
            print("データベースに登録できませんでした\nerror:{}".format(e))
            logger.info("データベースに登録できませんでした\n user:%s \n error: %s", email, e)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AuthMailView, self).dispatch(*args, **kwargs)


class AuthSuccessView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        email = json_request["auth"]["email"]

        # APIkeyの生成
        user = AppUser.objects.get(email=email)
        apikey = str(uuid.uuid4())
        user.apikey = apikey
        user.is_active = True
        user.save()

        data["result"] = {
            "authsuccess": True,
            "apikey": apikey
        }
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AuthSuccessView, self).dispatch(*args, **kwargs)


class QuestionResisterView(View):
    def get(self, request, *args, **kwargs):
        # API Keyの取得
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        apikey = json_request["answer"]["apikey"]
        sex = json_request["answer"]["sex"]
        year = json_request["answer"]["year"]

        user = AppUser.objects.get(apikey=apikey)
        user.sex = sex
        user.year = year
        user.save()

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(QuestionResisterView, self).dispatch(*args, **kwargs)


class LogInView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        email = json_request["auth"]["email"]
        enteredpassword = json_request["auth"]["password"]

        user = AppUser.objects.filter(email=email)

        if user.exists():
            # 既にメールアドレス登録されている場合
            db_password = user[0].password
            # パスワードのハッシュ化
            hashedpassword = hashlib.md5(enteredpassword.encode()).hexdigest()

            if hashedpassword == db_password:
                # データベースのパスワードと一致（ログイン成功）
                data["error"] = {"message": ""}
                data["result"] = {"authsuccess": True, "apikey": user[0].apikey}
            else:
                data["error"] = {"message": "入力されたパスワードが一致しません"}
                data["result"] = {"authsuccess": False, "apikey": ""}
        else:
            # メールアドレスが登録されていない
            data["error"] = {"message": "入力されたメールアドレスは登録されていません"}
            data["result"] = {"authsuccess": False, "apikey": ""}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(LogInView, self).dispatch(*args, **kwargs)


class PassResetView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        email = json_request["auth"]["email"]
        language = json_request["auth"]["language"]

        user = AppUser.objects.filter(email=email)

        if not user.exists():
            # メールアドレスが登録されていない場合
            data["error"] = {"message": "入力されたメールアドレスは登録されていません"}
            data["result"] = {"authcode": 0}
        else:
            # メールが登録されている場合
            auth_code = random.randrange(1000, 9999)
            self.send_mail(email=email, authcode=auth_code, language=language)
            # JSON response
            data["error"] = {"message": ""}
            data["result"] = {"authcode": auth_code}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def send_mail(self, email, authcode, language):
        """
            1. 日本語メールの送信
            2. 英語メールの送信
            3. 多言語メールの送信（ファイルが存在しない場合はデフォルトで英語メールを送信）
        """
        context = {
            'email': email,
            'auth_code': authcode,
        }

        try:
            if language == "ja":
                subject = render_to_string('api/mail_template/password_reset/ja_reset_subject.txt', context)
                content = render_to_string('api/mail_template/password_reset/ja_reset_message.txt', context)
            elif language == "en":
                subject = render_to_string('api/mail_template/password_reset/en_reset_subject.txt', context)
                content = render_to_string('api/mail_template/password_reset/en_reset_message.txt', context)
            else:
                subject = render_to_string('api/mail_template/password_reset/{}_reset_subject.txt'.format(language), context)
                content = render_to_string('api/mail_template/password_reset/{}_reset_message.txt'.format(language), context)
        except FileNotFoundError:
            logger.info("メッセージ言語ファイルが存在しません。\n error: FileNotFoundError")
            subject = render_to_string('api/mail_template/password_reset/en_reset_subject.txt', context)
            content = render_to_string('api/mail_template/password_reset/en_reset_message.txt', context)
        except Exception as e:
            logger.info("メッセージ言語ファイルが存在しません。\n error:{}".format(e))
            print("メールを送信できませんでした\nerror:{}".format(e))
            subject = render_to_string('api/mail_template/password_reset/en_reset_subject.txt', context)
            content = render_to_string('api/mail_template/password_reset/en_reset_message.txt', context)
        # TODO: 本番環境用にメールアドレスを更新
        send_mail(subject, content, 'no-reply@startlens.com', [email])

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(PassResetView, self).dispatch(*args, **kwargs)


class PassAuthView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        email = json_request["auth"]["email"]

        # 認証成功(API生成)
        user = AppUser.objects.get(email=email)
        apikey = str(uuid.uuid4())
        user.apikey = apikey
        user.save()

        data["result"] = {
            "authsuccess": True,
            "apikey": apikey
        }
        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(PassAuthView, self).dispatch(*args, **kwargs)


class PassSendView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        apikey = json_request["auth"]["apikey"]
        password = json_request["auth"]["password"]

        user = AppUser.objects.get(apikey=apikey)
        if user.exists():
            hashedpassword = hashlib.md5(password.encode()).hexdigest()
            user.password = hashedpassword
            user.save()
            data["result"] = {"authsuccess": True}
        else:
            data["result"] = {"authsuccess": False}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(PassSendView, self).dispatch(*args, **kwargs)


class HomeView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        # TODO: 多言語処理
        apikey = request.GET.get('key')
        search_word = request.GET.get('q')
        language = request.GET.get('lang')

        if language == 'ja':
            data = self.get_json_ja(apikey, language, search_word)
        else:
            data = self.get_json_other(apikey, language, search_word)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, apikey, language, query):
        """
            検索クエリをもとに日本語のJSONデータを返す関数
        """
        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        if(query == 'all'):
            spot_list = User.objects.filter(is_staff=False).order_by('date_joined').reverse()
        else:
            spot_list = User.objects.filter(
                Q(username__icontains=query) |
                Q(address_city__icontains=query) |
                Q(address_street__icontains=query),
                is_staff=False).order_by('date_joined').reverse()

        for spot in spot_list:
            # TODO: 本番環境でのURL変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)

            if spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
                ratingamount = spot.rating_amount
            address = str(spot.address_prefecture) + str(spot.address_city) + str(spot.address_street)
            is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()

            spot_dict = {
                'spotTitle': spot.username,
                'category': category_list[spot.major_category],
                'thumbnail': self.DEBUG_URL + url_join,
                'address': address,
                'ratingstar': ratingstar,
                'ratingAmount': ratingamount,
                'spotpk': spot.pk,
                'like': is_like,
            }
            data["result"].append(spot_dict)

        data["info"]["num"] = spot_list.count()
        data["error"]["message"] = ""
        return data

    def get_json_other(self, apikey, language, query):
        """
            検索クエリをもとに日本語以外のJSONデータを返す関数
            優先表示
            1. ClientのAPIrequestから取得した言語
            2. クエリの表示結果がない場合は英語をデフォルトで表示する
        """
        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        spot_list = UserLang.objects.filter(language=language, owner__is_staff=False)

        if spot_list.exists():
            # 優先言語（ClientのAPIrequestから取得した言語コード）がある場合
            if (query == 'all'):
                spot_list = spot_list.order_by('upload_date').reverse()
            else:
                spot_list = spot_list.filter(Q(username__icontains=query) | Q(address_city__icontains=query) | Q(address_street__icontains=query)).order_by('upload_date').reverse()
        else:
            # 優先言語がない場合にデフォルトで英語を表示する
            if(query == 'all'):
                spot_list = UserLang.objects.filter(language='en', owner__is_staff=False).order_by('upload_date').reverse()
            else:
                spot_list = UserLang.objects.filter(Q(username__icontains=query) | Q(address_city__icontains=query) | Q(address_street__icontains=query), language='en', owner__is_staff=False).order_by('upload_date').reverse()

        for spot_lang in spot_list:
            spot = spot_lang.owner
            # TODO: 本番環境でのURL変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)

            if spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
                ratingamount = spot.rating_amount
            address = str(spot_lang.address_street) + ',' + str(spot_lang.address_city) + ',' + str(spot_lang.address_prefecture)
            is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()

            if language == 'en':
                category = category_list_en[spot.major_category]
            else:
                category = category_list_other[spot.major_category]

            spot_dict = {
                'spotTitle': spot_lang.username,
                'category': category,
                'thumbnail': self.DEBUG_URL + url_join,
                'address': address,
                'ratingstar': ratingstar,
                'ratingAmount': ratingamount,
                'spotpk': spot.pk,
                'like': is_like,
            }
            data["result"].append(spot_dict)
        data["info"]["num"] = spot_list.count()
        data["error"]["message"] = ""
        return data


class SearchView(View):

    DEBUG_URL = ImageUrl()

    category_mapping = {
        '0': ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20'],
        '1': ['21'], '2': ['22'], '3': ['23'], '4': ['24', '25'], '5': ['26'], '6': ['27'], '7': ['28'],
        '8': ['29'], '9': ['30'], '10': ['31'], '11': ['32'], '12': ['33'], '13': ['34']
    }

    def get(self, request, *args, **kwargs):
        # TODO: 多言語処理
        apikey = request.GET.get('key')
        language = request.GET.get('lang')
        category = request.GET.get('cat')
        city = request.GET.get('city')

        if language == 'ja':
            data = self.get_json_ja(apikey, language, city, category)
        else:
            data = self.get_json_other(apikey, language, city, category)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, apikey, language, city, category):
        """
            検索クエリをもとに日本語のJSONデータを返す関数
        """
        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        if (city != 'all' and category != 'all'):
            # 場所とカテゴリーで検索
            spot_list = User.objects.filter(address_city__icontains=city, major_category__in=self.category_mapping[category], is_staff=False).order_by('date_joined').reverse()
        elif (city != 'all'):
            # 場所で検索
            spot_list = User.objects.filter(address_city__icontains=city, is_staff=False).order_by('date_joined').reverse()
        elif (category != 'all'):
            # カテゴリーで検索
            spot_list = User.objects.filter(major_category__in=self.category_mapping[category], is_staff=False).order_by('date_joined').reverse()
        else:
            spot_list = User.objects.filter(is_staff=False).order_by('date_joined').reverse()

        for spot in spot_list:
            # TODO: 本番環境でのURL変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)

            if spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
                ratingamount = spot.rating_amount
            address = str(spot.address_prefecture) + str(spot.address_city) + str(spot.address_street)
            is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()
            spot_dict = {
                'spotTitle': spot.username,
                'category': category_list[spot.major_category],
                'thumbnail': self.DEBUG_URL + url_join,
                'address': address,
                'ratingstar': ratingstar,
                'ratingAmount': ratingamount,
                'spotpk': spot.pk,
                'like': is_like,
            }
            data["result"].append(spot_dict)

        data["info"]["num"] = spot_list.count()
        data["error"]["message"] = ""
        return data

    def get_json_other(self, apikey, language, city, category):
        """
            検索クエリをもとに日本語以外のJSONデータを返す関数
            優先表示
            1. ClientのAPIrequestから取得した言語
            2. クエリの表示結果がない場合は英語をデフォルトで表示する
        """
        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        spot_list = UserLang.objects.filter(language=language, owner__is_staff=False)

        if spot_list.exists():
            # 優先言語（ClientのAPIrequestから取得した言語コード）がある場合
            if (city != 'all' and category != 'all'):
                # 場所とカテゴリーで検索
                spot_list = spot_list.filter(address_city__icontains=city, owner__major_category__in=self.category_mapping[category]).order_by('upload_date').reverse()
            elif (city != 'all'):
                # 場所で検索
                spot_list = spot_list.filter(address_city__icontains=city).order_by('upload_date').reverse()
            elif (category != 'all'):
                # カテゴリーで検索
                spot_list = spot_list.filter(owner__major_category__in=self.category_mapping[category]).order_by('upload_date').reverse()
            else:
                spot_list = spot_list.order_by('date_joined').reverse()
        else:
            # 優先言語がない場合にデフォルトで英語を表示する
            if (city != 'all' and category != 'all'):
                # 場所とカテゴリーで検索
                spot_list = UserLang.objects.filter(language='en', address_city__icontains=city, owner__major_category__in=self.category_mapping[category]).order_by('upload_date').reverse()
            elif (city != 'all'):
                # 場所で検索
                spot_list = UserLang.objects.filter(language='en', address_city__icontains=city).order_by('upload_date').reverse()
            elif (category != 'all'):
                # カテゴリーで検索
                spot_list = UserLang.objects.filter(language='en', owner__major_category__in=self.category_mapping[category]).order_by('upload_date').reverse()
            else:
                spot_list = UserLang.objects.filter(language='en').order_by('upload_date').reverse()

        for spot_lang in spot_list:
            spot = spot_lang.owner
            # TODO: 本番環境でのURL変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)

            if spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
                ratingamount = spot.rating_amount
            address = str(spot_lang.address_street) + ',' + str(spot_lang.address_city) + ',' + str(spot_lang.address_prefecture)
            is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()

            if language == 'en':
                category = category_list_en[spot.major_category]
            else:
                category = category_list_other[spot.major_category]

            spot_dict = {
                'spotTitle': spot_lang.username,
                'category': category,
                'thumbnail': self.DEBUG_URL + url_join,
                'address': address,
                'ratingstar': ratingstar,
                'ratingAmount': ratingamount,
                'spotpk': spot.pk,
                'like': is_like,
            }
            data["result"].append(spot_dict)
        data["info"]["num"] = spot_list.count()
        data["error"]["message"] = ""
        return data


class LikeView(View):
    def get(self, request, *args, **kwargs):
        apikey = request.GET.get('key')
        spot = int(request.GET.get('spot'))
        spot_obj = User.objects.get(id=spot)
        is_like = request.GET.get('islike')

        data = {}
        data["result"] = {}
        data["error"] = {}

        if is_like == "1":
            # 登録処理
            try:
                Like.objects.create(apikey=apikey, spot=spot_obj)
            except IntegrityError as e:
                logger.info("データベースに登録できませんでした。\n error:{}".format(e))
            except Exception as e:
                logger.info("データベースに登録できませんでした。\n error:{}".format(e))
        elif is_like == "0":
            # 削除処理
            try:
                Like.objects.filter(apikey=apikey, spot=spot_obj).delete()
            except Exception as e:
                logger.info("データベースを削除できませんでした。\n error:{}".format(e))
        else:
            logger.info("例外コード発生。\n error:{}".format(e))

        data["result"]["like"] = True
        data["error"]["message"] = ""
        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')


class FavoriteView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        apikey = request.GET.get('key')
        language = request.GET.get('lang')

        if language == 'ja':
            data = self.get_json_ja(apikey, language)
        else:
            data = self.get_json_other(apikey, language)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, apikey, language):
        """
            日本語のJSONデータを返す関数
        """
        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        like_list = Like.objects.filter(apikey=apikey).order_by('date_posted').reverse()

        for like in like_list:
            # TODO: 本番環境でのURL変更
            thumbnail_url = like.spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)

            if like.spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((like.spot.rating_sum / like.spot.rating_amount), 1)
                ratingamount = like.spot.rating_amount
            address = str(like.spot.address_prefecture) + str(like.spot.address_city) + str(like.spot.address_street)

            spot_dict = {
                'spotTitle': like.spot.username,
                'category': category_list[like.spot.major_category],
                'thumbnail': self.DEBUG_URL + url_join,
                'address': address,
                'ratingstar': ratingstar,
                'ratingAmount': ratingamount,
                'spotpk': like.spot.pk,
                'like': True,
            }
            data["result"].append(spot_dict)

        data["info"]["num"] = like_list.count()
        data["error"]["message"] = ""
        return data

    def get_json_other(self, apikey, language):
        """
            日本語以外のJSONデータを返す関数
            優先表示
            1. ClientのAPIrequestから取得した言語
            2. クエリの表示結果がない場合は英語をデフォルトで表示する
        """
        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        like_list = Like.objects.filter(apikey=apikey).order_by('date_posted').reverse()

        for like in like_list:
            # TODO: 本番環境でのURL変更
            thumbnail_url = like.spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)

            if like.spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((like.spot.rating_sum / like.spot.rating_amount), 1)
                ratingamount = like.spot.rating_amount

            lang_obj = UserLang.objects.filter(owner=like.spot, language=language)
            if not lang_obj.exists():
                # 優先言語がない場合にデフォルトで英語を表示する
                lang_obj = UserLang.objects.filter(owner=like.spot, language='en')

            try:
                address = str(lang_obj[0].address_city) + str(lang_obj[0].address_street) + str(lang_obj[0].address_prefecture)
                if language == 'en':
                    category = category_list_en[like.spot.major_category]
                else:
                    category = category_list_other[like.spot.major_category]

                spot_dict = {
                    'spotTitle': lang_obj[0].username,
                    'category': category,
                    'thumbnail': self.DEBUG_URL + url_join,
                    'address': address,
                    'ratingstar': ratingstar,
                    'ratingAmount': ratingamount,
                    'spotpk': like.spot.pk,
                    'like': True,
                }
                data["result"].append(spot_dict)
            except IndexError as e:
                logger.info("%s: ベースの英語での登録がありません。 \nerror: %s", like.spot.username, e)

        data["info"]["num"] = len(data["result"])
        data["error"]["message"] = ""
        return data


class SpotDetailView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        # TODO: 多言語処理
        apikey = request.GET.get('key')
        spot_pk = request.GET.get('spot')
        language = request.GET.get('lang')

        if language == 'ja':
            data = self.get_json_ja(apikey, spot_pk, language)
        else:
            data = self.get_json_other(apikey, spot_pk, language)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, apikey, spot_pk, language):
        """
            日本語のJSONデータを返す関数
        """
        data = {}
        data["result"] = {}
        data["result"]["review"] = []
        data["result"]["recommend"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        thumbnail_url = spot.thumbnail.url
        url_split = thumbnail_url.split('/')[-4:]
        url_join = '/'.join(url_split)

        if spot.rating_amount == 0:
            ratingstar = 0
            ratingamount = 0
        else:
            ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
            ratingamount = spot.rating_amount
        address = str(spot.address_prefecture) + str(spot.address_city) + str(spot.address_street)
        is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()

        data["result"]["spot"] = {
            "spotTitle": spot.username,
            "category": category_list[spot.major_category],
            "thumbnail": self.DEBUG_URL + url_join,
            "address": address,
            "ratingstar": ratingstar,
            "ratingAmount": ratingamount,
            "spotpk": spot.pk,
            "like": is_like,
            "intro": spot.self_intro,
            "telephone": spot.telephone,
            "url": spot.url,
            "fee": spot.entrance_fee,
            "businessHour": spot.business_hours,
            "holiday": spot.holiday,
        }

        # reviewを取得
        review_list = Review.objects.filter(spot=spot)
        review_num = min(review_list.count(), 2)
        data["info"]["reviewNum"] = review_num

        for review in review_list[:review_num]:
            review_dict = {
                "writer": self.mask_name(review.writer.email),
                "ratingstar": review.review_rating,
                "postedreview": review.review_post,
                "posteddate": review.date_posted.date().strftime('%Y年%m月%d日'),
            }
            data["result"]["review"].append(review_dict)

        # recommendを取得
        recommend_list = Exhibit.objects.filter(owner=spot)
        recommend_num = min(recommend_list.count(), 4)
        data["info"]["recommendNum"] = recommend_num

        for recommend in recommend_list[:recommend_num]:
            recommend_picture = ExhibitPicture.objects.filter(exhibit_id=recommend)[0]
            picture_url = recommend_picture.post_pic.url
            picture_url_split = picture_url.split('/')[-5:]
            picture_url_join = '/'.join(picture_url_split)

            recommend_dict = {
                "exhibitId": recommend.id,
                "exhibitName": recommend.exhibit_name,
                "exhibitUrl": self.DEBUG_URL + picture_url_join,
            }
            data["result"]["recommend"].append(recommend_dict)

        data["error"]["message"] = ""
        return data

    def get_json_other(self, apikey, spot_pk, language):
        """
            日本語以外のJSONデータを返す関数
            優先表示
            1. ClientのAPIrequestから取得した言語
            2. クエリの表示結果がない場合は英語をデフォルトで表示する
        """
        data = {}
        data["result"] = {}
        data["result"]["review"] = []
        data["result"]["recommend"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        thumbnail_url = spot.thumbnail.url
        url_split = thumbnail_url.split('/')[-4:]
        url_join = '/'.join(url_split)

        if spot.rating_amount == 0:
            ratingstar = 0
            ratingamount = 0
        else:
            ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
            ratingamount = spot.rating_amount

        is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()

        lang_obj = UserLang.objects.filter(owner=spot, language=language)
        if not lang_obj.exists():
            # 優先言語がない場合にデフォルトで英語を表示する
            lang_obj = UserLang.objects.filter(owner=spot, language='en')

        try:
            address = str(lang_obj[0].address_street) + ',' + str(lang_obj[0].address_city) + ',' + str(lang_obj[0].address_prefecture)
            if language == 'en':
                category = category_list_en[spot.major_category]
            else:
                category = category_list_other[spot.major_category]

            username = lang_obj[0].username
            introduction = lang_obj[0].self_intro
            fee = lang_obj[0].entrance_fee
            business_hours = lang_obj[0].business_hours
            holiday = lang_obj[0].holiday

        except IndexError as e:
            logger.info("%s: ベースの英語での登録がありません。 \nerror: %s", spot.username, e)

        data["result"]["spot"] = {
            "spotTitle": username,
            "category": category,
            "thumbnail": self.DEBUG_URL + url_join,
            "address": address,
            "ratingstar": ratingstar,
            "ratingAmount": ratingamount,
            "spotpk": spot.pk,
            "like": is_like,
            "intro": introduction,
            "telephone": spot.telephone,
            "url": spot.url,
            "fee": fee,
            "businessHour": business_hours,
            "holiday": holiday,
        }

        # reviewを取得
        if language == 'en':
            # 英語の場合は英語のみ取得する
            review_list = Review.objects.filter(spot=spot, lang='en')
        else:
            # 多言語の場合は多言語かつ英語のレビューを表示する
            review_list = Review.objects.filter(Q(lang=language) | Q(lang='en'), spot=spot)

        review_num = min(review_list.count(), 2)
        data["info"]["reviewNum"] = review_num

        for review in review_list[:review_num]:
            review_dict = {
                "writer": self.mask_name(review.writer.email),
                "ratingstar": review.review_rating,
                "postedreview": review.review_post,
                "posteddate": review.date_posted.date().strftime('%m/%d/%Y'),
            }
            data["result"]["review"].append(review_dict)

        recommend_list = Exhibit.objects.filter(owner=spot)
        recommend_num = min(recommend_list.count(), 4)
        data["info"]["recommendNum"] = recommend_num

        for recommend in recommend_list[:recommend_num]:
            recommend_picture = ExhibitPicture.objects.filter(exhibit_id=recommend)[0]
            picture_url = recommend_picture.post_pic.url
            picture_url_split = picture_url.split('/')[-5:]
            picture_url_join = '/'.join(picture_url_split)
            """
            言語ごとに処理を分ける。言語の説明文がない場合は英語をデフォルトで表示する
            TODO: データベースの構造を修正が必要(WebViewも要修正)
            """
            if language == 'zh':
                exhibit_name = recommend.exhibit_name_zh
                if len(exhibit_name) == 0:
                    exhibit_name = recommend.exhibit_name_en
            else:
                exhibit_name = recommend.exhibit_name_en

            recommend_dict = {
                "exhibitId": recommend.id,
                "exhibitName": exhibit_name,
                "exhibitUrl": self.DEBUG_URL + picture_url_join,
            }
            data["result"]["recommend"].append(recommend_dict)
        data["error"]["message"] = ""
        return data

    def mask_name(self, name):
        """
        メールアドレスをマスキングする関数
        ランダムにアドレスの7割の文字をマスキングする
        """
        index_list = self.rand_choice(start=0, end=len(name) - 1, num=math.floor((len(name) - 1) * 0.7))
        name_list = list(name)
        for s in index_list:
            name_list[s] = "*"
        masked_name = "".join(name_list)
        return masked_name

    def rand_choice(self, start, end, num):
        index_list = []
        while len(index_list) < num:
            index = random.randint(start, end)
            if index not in index_list:
                index_list.append(index)
        return index_list


class PostReviewView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        spot_pk = int(json_request["spot"])
        apikey = json_request["apikey"]
        review = json_request["review"]
        rating = float(json_request["rating"])
        language = json_request["lang"]

        spot = User.objects.get(id=spot_pk)
        user = AppUser.objects.get(apikey=apikey)
        review_obj = Review.objects.filter(spot=spot, writer=user)
        if review_obj.exists():
            # 既にレビューが存在する場合
            data["error"] = {"message": "すでにレビューを投稿しています。"}
        else:
            try:
                Review.objects.create(spot=spot, writer=user, lang=language, review_post=review, review_rating=rating)
                tmp_sum = spot.rating_sum + rating
                tmp_amount = spot.rating_amount + 1
                spot.rating_sum = tmp_sum
                spot.rating_amount = tmp_amount
                spot.save()
            except IntegrityError as e:
                logger.info("Appuser: %s, Spot %s, データベースに登録できませんでした\nerror:%s", user, spot, e)
            except Exception as e:
                logger.info("Appuser: %s, Spot %s, データベースに登録できませんでした\nerror:%s", user, spot, e)

            data["error"] = {"message": ""}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(PostReviewView, self).dispatch(*args, **kwargs)


class ReviewListView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        spot_pk = request.GET.get('spot')
        language = request.GET.get('lang')

        if language == 'ja':
            data = self.get_json_ja(spot_pk, language)
        else:
            data = self.get_json_other(spot_pk, language)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, spot_pk, language):
        """
            日本語のJSONデータを返す関数
        """
        data = {}
        data["result"] = {}
        data["result"]["review"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        review_list = Review.objects.filter(spot=spot, lang='ja')
        review_num = min(review_list.count(), 100)
        data["info"]["reviewNum"] = review_list.count()

        for review in review_list[:review_num]:
            review_dict = {
                "writer": self.mask_name(review.writer.email),
                "ratingstar": review.review_rating,
                "postedreview": review.review_post,
                "posteddate": review.date_posted.date().strftime('%Y年%m月%d日'),
            }
            data["result"]["review"].append(review_dict)

        data["error"]["message"] = ""

        return data

    def get_json_other(self, spot_pk, language):
        """
            日本語以外のJSONデータを返す関数
            優先表示言語
            1. ClienetAPIrequestの言語コード
            2. 英語（デフォルト）
        """
        data = {}
        data["result"] = {}
        data["result"]["review"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        if language == 'en':
            # 英語の場合は英語のみ取得する
            review_list = Review.objects.filter(spot=spot, lang='en')
        else:
            # 多言語の場合は多言語かつ英語のレビューを表示する
            review_list = Review.objects.filter(Q(lang=language) | Q(lang='en'), spot=spot)

        review_num = min(review_list.count(), 100)
        data["info"]["reviewNum"] = review_list.count()

        for review in review_list[:review_num]:
            review_dict = {
                "writer": self.mask_name(review.writer.email),
                "ratingstar": review.review_rating,
                "postedreview": review.review_post,
                "posteddate": review.date_posted.date().strftime('%m/%d/%Y'),
            }
            data["result"]["review"].append(review_dict)
        data["error"]["message"] = ""
        return data

    def mask_name(self, name):
        """
        メールアドレスをマスキングする関数
        ランダムにアドレスの6割の文字をマスキングする
        """
        index_list = self.rand_choice(start=0, end=len(name) - 1, num=math.floor((len(name) - 1) * 0.7))
        print(index_list)
        name_list = list(name)
        for s in index_list:
            name_list[s] = "*"
        masked_name = "".join(name_list)
        print(masked_name)
        return masked_name

    def rand_choice(self, start, end, num):
        index_list = []
        while len(index_list) < num:
            index = random.randint(start, end)
            if index not in index_list:
                index_list.append(index)
        return index_list


class ExhibitListView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        spot_pk = request.GET.get('spot')
        language = request.GET.get('lang')

        if language == 'ja':
            data = self.get_json_ja(spot_pk, language)
        else:
            data = self.get_json_other(spot_pk, language)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, spot_pk, language):
        """
            日本語のJSONデータを返す関数
        """
        data = {}
        data["result"] = {}
        data["result"]["recommend"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        recommend_list = Exhibit.objects.filter(owner=spot)
        recommend_num = min(recommend_list.count(), 100)
        data["info"]["exhibitNum"] = recommend_num

        for recommend in recommend_list[:recommend_num]:
            recommend_picture = ExhibitPicture.objects.filter(exhibit_id=recommend)[0]
            picture_url = recommend_picture.post_pic.url
            picture_url_split = picture_url.split('/')[-5:]
            picture_url_join = '/'.join(picture_url_split)

            recommend_dict = {
                "exhibitId": recommend.id,
                "exhibitName": recommend.exhibit_name,
                "exhibitUrl": self.DEBUG_URL + picture_url_join,
            }
            data["result"]["recommend"].append(recommend_dict)
        data["error"]["message"] = ""
        return data

    def get_json_other(self, spot_pk, language):
        """
            日本語以外のJSONデータを返す関数
            優先表示言語
            1. ClienetAPIrequestの言語コード
            2. 英語（デフォルト）
        """
        data = {}
        data["result"] = {}
        data["result"]["recommend"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        recommend_list = Exhibit.objects.filter(owner=spot)
        recommend_num = min(recommend_list.count(), 100)
        data["info"]["recommendNum"] = recommend_num

        for recommend in recommend_list[:recommend_num]:
            recommend_picture = ExhibitPicture.objects.filter(exhibit_id=recommend)[0]
            picture_url = recommend_picture.post_pic.url
            picture_url_split = picture_url.split('/')[-5:]
            picture_url_join = '/'.join(picture_url_split)
            """
            言語ごとに処理を分ける。言語の説明文がない場合は英語をデフォルトで表示する
            TODO: データベースの構造を修正が必要(WebViewも要修正)
            """
            if language == 'zh':
                exhibit_name = recommend.exhibit_name_zh
                if len(exhibit_name) == 0:
                    exhibit_name = recommend.exhibit_name_en
            else:
                exhibit_name = recommend.exhibit_name_en

            recommend_dict = {
                "exhibitId": recommend.id,
                "exhibitName": exhibit_name,
                "exhibitUrl": self.DEBUG_URL + picture_url_join,
            }
            data["result"]["recommend"].append(recommend_dict)
        data["error"]["message"] = ""
        return data


class CameraView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        spot_pk = int(json_request["spot"])
        apikey = json_request["apiKey"]
        result = json_request["result"]

        spot = User.objects.get(id=spot_pk)
        # path objectをstr
        path_knn = str(spot.knn_model)
        path_csv = str(spot.exhibit_csv)
        # 推論プロセス
        exhibit_list = run(result, spot_pk, path_knn, path_csv)

        # JSON responseの生成
        data = {}
        data["error"] = {}
        data["info"] = {}
        data["result"] = []
        for exhibit_pk in exhibit_list:
            exhibit = Exhibit.objects.get(id=exhibit_pk)

            # exhibitの外部キーによりExhibitの全ての投稿写真の中から一つ選択する
            exhibit_image_url = exhibit.exhibit_pk.all()[0].post_pic.url
            # TODO: Modelのフォルダパス変更後に変更する必要あり
            url_split = exhibit_image_url.split('/')[-5:]
            url_join = '/'.join(url_split)
            print(url_join)

            exhibit_dict = {
                'exhibitId': int(exhibit_pk),
                'exhibitName': exhibit.exhibit_name,
                'exhibitUrl': self.DEBUG_URL + url_join,
            }
            data["result"].append(exhibit_dict)

        data["info"]["exhibitNum"] = len(exhibit_list)
        data["error"]["message"] = ""

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CameraView, self).dispatch(*args, **kwargs)


class ExhibitDetailView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        exhibit_pk = request.GET.get('exhibitId')
        language = request.GET.get('lang')
        apikey = request.GET.get('key')

        if language == 'ja':
            data = self.get_json_ja(exhibit_pk, language)
        else:
            data = self.get_json_other(exhibit_pk, language)

        appuser = AppUser.objects.get(apikey=apikey)
        try:
            # TODO:閲覧履歴のデータベース保存
            print("保存しました")
        except IntegrityError as e:
            logger.info("Appuser: %s, Spot %s, データベースに登録できませんでした\nerror:%s", user, spot, e)
        except Exception as e:
            logger.info("Appuser: %s, Spot %s, データベースに登録できませんでした\nerror:%s", user, spot, e)
        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')

    def get_json_ja(self, exhibit_pk, language):
        """
            日本語のJSONデータを返す関数
        """
        data = {}
        data["error"] = {}

        exhibit = Exhibit.objects.get(id=exhibit_pk)
        data["result"] = {
            "intro": exhibit.exhibit_desc,
        }
        data["error"]["message"] = ""
        return data

    def get_json_other(self, exhibit_pk, language):
        """
            日本語以外のJSONデータを返す関数
            優先表示言語
            1. ClienetAPIrequestの言語コード
            2. 英語（デフォルト）
        """
        data = {}
        data["error"] = {}

        exhibit = Exhibit.objects.get(id=exhibit_pk)
        """
        言語ごとに処理を分ける。言語の説明文がない場合は英語をデフォルトで表示する
        TODO: データベースの構造を修正が必要(WebViewも要修正)
        """
        if language == 'zh':
            exhibit_description = exhibit.exhibit_desc_zh
            if len(exhibit_description) == 0:
                exhibit_description = exhibit.exhibit_desc_en
        else:
            exhibit_description = exhibit.exhibit_desc_en

        data["result"] = {
            "intro": exhibit_description,
        }
        data["error"]["message"] = ""
        return data


class ContactView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        data = {}
        json_request = json.loads(request.body)
        apikey = json_request["apikey"]
        contact = json_request["contact"]

        user = AppUser.objects.get(apikey=apikey)

        self.send_mail(email=user.email, contact=contact)
        data["error"] = {"message": ""}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def send_mail(self, email, contact):
        # 認証メール送信
        context = {
            'email': email,
            'contact': contact,
        }
        # TODO: ユーザーによって各言語のメールを返すようにする
        subject = render_to_string('api/mail_template/contact/subject.txt', context)
        content = render_to_string('api/mail_template/contact/message.txt', context)
        send_mail(subject, content, email, ['no-reply@sight.com'])

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ContactView, self).dispatch(*args, **kwargs)
