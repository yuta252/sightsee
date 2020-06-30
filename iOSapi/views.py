import hashlib
import json
import math
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

from analysis.models import User, Exhibit, ExhibitPicture
from api.models import AppUser, Review, Like
from api.recognize.classification import run

User = get_user_model()


def ImageUrl():
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
        # TODO: パスワードのValidation(clientで処理)
        if user.exists():
            # メールアドレスが既に登録されている、かつ認証済みの場合
            if not user[0].is_active:
                data["error"] = {"message": "入力されたメールアドレスは既に登録済みです"}
                data["result"] = {"authcode": 0}
            else:
                # メールアドレスが既に登録されている、かつ認証されていない場合
                auth_code = random.randrange(1000, 9999)
                self.send_mail(email=email, authcode=auth_code)
                self.save_database(email=email, password=password, language=language, country=country)
                # JSON response
                data["error"] = {"message": ""}
                data["result"] = {"authcode": auth_code}
        else:
            # メールが登録されていない新規登録もしくは認証されていない場合
            auth_code = random.randrange(1000, 9999)
            self.send_mail(email=email, authcode=auth_code)
            self.save_database(email=email, password=password, language=language, country=country)
            # JSON response
            data["error"] = {"message": ""}
            data["result"] = {"authcode": auth_code}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def send_mail(self, email, authcode):
        # 認証メール送信
        context = {
            'email': email,
            'auth_code': authcode,
        }
        # TODO: ユーザーによって各言語のメールを返すようにする
        subject = render_to_string('api/mail_template/email_auth/subject.txt', context)
        content = render_to_string('api/mail_template/email_auth/message.txt', context)
        send_mail(subject, content, 'no-reply@sight.com', [email])

    def save_database(self, email, password, language, country):
        try:
            # パスワードのハッシュ化
            hashedpassword = hashlib.md5(password.encode()).hexdigest()
            AppUser.objects.create(email=email, password=hashedpassword, language=language, country=country, is_active=False)
        except IntegrityError as e:
            print("データベースに登録できませんでした\nerror:{}".format(e))
        except Exception as e:
            print("データベースに登録できませんでした\nerror:{}".format(e))

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AuthMailView, self).dispatch(*args, **kwargs)


class AuthSuccessView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        print("post")
        data = {}
        json_request = json.loads(request.body)
        email = json_request["auth"]["email"]
        apikey = str(uuid.uuid4())

        # 認証成功(API生成)
        user = AppUser.objects.get(email=email)
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
        print(json_request)
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
        # TODO: パスワードのValidation(clientで処理)
        if user.exists():
            # 既にメールアドレス登録されている場合
            db_password = user.password
            # パスワードのハッシュ化
            hashedpassword = hashlib.md5(enteredpassword.encode()).hexdigest()

            if hashedpassword == db_password:
                # データベースのパスワードと一致（ログイン成功）
                data["error"] = {"message": ""}
                data["result"] = {"authsuccess": True, "apikey": user.apikey}
            else:
                data["error"] = {"message": "入力されたパスワードが一致しません"}
                data["result"] = {"authsuccess": False, "apikey": ""}
        else:
            # メールアドレスが登録されていない
            data["error"] = {"message": "入力されたメールアドレスは登録されていません"}
            data["result"] = {"authsuccess": False, "apikey": ""}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
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

        user = AppUser.objects.filter(email=email)
        # TODO: パスワードのValidation(clientで処理)
        if not user.exists():
            # メールアドレスが登録されていない場合
            data["error"] = {"message": "入力されたメールアドレスは登録されていません"}
            data["result"] = {"authcode": 0}
        else:
            # メールが登録されている場合
            auth_code = random.randrange(1000, 9999)
            self.send_mail(email=email, authcode=auth_code)
            # JSON response
            data["error"] = {"message": ""}
            data["result"] = {"authcode": auth_code}

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    def send_mail(self, email, authcode):
        # 認証メール送信
        context = {
            'email': email,
            'auth_code': authcode,
        }
        # TODO: ユーザーによって各言語のメールを返すようにする
        subject = render_to_string('api/mail_template/password_reset/reset_subject.txt', context)
        content = render_to_string('api/mail_template/password_reset/reset_message.txt', context)
        send_mail(subject, content, 'no-reply@sight.com', [email])

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
        apikey = str(uuid.uuid4())

        # 認証成功(API生成)
        user = AppUser.objects.get(email=email)
        user.apikey = apikey
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
        # category = request.GET.get('cat')
        # latitude = request.GET.get('lat')
        # longitude = request.GET.get('lon')

        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        if(search_word == 'all'):
            spot_list = User.objects.filter(is_staff=False).order_by('date_joined').reverse()
        else:
            spot_list = User.objects.filter(
                Q(username__icontains=search_word) |
                Q(address_city__icontains=search_word) |
                Q(address_street__icontains=search_word),
                is_staff=False).order_by('date_joined').reverse()

        for spot in spot_list:
            # TODO: 本番環境でのURL変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)
            print(url_join)
            category_list = {
                '00': '-', '11': '山岳', '12': '高原・湿原・原野', '13': '湖沼',
                '14': '河川・渓谷', '15': '滝', '16': '海岸・岬', '17': '岩石・洞窟',
                '18': '動物', '19': '植物', '21': '史跡', '22': '神社・寺院・教会',
                '23': '城跡・宮殿', '24': '集落・街', '25': '郷土景観', '26': '庭園・公園',
                '27': '建造物', '28': '年中行事（祭り・伝統行事）', '29': '動植物園・水族館', '30': '博物館・美術館',
                '31': 'テーマ公園・テーマ施設', '32': '温泉', '33': '食', '34': '芸能・イベント'
            }

            if spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((spot.rating_sum / spot.rating_amount), 1)
                ratingamount = spot.rating_amount
            address = str(spot.address_prefecture) + str(spot.address_city) + str(spot.address_street)
            print(address)
            is_like = Like.objects.filter(apikey=apikey, spot=spot).exists()

            print(is_like)
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
            print(spot_dict)

        data["info"]["num"] = spot_list.count()
        data["error"]["message"] = ""
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')


