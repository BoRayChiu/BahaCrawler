"""This is a crawler for Baha.

It will crawl data from Baha and generate crawl result.
"""

import json
import time

import requests as rq
from bs4 import BeautifulSoup as bsp


class BahaCrawler:
    """Set basic information for crawling data from Baha."""

    def __init__(self):
        self._headers = {
            "User-Agent":
                "".join(
                    (
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) ",
                        "Gecko/20100101 Firefox/111.0"
                    )
                )
        }

    def _crawl(self, url: str) -> str:
        """Return the HTML we crawl from website.

        Args:
            url: the website we want to crawl.
        Returns:
            HTML which type is sting.
            For example:
            '<div>Hello!</div>'
        """
        crawl_res = rq.post(url=url, headers=self._headers)
        crawl_res.encoding = "utf-8"
        return crawl_res


class BahaTopicUrlCrawler(BahaCrawler):
    """Get topic urls.

    Inherit from Baha Crawler.

    Attributes:
        board_id: The board we want to crawl.
        page: The number of page we want to get.
    """

    def __init__(self, board_id: str, page: str):
        super().__init__()
        self.__board_id = board_id
        self.__frequency = int(page)
    
    @property
    def result(self) -> list:
        """Get topic urls from crawl result and return it.

        Returns:
            A list is formed with the topic url.
            For example:
                ['C.php?bsn=38898&snA=4153&tnum=4']
        """
        topic_urls = []
        page = 1
        for i in range(self.__frequency):
            url = "".join(
                (
                    "https://forum.gamer.com.tw/B.php?page=",
                    str(page),
                    "&bsn=",
                    self.__board_id
                )
            )
            res = bsp(self._crawl(url).text.strip(), "html.parser")
            # Select topic url.
            index = res.select(
                ".b-list__row.b-list-item.b-imglist-item > .b-list__main > a")
            # Append topic url.
            for t in index:
                topic_urls.append(t["href"])
            page += 1
        return topic_urls

class BahaTopicCrawler(BahaCrawler):
    """Get all data we want from chat thread.

    Inherit from BahaCrawler.

    Attributes:
        topic_url: 
            The url of topic we want to crawl.
            For example: 
                "C.php?bsn=60076&snA=7654736"
    """
    def __init__(self, topic_url: str):
        super().__init__()
        self.__topic_url = topic_url

    @property
    def result(self) -> list:
        """Get all data we want from crawl result and return it.

        Returns:
            A dicts keys that are category and values are information.
            For example: 
                [
                    {
                        'Url': 
                        'Title': 'Hello World!'
                        'Author': 'abc123', 
                        'Time': '2023-03-28 00:01:05', 
                        'Contents': 'Hello World HAHA', 
                        'Messages': [
                            {
                                'Author': 'cba321', 
                                'Time': '2023-03-29 23:51:42', 
                                'Contents': 'HAHA'
                            }
                        ]
                    }
                ]
        """
        topics_box = []
        # Set max_page the smallest number.
        max_page = 1
        page = 1
        while page <= max_page:
            print("Page"+str(page)+" start!")
            url = "".join(
                (
                    "https://forum.gamer.com.tw/", 
                    self.__topic_url[0:6],
                    "page=",
                    str(page),
                    "&",
                    self.__topic_url[6:]
                )

            )
            # Get html docs.
            res = self._crawl(url)
            # bs4 html docs.
            res = bsp(res.text.strip(), "html.parser")
            # If page is current 1, reset max page.
            if (page == 1):
                pages = res.select(".BH-pagebtnA > a")
                max_page = int(pages[len(pages)- 1].text)
            # Topics content
            topics = res.select(".c-section__main.c-post")
            # If page is current 1, store Title
            if (page == 1):
                title = topics[0].select_one(
                    ".c-post__header__title").text
            for t in topics:
                topic = {}
                # Url
                topic["Url"] = url
                # Title
                topic["Title"] = title
                # Author
                topic["Author"] = t.select_one(".userid").text.replace(
                    "\n", "").replace("\xa0", " ")
                # Time
                topic["Time"] = t.select_one(
                    ".edittime.tippy-post-info")["data-mtime"]
                # Contents
                topic["Contents"] = t.select_one(
                    ".c-article__content").text.replace("\n", "").replace(
                    "\xa0", " ")
                # If has more messages, call __crawl_more_messages()
                has_more_messages = t.select_one(".c-reply__head.nocontent")
                if (has_more_messages is not None):
                    message_id = has_more_messages.select_one(
                        ".more-reply")["id"][15:]
                    board_id = self.__topic_url[10:]
                    topic["Messages"] = self.__crawl_more_messages(board_id, message_id)
                else:
                    # Message
                    replys = t.select(".c-reply__item")
                    messages = []
                    for i in range(len(replys)):
                        message = {}
                        # Author
                        message["Author"] = replys[i].select_one(
                            ".gamercard")["data-gamercard-userid"]
                        # Time
                        message["Time"] = replys[i].select(".edittime")[
                            1]["data-tippy-content"][5:]
                        # Contents
                        message["Contents"] = replys[i].select_one(
                            ".comment_content").text.replace("\n", "").replace("\xa0", " ")
                        messages.append(message)
                    # Get all Message in massages.
                    topic["Messages"] = messages
                topics_box.append(topic)
            page += 1
            print("Waiting...")
            # To avoid trouble.
            time.sleep(5)
        print("==========")
        return topics_box

    def __crawl_more_messages(self, board_id: str, message_id: str):
        """Get more messages if there are "more messages" button"""
        url = "".join(
            (
                "https://forum.gamer.com.tw/ajax/moreCommend.php?bsn=",
                board_id,
                "&snB=",
                message_id,
                "&returnHtml=1"
            )
        )
        # Get json from crawl result.
        res = json.loads(self._crawl(url).text).get("html")
        messages = []
        for i in range(len(res)):
            message = {}
            message_bsp = bsp(res[i].strip(), "html.parser")
            # Author
            message["Author"] = message_bsp.select_one(
                ".gamercard")["data-gamercard-userid"]
            # Time
            message["Time"] = message_bsp.select(".edittime")[1]["data-tippy-content"][5:]
            # Contents
            message["Contents"] = message_bsp.select_one(
                ".comment_content").text.replace("\n", "").replace("\xa0", " ")
            messages.append(message)
        return messages

# How to use:
if __name__ == "__main__":
    bu = BahaTopicUrlCrawler("17532", "1")
    print(bu.result)
    print("-------------")
    bc1 = BahaTopicCrawler("C.php?bsn=17532&snA=691826&tnum=2")
    print(bc1.result)
    print("-------------")
    bc2 = BahaTopicCrawler("C.php?bsn=17532&snA=689998&tnum=101")
    print(bc2.result)