import csv
import random
import re
import threading
from bs4 import BeautifulSoup
import requests
import os
import time


class Crawler(threading.Thread):
    """ 论文爬虫
        爬取 `stbcyj.paperonce.org` `http://www.jeesci.com/`
        — `论文标题`
        — `论文链接`
        — `论文的邮箱`
    """
    __slots__ = ["task", "jeesci_page", "jeesci_path", "stbcyj_path",  "stbcyj_dir", "jeesci_dir"]
    basic = ["http://stbcyj.paperonce.org/", "http://www.jeesci.com/"]
    headers = {
        'User-Agent': random.choice([
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/13.0.782.215',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:25.0) Gecko/20100101 Firefox/25.0',
            'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
        ])
    }

    def __init__(self,
                 task,
                 jeesci_page=None,
                 jeesci_path=None,
                 stbcyj_path=None,
                 stbcyj_dir=None,
                 jeesci_dir=None):
        """初始化必要参数"""
        self.task = task
        self.deplay = 1 if "stbcyj" in task else 2
        self.jeesci_page = jeesci_page if jeesci_page else (2008, 2022)

        if not jeesci_path and not stbcyj_path:
            self.stbcyj_path, self.jeesci_path = "stbcyj.csv", "jeesci.csv"

        if not jeesci_dir and not stbcyj_dir:
            self.stbcyj_dir, self.jeesci_dir = "./stbcyj_pdf", "./jeesci_pdf"

        # 初始化目录
        if not os.path.exists(str(self.stbcyj_dir)) and not os.path.exists(str(self.jeesci_dir)):
            os.mkdir(self.stbcyj_dir)
            os.mkdir(self.jeesci_dir)

        super(Crawler, self).__init__(name=self.task)

    def __repr__(self):
        return f'{Crawler.__class__}' \
               f'执行：' \
               f'第一个网页：{Crawler.basic[0]}， ' \
               f'第二个网页{Crawler.basic[1]}'

    def parse_url(self):
        for url in self.join_url():
            time.sleep(2)
            try:
                r = requests.get(url, headers=Crawler.headers)
                yield r.text
            except requests.exceptions.RequestException:
                print("爬取错误, 检查是否能访问")

            except requests.exceptions.ConnectTimeout:
                print("爬取超时，检查是否受限制")

    def parse_stbcyj_page(self):
        """解析jeesci分页URL"""
        soup = BeautifulSoup(next(self.parse_url()), 'lxml')
        for page in soup.findAll('ul', attrs={'class': 'clx'}):
            for p in page.findAll('li'):
                for page_url in p.findAll('a'):
                    page_url = "".join(Crawler.basic[0] + "oa/" +
                                       page_url.get('href')) \
                                      .replace("期", "%C6%DA") \
                                      .replace("年", "%C4%EA")
                    try:
                        r = requests.get(page_url, headers=Crawler.headers)
                        soup = BeautifulSoup(r.text, 'lxml')
                        for tr in soup.findAll('div', attrs={'class': 'ml_title'}):
                            for index_url in tr.findAll('a'):
                                time.sleep(1)
                                self.crawler_stbcyj_info(
                                    "".join(f'{Crawler.basic[0].rstrip("/")}{index_url.get("href")}'))

                    except requests.exceptions.RequestException:
                        print("爬取错误, 检查是否能访问")
                    except requests.exceptions.ConnectTimeout:
                        print("爬虫超时，检查是否受限制")

    def parse_jeesci_page(self):
        """解析jeesci分页URL"""
        for page in self.parse_url():
            soup = BeautifulSoup(page, 'lxml')
            for page_url in soup.findAll('td', attrs={'valign': 'top'}):
                for i in page_url.findAll('a'):
                    # 得到分页URL
                    try:
                        r = requests.get("".join(Crawler.basic[1] + "CN" + i['href'][2:]), headers=Crawler.headers)
                        soup = BeautifulSoup(r.text, 'lxml')
                        for index_url in soup.findAll('li', attrs={'class': 'biaoti'}):
                            time.sleep(1)
                            self.crawler_jeesci_info(index_url.find('a').get('href'))
                    except requests.exceptions.RequestException:
                        print("爬取错误, 检查是否能访问")
                    except requests.exceptions.ConnectTimeout:
                        print("爬虫超时，检查是否受限制")

    def crawler_stbcyj_info(self, url):
        """解析 stbcyj 的 `标题` `链接` `邮箱` 参数"""
        try:
            try:
                r = requests.get(url, headers=Crawler.headers, timeout=80)
                # 部分网页采用gb2312, 手动设置解码
                r.encoding = r.apparent_encoding if "upload" in url else 'gb2312'
            except:
                raise Exception("爬取完成, 结束等待")
            soup = BeautifulSoup(r.text, 'lxml')
            if not soup.find('div', attrs={'class': 'referencetitle'}):
                title = soup.find('div', attrs={'class': 'title'}).text.replace(' ', '').replace('\r\n', '').strip(),
                pdf_url = "".join('http://stbcyj.paperonce.org/oa/pdfdow.aspx?Sid={}'.format(re.findall("\d+", url)[0]))
                self.download_pdf(title, pdf_url)

                info = {
                    '论文标题': title,
                    '论文链接': url.strip(),
                    # 检查是否存在邮箱
                    '邮箱': "无邮箱"
                }
                self.save_as_csv(info)
            else:
                # 遍历数据
                for data in soup.findAll('span', attrs={'id': 'LbMemory'}):
                    title = soup.find('span', attrs={'id': 'LbTitleC'}).text.replace(' ', '').replace('\r\n','').strip()
                    if re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", data.text):
                            email = re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", data.text)
                    else:
                            email = "无邮箱"
                            pdf_url = "".join('http://stbcyj.paperonce.org/oa/pdfdow.aspx?Sid={}'.format(re.findall("\d+", url)[0]))
                            self.download_pdf(title, pdf_url)

                    info = {
                        '论文标题': title,
                        '论文链接': url.strip(),
                        # 检查是否存在邮箱
                        '邮箱': email
                    }
                    self.save_as_csv(info)

        except requests.exceptions as e:
            print("爬虫出现错误", e)

    def crawler_jeesci_info(self, url):
        """解析 jeesci 的 `标题` `链接` `邮箱` 参数"""
        try:
            try:
                r = requests.get(url, headers=Crawler.headers, timeout=80)
            except:
                raise Exception("爬取完成, 结束等待")
            soup = BeautifulSoup(r.text, 'html.parser')
            data = soup.findAll('p', attrs={'data-toggle': 'collapse'})

            # 遍历数据
            for i in data[::2]:
                title = soup.find('h3', attrs={'class': 'abs-tit'}).text.replace(' ', '').replace('\r\n', '')
                pdf_url = soup.find("meta", attrs={'name':'citation_pdf_url'}).get('content').replace('&amp;', '')
                if i.find('a'):
                    email = str(i.find('a').get('href'))[7:]
                else:
                    email = "无邮箱"
                    self.download_pdf(title, pdf_url)

                info = {
                    '论文标题': title,
                    '论文链接': url,
                    # 检查是否存在邮箱
                    '邮箱': email
                }
                self.save_as_csv(info)

        except requests.exceptions as e:
            print("爬虫出现错误", e)

    def save_as_csv(self, info):
        header = ['论文标题', '论文链接', '邮箱']
        print(f"《{info['论文标题']}》 爬取完成")
        if "jeesci" in self.task:
            with open(self.jeesci_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                # 判断header, 阻止重复写入
                if f.tell() == 0:
                    writer.writeheader()
                    writer.writerow(info)
                else:
                    writer.writerow(info)

        if "stbcyj" in self.task:
            with open(self.stbcyj_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                # 判断header, 阻止重复写入
                if f.tell() == 0:
                    writer.writeheader()
                    writer.writerow(info)
                else:
                    writer.writerow(info)

    def join_url(self) -> str:
        """ 组装URL """
        if "stbcyj" in self.task:
            time.sleep(2)
            yield "".join(Crawler.basic[0] + "oa/dlistnum.aspx")

        if "jeesci" in self.task:
            for i in range(self.jeesci_page[0], self.jeesci_page[1] + 1):
                time.sleep(2)
                yield "".join(Crawler.basic[1] + f'CN/article/showTenYearVolumnDetail.do?nian={i}')

    def download_pdf(self, name, url):
        #http://www.jeesci.com/CN/article/downloadArticleFile.do?attachType=PDF&id=1291
        r = requests.get(url)
        index = r.content
        if "stbcyj" in self.task:
            path = f'{self.stbcyj_dir}/{name}.pdf'
            with open(path, 'wb') as f:
                f.write(index)

        else:
            path = f'{self.jeesci_dir}/{name}.pdf'
            with open(path, 'wb') as f:
                f.write(index)

    def run(self):
        if "stbcyj" in self.task:
            self.parse_stbcyj_page()
        else:
            self.parse_jeesci_page()

def main():
    stbcyj_task = Crawler("stbcyj")
    jeesci_task = Crawler("jeesci")

    stbcyj_task.start()
    jeesci_task.start()

    stbcyj_task.join()
    jeesci_task.join()


if __name__ == '__main__':
    main()