class SearchView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        # TODO: 多言語処理
        apikey = request.GET.get('key')
        category = request.GET.get('cat')
        city = request.GET.get('city')

        data = {}
        data["result"] = []
        data["error"] = {}
        data["info"] = {}

        category_mapping = {
            '0': ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20'],
            '1': ['21'], '2': ['22'], '3': ['23'], '4': ['24', '25'], '5': ['26'], '6': ['27'], '7': ['28'],
            '8': ['29'], '9': ['30'], '10': ['31'], '11': ['32'], '12': ['33'], '13': ['34']
        }

        if (city != 'all' and category != 'all'):
            # 場所とカテゴリーで検索
            spot_list = User.objects.filter(address_city__icontains=city, major_category__in=category_mapping[category], is_staff=False).order_by('date_joined').reverse()
        elif (city != 'all'):
            # 場所で検索
            spot_list = User.objects.filter(address_city__icontains=city, is_staff=False).order_by('date_joined').reverse()
        elif (category != 'all'):
            # カテゴリーで検索
            spot_list = User.objects.filter(major_category__in=category_mapping[category], is_staff=False).order_by('date_joined').reverse()
        else:
            spot_list = User.objects.filter(is_staff=False).order_by('date_joined').reverse()

        for spot in spot_list:
            # TODO: 本番環境でのURL変更
            thumbnail_url = spot.thumbnail.url
            url_split = thumbnail_url.split('/')[-4:]
            url_join = '/'.join(url_split)
            print(url_join)
            category_list = {
                '00': '-', '11': '山岳', '12': '高原・湿原・原野', '13': '湖沼',
                '14': '河川・渓谷', '15': '滝', '16': '海岸・岬', '17': '岩石・洞窟',
                '18': '動物', '19': '植物', '21': '史跡', '22': '神社・寺院・教会',
                '23': '城跡・宮殿', '24': '集落・街', '25': '郷土景観', '26': '庭園・公園',
                '27': '建造物', '28': '年中行事（祭り・伝統行事）', '29': '動植物園・水族館', '30': '博物館・美術館',
                '31': 'テーマ公園・テーマ施設', '32': '温泉', '33': '食', '34': '芸能・イベント'
            }

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
            print(spot_dict)

        data["info"]["num"] = spot_list.count()
        data["error"]["message"] = ""
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')


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
                print("データベースに登録できませんでした\nerror:{}".format(e))
            except Exception as e:
                print("データベースに登録できませんでした\nerror:{}".format(e))
            print("データベース登録完了")
        elif is_like == "0":
            # 削除処理
            Like.objects.filter(apikey=apikey, spot=spot_obj).delete()
        else:
            print("処理が未済")

        data["result"]["like"] = True
        data["error"]["message"] = ""
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')


