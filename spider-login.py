from selenium import webdriver
import requests
import re
import json
import time
import random
import csv
from bs4 import BeautifulSoup
from tqdm import tqdm


## 通过读取预先保存的包含登录信息的json文件实现登录
def getCookie(url,file = 'liepincookies.json'):
    with open(file, 'r', encoding='utf8') as f:
              listCookies = json.loads(f.read())
    for cookie in listCookies:
        cookie_dict = {
            'domain': '.liepin.com',
            'name': cookie.get('name'),
            'value': cookie.get('value'),
            'path': '/',
            "expires": '',
            'sameSite': 'None',
            'secure': cookie.get('secure')
        }
        driver.add_cookie(cookie_dict)
    print("get cookie")

# 输入并查询爬取的工作名称
def searchJob(jobname="前端"):
    ## 找到职位搜索的位置并输入职位名称
    input = driver.find_element_by_xpath('//*[@placeholder="搜索职位/公司/内容关键词"]')
    input.send_keys(jobname)
    ## 点击搜索打开搜索新界面
    # 登录
    # driver.find_element_by_xpath('//*[@id="main-container"]/div/div[3]/div[1]/div/div[1]/div[1]/div/div/div/span').click()
    # 非登录
    driver.find_element_by_xpath('//*[@id="home-search-bar-container"]/div/div/div/div/div/div[1]/div[1]/div/div/div/span').click()
    time.sleep(1)

## requests请求中增加高匿代理proxy和Usergent获取条目的具体信息
def getResponse(url):
    ## 通过Proxy代理池筛选得到高匿代理
    proxypool = [
        'http://8.210.83.33:80', 'http://223.68.190.136:9091',
        'http://47.57.188.208:80', 'http://121.37.31.195:8080']
    Agent = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11']
    ## 如果页面请求失败，最大尝试次数为5
    for i in range(0,5):
        try:
            headers = {'User-Agent': random.choice(Agent)}
            proxy = random.choice(proxypool)
            proxies = {"http":proxy}
            ## 在请求中增加匿名代理和头部信息，并设置访问超时时长
            html = requests.get(url= url, headers= headers ,proxies = proxies, timeout =(10,15))
            if html.status_code == 200:
                html.encoding = html.apparent_encoding
                return html
        except Exception as e:
            break
    return False

# 获取当前界面下所有条目的具体信息：岗位要求  通过requests请求的html文件，获取文本信息
def getitemInfo(detailhref):
    pagedetail = []
    pagewelfare = []
    for href in tqdm(detailhref):
        try:
            ## 获取下一层网页的具体信息
            html = getResponse(href)
            ## 通过bs4对需要的信息进行提取
            infodetail = BeautifulSoup(html.text,'html.parser').select('dl dd')
            welfare = BeautifulSoup(html.text,'html.parser').select('div div.labels')
            infodetail = infodetail[0].text.replace('\n',' ')
            welfare = welfare[0].text.replace('\n',' ')
            pagedetail.append(infodetail)
            pagewelfare.append(welfare)
            time.sleep(0.1)
        except Exception as e:
            print(e)
    return pagedetail,pagewelfare

