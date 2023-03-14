'''
$pip install requests
$pip install BeautifulSoup4

'''
import requests as rq
from bs4 import BeautifulSoup as bsp
import time
import json


class Crawler:

    def __init__(self):
        self._headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)""AppleWebKit/537.36 (KHTML, like Gecko)""Chrome/110.0.0.0 Safari/537.36"}

    def _crawl(self, url:str)->str:
        crawl_res = rq.post(url=url, headers=self._headers)
        crawl_res.encoding = "utf-8"
        return crawl_res


class TopicIdCrawler(Crawler):

    def __init__(self, board_id:str, frequency:int):
        super().__init__()
        self.__board_id = board_id
        self.__frequency = frequency
        self.__topic_urls = []
    
    def __main(self):
        page = 1
        for i in range(self.__frequency):
            url = "https://forum.gamer.com.tw/B.php?page="+str(page)+"&bsn="+self.__board_id
            res = bsp(self._crawl(url).text.strip(), "html.parser")
            index = res.select(".b-list__row.b-list-item.b-imglist-item > .b-list__main > a")
            for t in index:
                self.__topic_urls.append(t["href"])
            page += 1
    
    @property
    def result(self):
        self.__main()
        return self.__topic_urls


class ThreadCrawler(Crawler):

    def __init__(self, board_id:str, topic_id:str):
        super().__init__()
        self.__board_id = board_id
        self.__topic_id = topic_id
        self.__thread = {}
        self.__thread["Topics"] = []
    
    def __main(self):
        max_page = 1
        page= 1
        while page <= max_page:
            print("Page"+str(page)+" start!")
            url = "https://forum.gamer.com.tw/C.php?page="+str(page)+"&bsn="+self.__board_id+"&snA="+self.__topic_id
            res = self._crawl(url)
            res = bsp(res.text.strip(), "html.parser")
            if page == 1:
                max_page = int(res.select(".BH-pagebtnA > a")[-1].text)
            topics = res.select(".c-section__main.c-post")
            if page == 1:
                self.__thread["Title"] = topics[0].select_one(".c-post__header__title").text
            for t in topics:
                topic = {}
                topic["Author"] = t.select_one(".userid").text.replace("\n", "").replace("\xa0", " ")
                topic["Time"] = t.select_one(".edittime.tippy-post-info")["data-mtime"]
                topic["Contents"] = t.select_one(".c-article__content").text.replace("\n", "").replace("\xa0", " ")
                has_more_messages = t.select_one(".c-reply__head.nocontent")
                if has_more_messages != None:
                    message_id = has_more_messages.select_one(".more-reply")["id"][15:]
                    topic["Messages"] = self.__crawl_more_messages(message_id)
                else:
                    replys = t.select(".c-reply__item")
                    messages = []
                    for i in range(len(replys)):
                        message = {}
                        message["Author"] = replys[i].select_one(".gamercard")["data-gamercard-userid"]
                        message["Time"] = replys[i].select(".edittime")[1]["title"][5:]
                        message["Contents"] = replys[i].select_one(".comment_content").text.replace("\n", "").replace("\xa0", " ")
                        messages.append(message)
                    topic["Messages"] = messages
                self.__thread["Topics"].append(topic)
            page += 1
            print("Waiting...")
            time.sleep(10)

    def __crawl_more_messages(self, message_id:str):
        url = "https://forum.gamer.com.tw/ajax/moreCommend.php?bsn="+self.__board_id+"&snB="+message_id+"&returnHtml=1"
        res = json.loads(self._crawl(url).text).get("html")
        messages = []
        for i in range(len(res)):
            message = {}
            message_bsp = bsp(res[i].strip(), "html.parser")
            message["Author"] = message_bsp.select_one(".gamercard")["data-gamercard-userid"]
            message["Time"] = message_bsp.select(".edittime")[1]["title"][5:]
            message["Contents"] = message_bsp.select_one(".comment_content").text.replace("\n", "").replace("\xa0", " ")
            messages.append(message)
        return messages

    @property
    def result(self):
        self.__main()
        return self.__thread
