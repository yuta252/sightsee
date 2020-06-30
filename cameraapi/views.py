import json
import base64

from django.http.response import HttpResponse
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from analysis.models import User, Exhibit, ExhibitPicture


User = get_user_model()


class LoginView(View):

    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)
        spotmail = json_request["spotEmail"]
        spotpass = json_request["spotPass"]

        # user, created = User.objects.get_or_create(id=spotid, email=email, username=spotname, is_superuser=False, is_staff=False, is_active=True)

        data = {}
        # Emailの存在確認
        spotuser = User.objects.filter(email=spotmail)
        is_exist = spotuser.exists()

        if is_exist:
            if spotuser[0].check_password(spotpass):
                spot_id = spotuser[0].id
                spot_name = spotuser[0].username
                # ログイン完了
                data["is_error"] = False
                data["message"] = ""
                data["spot_id"] = spot_id
                data["spot_name"] = spot_name
            else:
                data["is_error"] = True
                data["message"] = "正しいパスワードを入力してください。"
                data["spot_id"] = 0
                data["spot_name"] = ""
        else:
            data["is_error"] = True
            data["message"] = "このアカウントは存在しません。"
            data["spot_id"] = 0
            data["spot_name"] = ""

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)


class ExhibitView(View):
    DEBUG_URL = 'http://10.0.2.2:80/'

    def get(self, request, *args, **kwargs):
        spot_id = request.GET.get('s')
        print(spot_id)

        data = {}
        data["Search"] = []

        spot_list = User.objects.filter(id=spot_id).order_by('date_joined').reverse()

        for spot in spot_list:
            # TODO: 本番環境では画像処理変更
            exhibit_list = spot.exhibit_owner.all()

            for exhibit in exhibit_list:
                exhibit_name = exhibit.exhibit_name
                thumbnail_list = exhibit.exhibit_pk.all()
                thumbnail_url = thumbnail_list[0].post_pic.url
                url_split = thumbnail_url.split('/')[-5:]
                url_join = '/'.join(url_split)

                spot_dict = {
                    'Title':exhibit_name,
                    'Thumbnail':self.DEBUG_URL + url_join,
                }
                data["Search"].append(spot_dict)

        data = json.dumps(data, indent=5, ensure_ascii=False)
        return HttpResponse(data, content_type='application/json')


class ResultView(View):
    def get(self, request, *args, **kwargs):
        data = {}
        return HttpResponse(data, content_type='application/json')

    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)
        spotid = json_request["spotId"]
        exhibit_id = json_request["exhibitId"]
        exhibitname = json_request["exhibitName"]
        image = json_request["image"]
        postnumber = json_request["postNum"]
        print(exhibit_id)

        # base64エンコード
        image_decoded = ContentFile(base64.b64decode(image), name='image_decoded.jpg')

        spot_list = User.objects.get(id=spotid)
        data = {}

        if( postnumber == 1):
            # 初回の投稿処理
            exhibit, created = Exhibit.objects.get_or_create(owner=spot_list, exhibit_name=exhibitname)
            ExhibitPicture.objects.create(exhibit_id=exhibit, post_pic=image_decoded)
            data = {
                'is_error':False,
                'message':"",
                'exhibit_id':exhibit.id,
            }
        else:
            # 2回目以降の投稿処理
            exhibit = Exhibit.objects.get(id=exhibit_id)
            print(exhibit)
            ExhibitPicture.objects.create(exhibit_id=exhibit, post_pic=image_decoded)
            data = {
                'is_error':False,
                'message':"",
                'exhibit_id':exhibit_id,
            }

        data = json.dumps(data, indent=5, ensure_ascii=False)
        print(data)
        return HttpResponse(data, content_type='application/json')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ResultView, self).dispatch(*args, **kwargs)