class FavoriteView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        # TODO: 多言語処理
        apikey = request.GET.get('key')

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
            print(url_join)
            category_list = {
                '00': '-', '11': '山岳', '12': '高原・湿原・原野', '13': '湖沼',
                '14': '河川・渓谷', '15': '滝', '16': '海岸・岬', '17': '岩石・洞窟',
                '18': '動物', '19': '植物', '21': '史跡', '22': '神社・寺院・教会',
                '23': '城跡・宮殿', '24': '集落・街', '25': '郷土景観', '26': '庭園・公園',
                '27': '建造物', '28': '年中行事（祭り・伝統行事）', '29': '動植物園・水族館', '30': '博物館・美術館',
                '31': 'テーマ公園・テーマ施設', '32': '温泉', '33': '食', '34': '芸能・イベント'
            }

            if like.spot.rating_amount == 0:
                ratingstar = 0
                ratingamount = 0
            else:
                ratingstar = round((like.spot.rating_sum / like.spot.rating_amount), 1)
                ratingamount = like.spot.rating_amount
            address = str(like.spot.address_prefecture) + str(like.spot.address_city) + str(like.spot.address_street)
            print(address)

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
            print(spot_dict)

        data["info"]["num"] = like_list.count()
        data["error"]["message"] = ""
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')


class SpotDetailView(View):

    DEBUG_URL = ImageUrl()

    def get(self, request, *args, **kwargs):
        # TODO: 多言語処理
        apikey = request.GET.get('key')
        spot_pk = request.GET.get('spot')

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
        category_list = {
            '00': '-', '11': '山岳', '12': '高原・湿原・原野', '13': '湖沼',
            '14': '河川・渓谷', '15': '滝', '16': '海岸・岬', '17': '岩石・洞窟',
            '18': '動物', '19': '植物', '21': '史跡', '22': '神社・寺院・教会',
            '23': '城跡・宮殿', '24': '集落・街', '25': '郷土景観', '26': '庭園・公園',
            '27': '建造物', '28': '年中行事（祭り・伝統行事）', '29': '動植物園・水族館', '30': '博物館・美術館',
            '31': 'テーマ公園・テーマ施設', '32': '温泉', '33': '食', '34': '芸能・イベント'
        }

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
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

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

        spot = User.objects.get(id=spot_pk)
        user = AppUser.objects.get(apikey=apikey)
        print(spot)
        print(user)
        review_obj = Review.objects.filter(spot=spot, writer=user)
        if review_obj.exists():
            # 既にレビューが存在する場合
            data["error"] = {"message": "すでにレビューを投稿しています。"}
        else:
            try:
                Review.objects.create(spot=spot, writer=user, lang="ja", review_post=review, review_rating=rating)
                tmp_sum = spot.rating_sum + rating
                tmp_amount = spot.rating_amount + 1
                spot.rating_sum = tmp_sum
                spot.rating_amount = tmp_amount
                spot.save()
            except IntegrityError as e:
                print("データベースに登録できませんでした\nerror:{}".format(e))
            except Exception as e:
                print("データベースに登録できませんでした\nerror:{}".format(e))

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
        # TODO: 多言語処理
        spot_pk = request.GET.get('spot')

        data = {}
        data["result"] = {}
        data["result"]["review"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        # reviewを取得
        review_list = Review.objects.filter(spot=spot)
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
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

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
        # TODO: 多言語処理
        spot_pk = request.GET.get('spot')

        data = {}
        data["result"] = {}
        data["result"]["recommend"] = []
        data["error"] = {}
        data["info"] = {}

        spot = User.objects.get(id=spot_pk)

        # recommendを取得
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
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')


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

        # TODO : DBへの履歴登録（トレースする）
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
        # TODO: 多言語処理
        exhibit_pk = request.GET.get('exhibitId')

        data = {}
        data["error"] = {}

        exhibit = Exhibit.objects.get(id=exhibit_pk)
        data["result"] = {
            "intro": exhibit.exhibit_desc,
        }

        data["error"]["message"] = ""
        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')


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
