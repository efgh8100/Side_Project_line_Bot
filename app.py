import sys
import urllib.request
import requests
import simplejson as json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

from argparse import ArgumentParser

import random
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('Channel Access Token')
# Channel Secret
handler = WebhookHandler('Channel Secret')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

#加入群組打招呼
@handler.add(JoinEvent)
def handle_join(event):
    newcoming_text = "大家好，蜜蜜我的名字叫棉木_蜜雪兒，大家可以叫我姆咪，目前蜜蜜可以幫大家查詢美食、天氣、即時匯率跟松山機場剩餘車位及聯合候補，其他事情還在學習中，另外，蜜蜜現在沒錢，只能使用免費的伺服器，偶而回應速度較慢或是沒反應，還請大家多包涵喔!!"

    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=newcoming_text)
        )


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    #處理"天氣"關鍵字
    keyWordWeather = u"天氣"
    if(keyWordWeather in event.message.text):
        locations = ["臺北市","新北市","桃園市","臺中市","臺南市","高雄市","基隆市","新竹縣","新竹市","苗栗縣","彰化縣","南投縣","雲林縣","嘉義縣","嘉義市","屏東縣","宜蘭縣","花蓮縣","臺東縣","澎湖縣","金門縣","連江縣"]
        for location in locations:
            if location in event.message.text:
                x = locations.index(location)
        with urllib.request.urlopen("https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization=向氣象局申請的ApiKey&format=json") as url:
                 datas = json.loads(url.read().decode())
        try:
            reply = datas["cwbopendata"]["dataset"]["location"][x]["locationName"]+"未來6到12小時，"+datas["cwbopendata"]["dataset"]["location"][x]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]+"，最高溫:"+datas["cwbopendata"]["dataset"]["location"][x]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]+"度"+"，最低溫:"+datas["cwbopendata"]["dataset"]["location"][x]["weatherElement"][2]["time"][0]["parameter"]["parameterName"]+"度"+"，感覺"+datas["cwbopendata"]["dataset"]["location"][x]["weatherElement"][3]["time"][0]["parameter"]["parameterName"]
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=reply))
        except:
            line_bot_api.reply_message(event.reply_token,TextMessage(text="蜜蜜不知道啦，要告訴人家'縣市名稱'+'天氣'這個關鍵字...姆咪..^o^"))
    #讓姆咪離開群組
    elif (("姆咪" and "離開群組") in event.message.text):
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='蜜蜜先離開了，謝謝大家照顧!!'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='蜜蜜先離開了，謝謝大家照顧!!'))
            line_bot_api.leave_group(event.source.room_id)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='蜜蜜沒辦法離開1對1聊天喔!!'))
    #查找美食(關鍵字:姆咪查美食-關鍵字(可不輸入)-地點)
    elif ("姆咪查" in event.message.text):
        api_key='向yelp申請的ApiKey'
        headers = {'Authorization': 'Bearer %s' % api_key}
        url='https://api.yelp.com/v3/businesses/search'
        received_text = event.message.text.split('-',2)
        term = received_text[1]
        location = received_text[2]
        if ("美食-" in event.message.text):
            params = {'term':term,'location':location,'radius':1600}
            req = requests.get(url, headers=headers, params=params)
            business = req.json()
            try:
                if business['error']:
                    msg = '蜜蜜找不到'+str(location)+'這個地方ㄟ!!!這是甚麼鄉下地方啊?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            except:
                if len(business['businesses'])==0:
                    msg = '蜜蜜在'+str(location)+'找不到'+str(term)+'的店家ㄟ!!!要不要吃其他的?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                else:
                    x = random.randint(0,len(business["businesses"])-1)
                    msg = business["businesses"][x]["alias"]+"  網站:"+business["businesses"][x]["url"]+"  地址:"+business["businesses"][x]["location"]["address1"]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        elif ("人氣餐廳-" in event.message.text):
            params = {'term':term,'location':location,'radius':1600,'sort_by':'review_count','limit':10}
            req = requests.get(url, headers=headers, params=params)
            business = req.json()
            try:
                if business['error']:
                    msg = '蜜蜜找不到'+str(location)+'這個地方ㄟ!!!這是甚麼鄉下地方啊?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            except:
                if len(business['businesses'])==0:
                    msg = '蜜蜜在'+str(location)+'找不到'+str(term)+'的店家ㄟ!!!要不要吃其他的?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                else:
                    msg = str(location)+"人氣"+str(term)+":"+business["businesses"][0]["alias"]+"  網站:"+business["businesses"][0]["url"]+"  地址:"+business["businesses"][0]["location"]["address1"]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        elif ("最佳餐廳-" in event.message.text):
            params = {'term':term,'location':location,'radius':1600,'sort_by':'rating','limit':10}
            req = requests.get(url, headers=headers, params=params)
            business = req.json()
            try:
                if business['error']:
                    msg = '蜜蜜找不到'+str(location)+'這個地方ㄟ!!!這是甚麼鄉下地方啊?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            except:
                if len(business['businesses'])==0:
                    msg = '蜜蜜在'+str(location)+'找不到'+str(term)+'的店家ㄟ!!!要不要吃其他的?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                else:
                    msg = str(location)+"網評最佳"+str(term)+":"+business["businesses"][0]["alias"]+"  網站:"+business["businesses"][0]["url"]+"  地址:"+business["businesses"][0]["location"]["address1"]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        elif ("平價餐廳-" in event.message.text):
            params = {'term':term,'location':location,'radius':1600,'price':'1','limit':10}
            req = requests.get(url, headers=headers, params=params)
            business = req.json()
            try:
                if business['error']:
                    msg = '蜜蜜找不到'+str(location)+'這個地方ㄟ!!!這是甚麼鄉下地方啊?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            except:
                if len(business['businesses'])==0:
                    msg = '在'+str(location)+'這種天龍地方沒有平價'+str(term)+'這種東西啦!!'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                else:
                    x = random.randint(0,len(business["businesses"])-1)
                    msg = str(location)+'隨選平價'+str(term)+':'+business["businesses"][x]["alias"]+"  網站:"+business["businesses"][x]["url"]+"  地址:"+business["businesses"][x]["location"]["address1"]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))  
        elif ("高檔餐廳-" in event.message.text):
            params = {'term':term,'location':location,'radius':1600,'price':'3,4','limit':10}
            req = requests.get(url, headers=headers, params=params)
            business = req.json()
            try:
                if business['error']:
                    msg = '蜜蜜找不到'+str(location)+'這個地方ㄟ!!!這是甚麼鄉下地方啊?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            except:
                if len(business['businesses'])==0:
                    msg = '在'+str(location)+'這種鄉下地方沒有高檔'+str(term)+'這種東西啦!!'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                else:
                    x = random.randint(0,len(business["businesses"])-1)
                    msg = str(location)+'隨選高檔'+str(term)+':'+business["businesses"][x]["alias"]+"  網站:"+business["businesses"][x]["url"]+"  地址:"+business["businesses"][x]["location"]["address1"]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        elif ("外送飲料-" in event.message.text):
            params = {'term':term,'location':location,'radius':3000,'categories':'bubbletea,delivery','limit':10}
            req = requests.get(url, headers=headers, params=params)
            business = req.json()
            try:
                if business['error']:
                    msg = '蜜蜜找不到'+str(location)+'這個地方ㄟ!!!這是甚麼鄉下地方啊?'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            except:
                if len(business['businesses'])==0:
                    msg = '蜜蜜在'+str(location)+'找不到外送飲料店，喝水比較健康啦!!'
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                else:
                    x = random.randint(0,len(business["businesses"])-1)
                    msg = '附近外送飲料隨選:'+business["businesses"][x]["alias"]+"  電話:"+business["businesses"][x]["phone"]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))

    #處理匯率關鍵字
    elif "匯率" in event.message.text:
        cu=requests.get('https://tw.rter.info/capi.php')
        currency=cu.json()
        usd = round(currency["USDTWD"]["Exrate"],4)
        jpy = round((currency["USDTWD"]["Exrate"]/currency["USDJPY"]["Exrate"]),4)
        eur = round((currency["USDTWD"]["Exrate"]/currency["USDEUR"]["Exrate"]),4)
        cny = round((currency["USDTWD"]["Exrate"]/currency["USDCNY"]["Exrate"]),4)
        hkd = round((currency["USDTWD"]["Exrate"]/currency["USDHKD"]["Exrate"]),4)
        mop = round((currency["USDTWD"]["Exrate"]/currency["USDMOP"]["Exrate"]),4)
        krw = round((currency["USDTWD"]["Exrate"]/currency["USDKRW"]["Exrate"]),4)
        sgd = round((currency["USDTWD"]["Exrate"]/currency["USDSGD"]["Exrate"]),4)
        thb = round((currency["USDTWD"]["Exrate"]/currency["USDTHB"]["Exrate"]),4)
        myr = round((currency["USDTWD"]["Exrate"]/currency["USDMYR"]["Exrate"]),4)
        aud = round((currency["USDTWD"]["Exrate"]/currency["USDAUD"]["Exrate"]),4)
        nzd = round((currency["USDTWD"]["Exrate"]/currency["USDNZD"]["Exrate"]),4)
        zar = round((currency["USDTWD"]["Exrate"]/currency["USDZAR"]["Exrate"]),4)
        if ("美元" in event.message.text) or("美金" in event.message.text)or("鎂" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="美元匯率: " + str(usd) +"僅供參考喔!!"))
        elif ("日幣" in event.message.text)or ("日圓" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="日圓匯率: " + str(jpy) +"僅供參考喔!!"))
        elif "歐元" in event.message.text:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="歐元匯率: " + str(eur) +"僅供參考喔!!"))
        elif "人民幣" in event.message.text:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="人民幣匯率: " + str(cny) +"僅供參考喔!!"))
        elif "港幣" in event.message.text:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="港幣匯率: " + str(hkd) +"僅供參考喔!!"))
        elif "澳門幣" in event.message.text:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="澳門幣匯率: " + str(mop) +"僅供參考喔!!"))
        elif ("韓幣" in event.message.text) or ("韓圓" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="韓幣匯率: " + str(krw) +"僅供參考喔!!"))
        elif ("新幣" in event.message.text) or ("新加坡幣" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="新加坡幣匯率: " + str(sgd) +"僅供參考喔!!"))
        elif "泰銖" in event.message.text:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="泰銖匯率: " + str(thb) +"僅供參考喔!!"))
        elif ("馬幣" in event.message.text) or ("馬來西亞幣" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="馬幣匯率: " + str(myr) +"僅供參考喔!!"))
        elif ("澳幣" in event.message.text)or ("澳洲幣" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="澳幣匯率: " + str(aud) +"僅供參考喔!!"))
        elif ("紐幣" in event.message.text) or ("紐西蘭幣" in event.message.text):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="紐幣匯率: " + str(nzd) +"僅供參考喔!!"))
        elif "南非幣" in event.message.text:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="南非幣匯率: " + str(zar) +"僅供參考喔!!"))
        else:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text = "蜜蜜不知道啦，要告訴人家'幣別'+'匯率'這個關鍵字，另外，蜜蜜目前只知道美元、日幣、歐元、人民幣、港幣、澳門幣、韓幣、新加坡幣、泰銖、馬幣、澳幣、紐幣跟南非幣這些資料喔...姆咪..^o^"))
    #處理松山機場關鍵字
    elif "松山機場" in event.message.text:
        #處理松機停車位查詢
        if "停車場" in event.message.text:
            p_space=requests.get('https://www.tsa.gov.tw/tsa/get_parkjason.aspx')
            parking=p_space.json()
            p_1 = parking[0]["停車場"]+"剩餘"+str(parking[0]["剩餘車位數"])+"車位"
            p_2 = parking[1]["停車場"]+"剩餘"+str(parking[1]["剩餘車位數"])+"車位"
            p_3 = parking[2]["停車場"]+"剩餘"+str(parking[2]["剩餘車位數"])+"車位"
            if "第一" in event.message.text:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text = p_1))
            elif "第二" in event.message.text:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text = p_2))
            elif "第三" in event.message.text:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text = p_3))
            else:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text = p_1+"；"+p_2+"；"+p_3))
        #處理松機聯合候補查詢
        elif "候補" in event.message.text:
            wait_info=requests.get('https://www.tsa.gov.tw/tsa/info_waitlist.aspx?sid=1269')
            waiting=wait_info.json()
            kinmen_1 = waiting[0]["Airline"]+"航空，往"+waiting[0]["Location"]+"航班，目前叫號:"+str(waiting[0]["Call"])+"，等待人數:"+str(waiting[0]["Wait"])+"人"
            kinmen_2 = waiting[1]["Airline"]+"航空，往"+waiting[1]["Location"]+"航班，目前叫號:"+str(waiting[1]["Call"])+"，等待人數:"+str(waiting[1]["Wait"])+"人"
            kinmen_3 = waiting[2]["Airline"]+"航空，往"+waiting[2]["Location"]+"航班，目前叫號:"+str(waiting[2]["Call"])+"，等待人數:"+str(waiting[2]["Wait"])+"人"
            taitung_1 = waiting[3]["Airline"]+"航空，往"+waiting[3]["Location"]+"航班，目前叫號:"+str(waiting[3]["Call"])+"，等待人數:"+str(waiting[3]["Wait"])+"人"
            taitung_2 = waiting[4]["Airline"]+"航空，往"+waiting[4]["Location"]+"航班，目前叫號:"+str(waiting[4]["Call"])+"，等待人數:"+str(waiting[4]["Wait"])+"人"
            hualien = waiting[5]["Airline"]+"航空，往"+waiting[5]["Location"]+"航班，目前叫號:"+str(waiting[5]["Call"])+"，等待人數:"+str(waiting[5]["Wait"])+"人"
            penghu_1 = waiting[6]["Airline"]+"航空，往"+waiting[6]["Location"]+"航班，目前叫號:"+str(waiting[6]["Call"])+"，等待人數:"+str(waiting[6]["Wait"])+"人"
            penghu_2 = waiting[7]["Airline"]+"航空，往"+waiting[7]["Location"]+"航班，目前叫號:"+str(waiting[7]["Call"])+"，等待人數:"+str(waiting[7]["Wait"])+"人"
            penghu_3 = waiting[8]["Airline"]+"航空，往"+waiting[8]["Location"]+"航班，目前叫號:"+str(waiting[8]["Call"])+"，等待人數:"+str(waiting[8]["Wait"])+"人"
            if "金門" in event.message.text:
                if "立榮" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = kinmen_1))
                elif "華信" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = kinmen_2))
                elif "遠東" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = kinmen_3))
                else:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = kinmen_1+"；"+kinmen_2+"；"+kinmen_3))
            elif "臺東" in event.message.text:
                if "立榮" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = taitung_1))
                elif "華信" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = taitung_2))
                else:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = taitung_1+"；"+taitung_2))
            elif "花蓮" in event.message.text:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text = hualien))
            elif "澎湖" in event.message.text:
                if "立榮" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = penghu_1))
                elif "華信" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = penghu_2))
                elif "遠東" in event.message.text:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = penghu_3))
                else:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text = penghu_1+"；"+penghu_2+"；"+penghu_3))
            else:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text = "蜜蜜不知道啦，要告訴人家'目的地'+'候補'這個關鍵字，另外，目前還無法查詢南北竿喔"))
        
    #非前述關鍵字，進入一般對話模式
    else:
        if event.message.text == "姆咪姆咪":
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage(random.choice ( ['心動動', '蹦蹦跳'] )))
        elif event.message.text == "不要學我說話":
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("蜜蜜偏要學!!  >_<"))
        elif event.message.text == "防災頭巾":
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("是兔兔蜜外套啦!!  >_<"))
        elif ("姆咪" in event.message.text) and ("吃大便" in event.message.text):
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("你才吃大便!!"))
        elif ("姆咪" in event.message.text) and ("謝" in event.message.text):
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("蜜蜜很厲害吧，嘿嘿!!"))
        elif ("抱歉" in event.message.text) or ("對不起" in event.message.text):
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("知道錯就好，這次蜜蜜就先原諒你!!"))
        elif event.message.text == '紅':
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("紅"))
        elif "賽" in event.message.text:
            message = TextSendMessage(text=event.message.text)
            line_bot_api.reply_message(event.reply_token, message)
        elif "離開群組"in event.message.text:
            line_bot_api.reply_message(event.reply_token,
            TextSendMessage("蜜蜜偏要留在這裡，嘻嘻!!"))
        elif event.message.text == "(摸頭)":
            sticker_message = StickerSendMessage(package_id='1',sticker_id='5')
            line_bot_api.reply_message(event.reply_token,sticker_message)
        #如果不在多人聊天室或群組就會學人講話，這是為了避免姆咪在群組太吵
        else:
            if isinstance(event.source, SourceGroup):
                pass
            elif isinstance(event.source, SourceRoom):
                pass
            else:
                message = TextSendMessage(text=event.message.text+"...姆咪..^o^")
                line_bot_api.reply_message(event.reply_token, message)

#位置處理
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    api_key='向yelp申請的ApiKey'
    headers = {'Authorization': 'Bearer %s' % api_key}
    url='https://api.yelp.com/v3/businesses/search'
    latitude = event.message.latitude
    longitude = event.message.longitude
    params = {'latitude':latitude,'longitude':longitude,'radius':1600}
    req = requests.get(url, headers=headers, params=params)
    business = req.json()
    x = random.randint(0,len(business["businesses"]))
    if len(business["businesses"]) ==0:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='這甚麼鬼地方!!方圓1.6公里內竟然找不到餐廳!!!'))
    else:
        msg = business["businesses"][x]["alias"]+"  網站:"+business["businesses"][x]["url"]+"  地址:"+business["businesses"][x]["location"]["address1"]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))


#貼圖處理
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])
    sticker_message = StickerSendMessage(package_id='1',sticker_id=sticker_id)
    line_bot_api.reply_message(event.reply_token,sticker_message)

#主動推播訊息(to do ...)


#測試區

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
