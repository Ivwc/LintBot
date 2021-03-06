
import configparser
import requests
import datetime
from flask import Flask, request, abort


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

from bs4 import BeautifulSoup
import random


app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi('r7uHxtXwtjDXYHoAWazEgWw93ZBdr5+m5kiyLPp2aGKA1KXxlzrvMvDyz8WVWhfk7tzeX5l3Q+Etrr4pA8ezmg7QYKQ70c27UMG/ZatLlvyIIqmnNHq3l6BmHCNsVfpuzEjMPUjOb/XRTZ8LsHW+JgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('b334451f4eaeabb48c0050a013167f01')

@app.route("/callback", methods=['POST'])

def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'



def apple_news():
    target_url = 'http://www.appledaily.com.tw/realtimenews/section/new/'
    head = 'http://www.appledaily.com.tw'
    print('Start parsing appleNews....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('.rtddt a'), 0):
        if index == 15:
            return content
        if head in data['href']:
            link = data['href']
        else:
            link = head + data['href']
        content += '{}\n\n'.format(link)
    return content


def get_page_number(content):
    start_index = content.find('index')
    end_index = content.find('.html')
    page_number = content[start_index + 5: end_index]
    return int(page_number) + 1


def craw_page(res, push_rate):
    soup_ = BeautifulSoup(res.text, 'html.parser')
    article_seq = []
    for r_ent in soup_.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']
            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                rate = r_ent.find(class_="nrec").text
                url = 'https://www.ptt.cc' + link
                if rate:
                    rate = 100 if rate.startswith('爆') else rate
                    rate = -1 * int(rate[1]) if rate.startswith('X') else rate
                else:
                    rate = 0
                # 比對推文數
                if int(rate) >= push_rate:
                    article_seq.append({
                        'title': title,
                        'url': url,
                        'rate': rate,
                    })
        except Exception as e:
            # print('crawPage function error:',r_ent.find(class_="title").text.strip())
            print('本文已被刪除', e)
    return article_seq


def crawl_page_gossiping(res):
    soup = BeautifulSoup(res.text, 'html.parser')
    article_gossiping_seq = []
    for r_ent in soup.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']

            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                url_link = 'https://www.ptt.cc' + link
                article_gossiping_seq.append({
                    'url_link': url_link,
                    'title': title
                })

        except Exception as e:
            # print u'crawPage function error:',r_ent.find(class_="title").text.strip()
            # print('本文已被刪除')
            print('delete', e)
    return article_gossiping_seq


def ptt_gossiping():
    rs = requests.session()
    load = {
        'from': '/bbs/Gossiping/index.html',
        'yes': 'yes'
    }
    res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=load)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_page_url = soup.select('.btn.wide')[1]['href']
    start_page = get_page_number(all_page_url)
    index_list = []
    article_gossiping = []
    for page in range(start_page, start_page - 2, -1):
        page_url = 'https://www.ptt.cc/bbs/Gossiping/index{}.html'.format(page)
        index_list.append(page_url)

    # 抓取 文章標題 網址 推文數
    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        # 如網頁忙線中,則先將網頁加入 index_list 並休息1秒後再連接
        if res.status_code != 200:
            index_list.append(index)
            # print u'error_URL:',index
            # time.sleep(1)
        else:
            article_gossiping = crawl_page_gossiping(res)
            # print u'OK_URL:', index
            # time.sleep(0.05)
    content = ''
    for index, article in enumerate(article_gossiping, 0):
        if index == 15:
            return content
        data = '{}\n{}\n\n'.format(article.get('title', None), article.get('url_link', None))
        content += data
    return content


def ptt_beauty():
    rs = requests.session()
    res = rs.get('https://www.ptt.cc/bbs/Beauty/index.html', verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_page_url = soup.select('.btn.wide')[1]['href']
    start_page = get_page_number(all_page_url)
    page_term = 2  # crawler count
    push_rate = 10  # 推文
    index_list = []
    article_list = []
    for page in range(start_page, start_page - page_term, -1):
        page_url = 'https://www.ptt.cc/bbs/Beauty/index{}.html'.format(page)
        index_list.append(page_url)

    # 抓取 文章標題 網址 推文數
    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        # 如網頁忙線中,則先將網頁加入 index_list 並休息1秒後再連接
        if res.status_code != 200:
            index_list.append(index)
            # print u'error_URL:',index
            # time.sleep(1)
        else:
            article_list = craw_page(res, push_rate)
            # print u'OK_URL:', index
            # time.sleep(0.05)
    content = ''
    for article in article_list:
        data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                             article.get('url', None))
        content += data
    return content


def ptt_hot():
    target_url = 'http://disp.cc/b/PttHot'
    print('Start parsing pttHot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for data in soup.select('#list div.row2 div span.listTitle'):
        title = data.text
        link = "http://disp.cc/b/" + data.find('a')['href']
        if data.find('a')['href'] == "796-59l9":
            break
        content += '{}\n{}\n\n'.format(title, link)
    return content


def movie():
    target_url = 'http://www.atmovies.com.tw/movie/next/0/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('ul.filmNextListAll a')):
        if index == 20:
            return content
        title = data.text.replace('\t', '').replace('\r', '')
        link = "http://www.atmovies.com.tw" + data['href']
        content += '{}\n{}\n'.format(title, link)
    return content


def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""

    for index, data in enumerate(soup.select('article div h1.entry-title a')):
        if index == 12:
            return content
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content


def panx():
    target_url = 'https://panx.asia/'
    print('Start parsing ptt hot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for data in soup.select('div.container div.row div.desc_wrap h2 a'):
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content

def getShowTimeMovie():
    resp = requests.get('http://www.srm.com.tw/time/time.htm')
    resp.encoding = "big5"
    soup = BeautifulSoup(resp.text, "html.parser")
    movies = soup.select('table')

    # for movie in movies:
    #     moveName = movie.find_all('tr')
    #     print(moveName[1].find_all('td')[0].find_all('p')[1].get_text())

    showTime = requests.get('http://www.atmovies.com.tw/showtime/t04410/a04/')
    showTime.encoding = "utf-8"
    soup2 = BeautifulSoup(showTime.text, "html.parser")
    title = soup2.select('#theaterShowtimeTable')
    showTimeMovies = []
    showTimeMoviesTimes = []
    timelen = -1
    for movie in title:
        # 取得电影名称
        movieName = movie.select('.filmTitle a')[0].get_text()
        # 取得电影时刻
        times = movie.select('li')[1].select('ul')[1].select('li')

        # 判断电影名称是否已经在电影阵列里了
        if movieName not in showTimeMovies:
            # 不在的话就把电影名称放到电影阵列里
            showTimeMovies.extend([movieName])

            # 帮时刻阵列创一个空间出来放电影的时刻
            showTimeMoviesTimes.append([])
            timelen = timelen + 1

        # 把电影时刻塞到时刻阵列
        for index in range(len(times)):
            if index != (len(times) - 1):
                showTimeMoviesTimes[timelen].append(times[index].get_text())

    content = ""
    for index in range(len(showTimeMovies)):
        content += "[ "+showTimeMovies[index] + " ]\n"
        # print(showTimeMovies[index])
        # print(showTimeMoviesTimes[index])
        for index2 in range(len(showTimeMoviesTimes[index])):
            if (index2 + 1) != len(showTimeMoviesTimes[index]):
                content += showTimeMoviesTimes[index][index2] + "\n"
            else:
                content += showTimeMoviesTimes[index][index2] + "\n\n"

    return content

def getShowTimeMovies():
    resp = requests.get('http://www.srm.com.tw/time/time.htm')
    resp.encoding = "big5"
    soup = BeautifulSoup(resp.text, "html.parser")
    movies = soup.select('table')

    # for movie in movies:
    #     moveName = movie.find_all('tr')
    #     print(moveName[1].find_all('td')[0].find_all('p')[1].get_text())

    showTime = requests.get('http://www.atmovies.com.tw/showtime/t04410/a04/')
    showTime.encoding = "utf-8"
    soup2 = BeautifulSoup(showTime.text, "html.parser")
    title = soup2.select('#theaterShowtimeTable')
    showTimeMovies = []
    for movie in title:
        # 取得电影名称
        movieName = movie.select('.filmTitle a')[0].get_text()
        # 取得电影时刻
        times = movie.select('li')[1].select('ul')[1].select('li')

        # 判断电影名称是否已经在电影阵列里了
        if movieName not in showTimeMovies:
            # 不在的话就把电影名称放到电影阵列里
            showTimeMovies.extend([movieName])

    return showTimeMovies



def getShowTimeChoiseMovie(choise_movie):
    showTime = requests.get('http://www.atmovies.com.tw/showtime/t04410/a04/')
    showTime.encoding = "utf-8"
    soup2 = BeautifulSoup(showTime.text, "html.parser")
    title = soup2.select('#theaterShowtimeTable')
    showTimeMovies = []
    showTimeMoviesTimes = []
    timelen = -1
    for movie in title:
        # 取得电影名称
        movieName = movie.select('.filmTitle a')[0].get_text()
        # 取得电影时刻
        times = movie.select('li')[1].select('ul')[1].select('li')

        # 判断电影名称是否已经在电影阵列里了
        if movieName not in showTimeMovies:
            # 不在的话就把电影名称放到电影阵列里
            showTimeMovies.extend([movieName])

            # 帮时刻阵列创一个空间出来放电影的时刻
            showTimeMoviesTimes.append([])
            timelen = timelen + 1

        # 把电影时刻塞到时刻阵列
        for index in range(len(times)):
            if index != (len(times) - 1):
                showTimeMoviesTimes[timelen].append(times[index].get_text())

    content = ""
    nowtime = datetime.datetime.now().strftime("%H:%M")
    nowArr = nowtime.split(":")
    # heroku時區是+0 不是台灣的+8
    now = (int(nowArr[0]) + 8) * 100 + int(nowArr[1])
    choise_movie = choise_movie.split(" ")
    choise_movie = choise_movie[len(choise_movie) - 1]
    # 判斷有符合字串的電影
    result = [a for a in showTimeMovies if a.find(choise_movie) >= 0]
    if len(result) > 0:
        for m in result:
            content += "現在時間 " + str(int(nowArr[0]) + 8)+":"+ str(nowArr[1])+ "\n"
            movieIndex = showTimeMovies.index(m)
            content += "[" + showTimeMovies[movieIndex] + "]\n"

            content2 = ""
            for index2 in range(len(showTimeMoviesTimes[movieIndex])):
                thisTime = showTimeMoviesTimes[movieIndex][index2]
                try:
                    if thisTime.index("：") == 2:
                        thisTime = thisTime.split('：')
                        thisTime = int(thisTime[0]) * 100 + int(thisTime[1])
                        if thisTime >= now:
                            if (index2 + 1) != len(showTimeMoviesTimes[movieIndex]):
                                content2 += showTimeMoviesTimes[movieIndex][index2] + "\n"
                            else:
                                content2 += showTimeMoviesTimes[movieIndex][index2] + "\n\n"
                except ValueError:
                    content2 += showTimeMoviesTimes[movieIndex][index2] + "\n"

            if content2 == "":
                content2 = "今日已無場次"

            content += content2

    else:
        content = "找不到電影，請確認您輸入的電影名稱"



    return content

def getNearByRestaurant(lat,lng):
    # location使用者的位置  radius範圍 key谷歌APIKEY type要尋找的景點類型 opennow有在營業
    googleMap = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+lat+","+lng+"&radius=300&key=AIzaSyAQd44RuqDMGHr5Uz58jMlLWYzrOpdV0gA&type=restaurant&opennow&language=zh-TW"
    googleMapImage = "https://maps.googleapis.com/maps/api/place/photo?key=AIzaSyAQd44RuqDMGHr5Uz58jMlLWYzrOpdV0gA"
    res = requests.get(googleMap)
    status = res.json()['status']
    results = res.json()['results']
    requestsLen = len(results) - 1
    content = []
    if status == "OK":
        indexArr = []
        # 隨機取出10筆店家
        for index in range(10):
            # 隨機產生0~API回吐的數量
            ranInt = random.randint(0, requestsLen)
            # 因為要取出五筆資料但是不重複，所以要判斷是否已經有在arr裡面了
            while ranInt in indexArr:
                ranInt = random.randint(0, requestsLen)
            indexArr.append(ranInt)
            print("==================================")
            image = ""
            # 判斷是否有photo
            if 'photos' in results[ranInt].keys():
                height = str(results[ranInt]['photos'][0]['height'])
                width = str(results[ranInt]['photos'][0]['width'])
                reference = results[ranInt]['photos'][0]['photo_reference']
                googleMapImage = googleMapImage + "&photoreference=" + reference + "&maxheight=" + height + "&maxwidth=" + width
                image = requests.get(googleMapImage)
                # print(googleMapImage)
                # print(image)
                # image = googleMapImage
            rating = "無評價"
            if 'rating' in results[ranInt].keys():
                rating = "評價: " + str(results[ranInt]['rating'])
            content.append({
                "thumbnailImageUrl": image,
                "imageBackgroundColor": "#FFFFFF",
                "title": results[ranInt]['name'],
                "text": rating,
                "actions": [
                    {
                        "type": "uri",
                        "label": "查看位置",
                        "uri": "https://www.google.com.tw/maps/place/"+str(results[ranInt]['geometry']['location']['lat'])+","+str(results[ranInt]['geometry']['location']['lng'])
                    }
                ]
            })





    elif res.json()['status'] == "ZERO_RESULTS":
        content += "沒有資料"
    else:
        content += "發生錯誤請聯絡管理員"



    return content


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)

    if event.message.text == "蘋果即時新聞":
        content = apple_news()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "PTT 表特版 近期大於 10 推的文章":
        content = ptt_beauty()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "隨便來張正妹圖片":
        content = ptt_beauty()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "近期熱門廢文":
        content = ptt_hot()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "即時廢文":
        content = ptt_gossiping()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "近期上映電影":
        content = movie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "科技新報":
        content = technews()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "PanX泛科技":
        content = panx()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if event.message.text == "開始玩":
        buttons_template = TemplateSendMessage(
            alt_text='開始玩 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='新聞',
                        text='新聞'
                    ),
                    MessageTemplateAction(
                        label='電影',
                        text='電影'
                    ),
                    MessageTemplateAction(
                        label='看廢文',
                        text='看廢文'
                    ),
                    MessageTemplateAction(
                        label='正妹',
                        text='正妹'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "新聞":
        buttons_template = TemplateSendMessage(
            alt_text='新聞 template',
            template=ButtonsTemplate(
                title='新聞類型',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/vkqbLnz.png',
                actions=[
                    MessageTemplateAction(
                        label='蘋果即時新聞',
                        text='蘋果即時新聞'
                    ),
                    MessageTemplateAction(
                        label='科技新報',
                        text='科技新報'
                    ),
                    MessageTemplateAction(
                        label='PanX泛科技',
                        text='PanX泛科技'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "電影":
        buttons_template = TemplateSendMessage(
            alt_text='電影 template',
            template=ButtonsTemplate(
                title='服務類型',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/sbOTJt4.png',
                actions=[
                    MessageTemplateAction(
                        label='近期上映電影',
                        text='近期上映電影'
                    ),
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "看廢文":
        buttons_template = TemplateSendMessage(
            alt_text='看廢文 template',
            template=ButtonsTemplate(
                title='你媽知道你在看廢文嗎',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/ocmxAdS.jpg',
                actions=[
                    MessageTemplateAction(
                        label='近期熱門廢文',
                        text='近期熱門廢文'
                    ),
                    MessageTemplateAction(
                        label='即時廢文',
                        text='即時廢文'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "正妹":
        buttons_template = TemplateSendMessage(
            alt_text='正妹 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/qKkE2bj.jpg',
                actions=[
                    MessageTemplateAction(
                        label='PTT 表特版 近期大於 10 推的文章',
                        text='PTT 表特版 近期大於 10 推的文章'
                    ),
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if event.message.text == "秀泰電影":
        actions = []
        actions.append(MessageTemplateAction(
            label='所有場次',
            text='秀泰電影 所有場次'
        ))
        actions.append(MessageTemplateAction(
            label='待會看',
            text='請輸入[秀泰電影 待會看 電影名稱]，電影名稱替換成您想要找的電影，即可搜尋今天還可以看的場次。'
        ))

        buttons_template = TemplateSendMessage(
            alt_text='秀泰電影 template',
            template=ButtonsTemplate(
                title='選擇秀泰服務',
                text='請選擇',
                thumbnail_image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHAf1HE8a6jBJf1yDZWZn-IyYqKyI-28N1ES2A7A-S6oTzX5Sznw',
                actions=actions
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

    if len(event.message.text) > 8 and event.message.text.find("秀泰電影 待會看") >= 0:
        content = getShowTimeChoiseMovie(event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))


    if event.message.text == "秀泰電影 所有場次":
        content = getShowTimeMovie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))

    if event.message.text == "找餐廳":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請使用Line的 '傳送位置' 訊息功能，即可搜尋出附近的餐廳。"))


    # if event.message.text == "秀泰電影 待會看":
    #     content = getShowTimeMovies();
    #     actions = []
    #     for movie in content:
    #         actions.append(MessageTemplateAction(
    #             label=movie,
    #             text='秀泰電影 待會看 '+movie
    #         ))
    #
    #     buttons_template = TemplateSendMessage(
    #         alt_text='上映電影 template',
    #         template=ButtonsTemplate(
    #             title='選擇電影',
    #             text='選擇待會想去看的電影',
    #             thumbnail_image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFcK4kz9kCm_O97zz_KrEYii_3MdPnDfAeAR5cDnbuD6rk7W4N',
    #             actions=actions
    #         )
    #     )
    #     line_bot_api.reply_message(event.reply_token, buttons_template)
    #     return 0

    if event.message.text == "功能選單":
        buttons_template = TemplateSendMessage(
            alt_text='目錄 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.ytimg.com/vi/_TVMVbTC0U0/maxresdefault.jpg',
                actions=[
                    MessageTemplateAction(
                        label='秀泰電影',
                        text='秀泰電影'
                    ),
                    MessageTemplateAction(
                        label='開始玩',
                        text='開始玩',
                    ),
                    MessageTemplateAction(
                        label='找餐廳',
                        text='找餐廳',
                    ),
                    # URITemplateAction(
                    #     label='影片介紹 阿肥bot',
                    #     uri='https://youtu.be/1IxtWgWxtlE'
                    # ),
                    # URITemplateAction(
                    #     label='如何建立自己的 Line Bot',
                    #     uri='https://github.com/twtrubiks/line-bot-tutorial'
                    # ),
                    # URITemplateAction(
                    #     label='聯絡作者',
                    #     uri='https://www.facebook.com/TWTRubiks?ref=bookmarks'
                    # )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

@handler.add(MessageEvent, message=LocationMessage)
def handle_message(event):
    res = getNearByRestaurant(str(event.message.latitude),str(event.message.longitude))
    columns = []
    for r in res:
        columns.append({
            "thumbnailImageUrl": 'https://example.com/bot/images/item1.jpg',
            "imageBackgroundColor": "#FFFFFF",
            "title": r['title'],
            "text": r['text'],
            "actions": [
                {
                    "type": "uri",
                    "label": "查看位置",
                    "uri": r['actions'][0]['uri']
                }
            ]
        })
    Carousel_template = TemplateSendMessage(
        alt_text='餐廳 template',
        template=CarouselTemplate(
            imageAspectRatio='rectangle',
            imageSize='cover',
            columns=columns
        )
    )

    line_bot_api.reply_message(event.reply_token, Carousel_template)

if __name__ == '__main__':
    app.run()