# 获取当前界面的一些标准信息  并接收下一层requests得到的岗位信息
# 将所有信息汇总并保存
def getPageInfo(jobname):
    ## 获取当前界面所有的条目信息
    jobdetaihrefs=driver.find_elements_by_xpath('//*[@class="job-detail-box"]/a[1]')
    ## 将当前界面下所有条目信息的链接整合到列表detailhreflist中
    detailhreflist = []
    for jobdetaihref in jobdetaihrefs[:3]:
        href = jobdetaihref.get_attribute('href')
        detailhreflist.append(href)
    ## 获取当前界面所的所有条目的信息，并整理进行保存
    titles=driver.find_elements_by_xpath('//*[@class="job-detail-box"]/a[1]/div[1]/div/div[1]')
    locations = driver.find_elements_by_xpath('//*[@class="job-detail-box"]/a[1]/div[1]/div/div[2]/span[2]')
    salarys = driver.find_elements_by_xpath('//*[@class="job-salary"]')
    joblabels = driver.find_elements_by_xpath('//*[@class="job-detail-box"]/a[1]/div[2]')
    companys = driver.find_elements_by_xpath('//*[@class="job-detail-box"]/a[2]/div/div/span')
    companytags = driver.find_elements_by_xpath('//*[@class="job-detail-box"]/a[2]/div/div/div[2]')
    ## 通过requests请求的该条目的链接获得岗位要求和福利信息
    welfares,jobdetails = getitemInfo(detailhreflist)
    currentpageinfo=[]
    for title,location,salary,jobtag,company,companytag,welfare,jobdetail in zip(\
              titles,locations,salarys,joblabels,companys,companytags,welfares,jobdetails):
        iteminfo=[title.text,location.text,salary.text,jobtag.text.replace('\n',' '),\
                  company.text,companytag.text.replace('\n',' '),welfare,jobdetail]
        currentpageinfo.append(iteminfo)
    ## 当前页面爬取结束，将数据进行保存
    savetofile(currentpageinfo,jobname)

# 先写入表格标题
def savedatahead(filename):
    head = ["职位","城市","薪资","要求","公司","公司描述","岗位描述","福利"]
    with open(filename + ".csv","w") as csvfile:
        writer=csv.writer(csvfile)
        writer.writerow(head)

# 单个界面所有信息爬取结束时就写入到文件
def savetofile(info,filename):
    with open(filename + ".csv","a") as csvfile:
        writer=csv.writer(csvfile)
        writer.writerows(info)


jobname = "Linux"
mainurl = 'https://www.liepin.com'
## 初始化浏览器
driver = webdriver.Chrome()
driver.get(mainurl)
time.sleep(1)
##  通过原先保存的cookie实现登录
# getCookie(mainurl)
##  加入Cookie后打开新窗口才有登录信息
# driver.execute_script('window.open("https://www.liepin.com");')
# time.sleep(1)
# window = driver.window_handles
# driver.switch_to.window(window[1])
# time.sleep(1)
## 先保存数据的标题
savedatahead(jobname)
## 进入输入工作名称，进入搜索界面
searchJob()
## 切换爬虫处理的搜索界面(浏览器的第二个界面)
window = driver.window_handles
driver.switch_to.window(window[1])
## 热门完整城市范围1-cityn   最大为14
cityn = 14
for indexcity in range (1,cityn):
    citylist = driver.find_elements_by_xpath('/html/body/div/section/div/div[1]/div[3]/ul/li')
    citybutton = citylist[indexcity]
    print('当前爬取城市'+ citybutton.text)
    ## 点击热门城市的标签，开始爬取该城市下的数据
    webdriver.ActionChains(driver).move_to_element(citybutton).click(citybutton).perform()
    ## 爬取第一页的数据
    getPageInfo(jobname)
    ## 点击进入下一页
    driver.find_element_by_xpath('//*[@class="anticon anticon-right"]').click()
    npage=1
    ## 调试演示时只爬取前4个页面
    ## 理论上切换城市前要把该城市能点击进入下一页的所有界面进行爬取
    ## 正确表达式为while True
    while npage<2:
        ## 获取下面可点击button的个数来判断当前界面是不是该城市的最后一个界面
        ## 没有找到其他的好的办法
        ## 理论上没有最后一页时点击下一页不会报错，且webdriver当前界面不发生改变
        nextbt = driver.find_elements_by_xpath('//*[@data-selector="pagintion-item-selector"]')
        getPageInfo(jobname)
        npage+=1
        if len(nextbt)==7:
            nextbt[6].click()
            time.sleep(0.1)
        else: break
    print("爬取总页面数：" + str(npage))
    time.sleep(1)
    ## 清空筛选条件点击进入下一个城市
    button = driver.find_element_by_xpath('//*[@id="search-jobs-clear-options"]')
    print(button.text)
    webdriver.ActionChains(driver).move_to_element(button).click(button).perform()
    time.sleep(2)
print('............数据爬取结束')
driver.quit()