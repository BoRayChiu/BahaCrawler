"""This is a crawler for Baha.

It will crawl the data from Baha and generate crawl result.
"""

import json
import time

import requests as rq
from bs4 import BeautifulSoup as bsp


class Crawler:
    """Crawl data from PTT."""

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
            HTML docs which type is sting.
            For example:
            '<div>Hello!</div>'
        """
        crawl_res = rq.post(url=url, headers=self._headers)
        crawl_res.encoding = "utf-8"
        return crawl_res


class TopicIdCrawler(Crawler):
    """Get topic urls.

    Inherit from Crawler.

    Attributes:
        board_id: The board we want to crawl.
        frequency: The number of page we want to get.
    """

    def __init__(self, board_id: str, frequency: int):
        super().__init__()
        self.__board_id = board_id
        self.__frequency = frequency
    
    @property
    def result(self):
        """Get topic urls from crawl result and return it.

        Returns:
            A list is formed with topic url.
            For example:
                ['bsn=38898&snA=3980&tnum=1']
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
            # Select topic urls.
            index = res.select(
                ".b-list__row.b-list-item.b-imglist-item > .b-list__main > a")
            # Append topic url.
            for t in index:
                topic_urls.append(t["href"])
            page += 1
        return topic_urls

class ThreadCrawler(Crawler):
    """Get all content we want in chat thread.

    Inherit from Crawler.

    Attributes:
        board_id: The board we want to crawl.
        topic_id: The id of topic we wnat to crawl.
    """
    def __init__(self, board_id: str, topic_id: str):
        super().__init__()
        self.__board_id = board_id
        self.__topic_id = topic_id

    @property
    def result(self):
        """Get all content we want from crawl result and return it.

        Returns:
            A dicts keys that are category and values are information.
            For example: 
                {
                    'Title': 'Hello World!'
                    'Topics': [
                        {
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
                }
        """
        thread = {}
        thread["Topics"] = []
        # Set max_page the smallest number.
        max_page = 1
        page = 1
        while page <= max_page:
            print("Page"+str(page)+" start!")
            url = "".join(
                (
                    "https://forum.gamer.com.tw/C.php?page=",
                    str(page),
                    "&bsn=",
                    self.__board_id,
                    "&snA=",
                    self.__topic_id
                )
            )
            # Get html docs.
            res = self._crawl(url)
            # bs4 html docs.
            res = bsp(res.text.strip(), "html.parser")
            # If page is current 1, reset max page.
            if (page == 1):
                max_page = int(res.select(".BH-pagebtnA > a")[-1].text)
            # Topics content
            topics = res.select(".c-section__main.c-post")
            # If page is current 1, store 'Title'
            if (page == 1):
                thread["Title"] = topics[0].select_one(
                    ".c-post__header__title").text
            for t in topics:
                topic = {}
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
                    topic["Messages"] = self.__crawl_more_messages(message_id)
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
                            1]["title"][5:]
                        # Contents
                        message["Contents"] = replys[i].select_one(
                            ".comment_content").text.replace("\n", "").replace("\xa0", " ")
                        messages.append(message)
                    # Get all Message in 'Messages'
                    topic["Messages"] = messages
                thread["Topics"].append(topic)
            page += 1
            print("Waiting...")
            # To avoid trouble.
            time.sleep(10)
        print("==========")
        return thread

    def __crawl_more_messages(self, message_id: str):
        """Get messages if there are more messages button"""
        url = "".join(
            (
                "https://forum.gamer.com.tw/ajax/moreCommend.php?bsn=",
                self.__board_id,
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
            message["Time"] = message_bsp.select(".edittime")[1]["title"][5:]
            # Contents
            message["Contents"] = message_bsp.select_one(
                ".comment_content").text.replace("\n", "").replace("\xa0", " ")
            messages.append(message)
        return messages