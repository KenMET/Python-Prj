
import sys
import time
import json
import signal
import random
import string
import threading
from socket import *

from bs4 import BeautifulSoup
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from contextlib import closing

target = 'https://unsplash.com/napi/collections/1065976/photos?page=00000&per_page=10&order_by=latest&share_key=a4a197fc196734b74c9d87e48cc86838'
download_url = 'https://unsplash.com/photos/0123456789/download'

def download_jpg(target_download, filename):
    httpsession = requests.session()
    with closing(httpsession.get(target_download)) as r:
        total_size = int(r.headers['Content-Length'])
        temp_size = 0
        with open('%d.jpg' % filename, 'ab+') as f:# "ab"表示追加形式写入文件
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    temp_size += len(chunk)
                    f.write(chunk)
                    f.flush()

                    ###这是下载实现进度显示####
                    done = int(50 * temp_size / total_size)
                    sys.stdout.write("\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * temp_size / total_size))
                    sys.stdout.flush()
    print()


def main():
    global target
    thisset = set()
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    
    for i in range(5):  #download 5 page
        target_page = target.replace('00000', str(i))
        req = requests.get(url=target_page, verify=False)
        bf = BeautifulSoup(req.text, "html.parser")
        html = json.loads(bf.text)
        for sub_element in html:
            thisset.add(sub_element['id'])

    #for element1 in bf.find_all('figure', attrs={'itemprop':'image'}):
        #for element2 in element1.find_all('div', attrs={'class':'IEpfq'}):
            #for element3 in element2.find_all('img', attrs={'class':'_2zEKz'}):
                #if 'srcset' in element3.attrs:
                    #web_element = element3.attrs['srcset'].split(",")
                    #thisset.add(web_element[len(web_element) - 1])



    print('thisset number :' + str(len(thisset)))
    for i in range(len(thisset)):
        photo_id = thisset.pop()
        print('Downloading ID :' + photo_id)
        download_url_tmp = download_url.replace('0123456789', photo_id)
        download_jpg(download_url_tmp, i)
        


            
            
    #f_log = open("test_logs.txt", "a")
    #f_log.write(final_text)





if __name__ == '__main__':
    main()

