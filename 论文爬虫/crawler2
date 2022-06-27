import time
import json
import requests
from bs4 import BeautifulSoup
import re
import csv

urls = {
    "华中科技大学": "http://xb.hust.edu.cn"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36 Edg/102.0.1245.33'
}


def fetch():
    """
        Request URL: http://html.journal.founderss.cn/hzkd/1574/13838/data.json
    """
    try:
        r = requests.get(f"{urls['华中科技大学']}/index-list", headers=headers, verify=False)
        r.encoding = r.apparent_encoding
    except requests.RequestException as e:
        print("错误错误", e)

    # 解析数据
    soup = BeautifulSoup(r.text, 'lxml')
    dl = soup.find_all('div', {"class":"indexList-sissue"})
    for dd in dl:
        for a in dd.find_all('a'):
            # 分页访问
            try:
                page = requests.get(f"{urls['华中科技大学']}{a.get('href')}", headers=headers)
                pagesoup = BeautifulSoup(page.text, 'lxml')
            except (requests.RequestException, Exception) as e:
                print("错误错误2222222", e)

            page_link = pagesoup.find_all('a', {'rel':'noopener'})
            for l in page_link:
                if "journal" in l['href']:
                    link = l['href']
                    nums = link[str(link).find('hzkd/'):]
                    nums = str(nums).lstrip('hzkd/').rstrip("/?showGoogle=0&showBaidu=1").split('/') \
                        if "/?show" in nums \
                        else str(nums).lstrip('hzkd/').split('/')
                    try:
                        resp = requests.get(f"http://html.journal.founderss.cn/hzkd/{nums[0]}/{nums[1]}/data.json", headers=headers)
                        index = json.loads(resp.text)
                        email = re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", resp.text)
                        data = {
                            "标题": index['titlegroup']['articletitle'][0]['data'][0]['data'],
                            # "作者": index['contribgroup']['author'][0]['name'][0]['givenname'],
                            "邮箱": str(set(email)).lstrip('{').rstrip('}').replace("'", ''),
                        }
                        print(data, f"http://html.journal.founderss.cn/hzkd/{nums[0]}/{nums[1]}/data.json")
                        #写入保存
                        header = ['标题', '邮箱']
                        with open("《华中科技大学》.csv", 'a', encoding='utf-8-sig', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=header)
                            # 判断header, 阻止重复写入
                            if f.tell() == 0:
                                writer.writeheader()
                                writer.writerow(data)
                            else:
                                writer.writerow(data)

                    except (requests.RequestException, Exception):
                        pass
                time.sleep(2)
            time.sleep(1)



fetch()
