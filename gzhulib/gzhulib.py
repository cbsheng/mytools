#!/usr/bin/python
#coding:utf-8

import requests
from BeautifulSoup import BeautifulSoup
import re
import sys
try:
    import mydebug
    usernm = mydebug.usernm
    passwd = mydebug.passwd
except ImportError:
    #本地使用可以直接写死这两个变量
    usernm = None
    passwd = None

help_doc = '''
  Example:
     #指定用户密码登录，并获取整个借阅列表
     > gzhulib -u ***** -p ***** -a 
      C语言接口与实现：创建可重用软件的技术 20141227
      Python入门经典：以解决计算问题为导向的Python编程实践 20150110
      PHP动态网页设计 20150316

     #直接查看本地用户即将过期或已过期的书籍
     > gzhulib 
      没有即将过期的书籍
     
     #查看30天内有哪些书籍即将过期
     > gzhulib -d 30
      书名：C语言接口与实现：创建可重用软件的技术
      还有8天过期

     #查看个人借阅史
     > gzhulib -his 20140901 20141219
      借阅日期   索引号   书名
      2014.09.27     J063/117           配色设计原理
      2014.09.27     D095.654/8       社会契约论
      2014.09.27     I565.65/25         荒谬的自由
      ``````

     #搜索书籍
     > gzhulib -s python
      易学Python
      (澳) Anthony Briggs著; 王威, 袁国忠译
      出版发行：北京: 人民邮电出版社, 2014
      索书号：TP311.561/3
      在馆数：2

      Head First Python : 中文版
      Paul Barry著; 林琪, 郭静等译
      出版发行：北京: 中国电力出版社, 2012
      索书号：TP311.56/246
      在馆数：1

      ``````
'''

class BookManager:
    def __init__(self, usernm, passwd):
        self.usernm = usernm
        self.passwd = passwd
        self.books = {}
        self.cookies = None
        self.login_url = 'http://lib.gzhu.edu.cn/opac/LoginSystem.aspx'
        self.search_url= 'http://lib.gzhu.edu.cn:8080/bookle'
        self.readlog_url = 'http://lib.gzhu.edu.cn/opac/RdrLogRetr.aspx'
        self.q = requests.Session()
        self.fmt = '%Y%m%d'

    def get_hidden_cls(self, soup):
        '''获取html中所有class为hidden的键值对'''
        para = {}
        for i in soup.findAll(type='hidden'):
            para.update( { i.get('name') : i.get('value') } )
        return para

    def http_get(self, promptstr, *l, **k):
        '''封装requests中的get方法'''
        try:
            return self.q.get(*l, **k)
        except requests.ConnectionError:
            print '在%s时发生了连接错误'%promptstr
            sys.exit(0)
        except requests.Timeout:
            print '在%s时发生了请求超时错误'%promptstr
            sys.exit(0)
        except requests.HTTPError:
            print '在%s时发生了罕见的无效HTTP响应错误'%promptstr
            sys.exit(0)
        except:
            print '发生未知错误'
            sys.exit(0)

    def http_post(self, promptstr, *l, **k):
        '''封装requests中的get方法'''
        try:
            return self.q.post(*l, **k)
        except requests.ConnectionError:
            print '在%s时发生了连接错误'%promptstr
            sys.exit(0)
        except requests.Timeout:
            print '在%s时发生了请求超时错误'%promptstr
            sys.exit(0)
        except requests.HTTPError:
            print '在%s时发生了罕见的无效HTTP响应错误'%promptstr
            sys.exit(0)
        except:
            print '发生未知错误'
            sys.exit(0)
        

    def login(self):
        '''登录帐号，获取图书页面'''
        login_rsp  = self.http_get('请求登录页面', self.login_url)
        login_html = login_rsp.text
        login_soup = BeautifulSoup(login_html)
        checknum = login_soup.find(id='labAppendix').text

        para = self.get_hidden_cls(login_soup)
        para.update({'UserName': self.usernm, 'Password':self.passwd, 'txtAppendix':checknum})
        rsp = self.http_post('用户登录图书馆网站', self.login_url, para) #登录

        if not rsp.ok:
            print 'http code is not 200'
            exit(0)
        pattern = re.compile('\d+')
        book_soup = BeautifulSoup(rsp.text)
        table = book_soup.find(id='ItemsGrid')
        books = {}
        for item in table.findAll('tr')[1:]:
            td = item.findAll('td')
            num = pattern.search(td[7].text).group().encode('utf-8') #归还日期的形式有可能是 *201501201  带星号的
            books[int(td[0].text)] = dict( name=td[1].text.encode('utf-8'), #书名
                                           back_date=num                    #归还日期
                                         ) 
        self.books = books
    
    def get_read_his(self, start=None, end=None):
        '''获取指定时间的借书记录'''
        if not start or not end:
            print '请指定查询时间'
            sys.exit(0)
        r = self.http_get('获取个人借阅史页面', self.readlog_url)

        readlog_soup = BeautifulSoup(r.text)
        para = self.get_hidden_cls(readlog_soup)
        para.update(dict(txtBegDate=start, txtEndDate=end, btnRetr='查询'))
        rsp = self.http_post('查询个人借阅史', self.readlog_url, para)

        readlog_soup = BeautifulSoup(rsp.text)
        table = readlog_soup.find(id='ItemsGrid')
        trs = table.findAll('tr')
        books_name = set()
        print '  借阅日期\t   索引号\t   书名'
        for tr in trs[1:]:
            tds = tr.findAll('td')
            name = tds[3].text
            date = tds[2].text
            index_num = tds[4].text
            print '  %-14s %-13s\t   %-6s'%(date, index_num, name)
            books_name.add(name)
        print '  你一共借过%d本书' % len(books_name)

    def check(self, day=30):
        '''检查是否有书籍即将过期或已过期'''
        from datetime import datetime, date, timedelta
        books = self.books
        day = timedelta(days=day)
        t = date.strftime(date.today(), self.fmt)
        today = datetime.strptime(t, self.fmt)
        not_book_need_return = True
        for _, book in books.items():
            back_date = datetime.strptime(book['back_date'], self.fmt)
            if (today+ day) >= back_date:
                not_book_need_return = False
                print "书名：%s "%book['name'] 
                if today < back_date:
                    print "还有%d天过期"%((back_date-today).days)
                elif today == back_date:
                    print "今天过期"
                else:
                    print "已经超过%d天"%((today-back_date).days)
        if not_book_need_return:
            print "没有即将过期的书籍"

    def all(self):
        '''获取图书列表'''
        books = self.books
        if books:
            print '\n 归还日期   书名'
            for _, book in books.items():
                print ' %s   %s'%(book['back_date'], book['name'])
            print

    def search(self, name):
        '''搜索书籍'''
        para = dict(
                    query=name,
                    matchsPerPage=10, #一页显示条目数
                    displayPages=15,  #总共显示多少页
                    index='default',  #索引模式
                    )
        page = 1 #索引页数
        while True:
            para.update(dict(searchPage=page))
            res = self.http_get('请求搜索结果页面', self.search_url, params=para)

            if not res.ok:
                print 'http code is not 200'
                sys.exit(0)

            book_soup = BeautifulSoup(res.text)
            if book_soup.find(id='search_noresult'):
                if page == 1:
                    print '检索找不到和你的查询相符的内容'
                else:
                    print '已经没有更多的内容'
                sys.exit(0)

            book_infos = book_soup.findAll(attrs={'class':'book_info'}) #取得该页所有书籍信息
            for book in book_infos:
                #html中每个book_info类都有两个h4标签
                h1 = book.findAll('h4')[0]
                h2 = book.findAll('h4')[1]
                publish = h1.text.split('\r\n')[0]   #出版社
                index_num = h2.text.split('\r\n')[0] #索书号
                have = h2.text.split('\r\n')[2][20:] #在馆数
                book_name = book.a.text #书名
                author = book.span.text #作者
                print '%s\n%s\n%s\n%s\n%s\n'%(book_name, author, publish, index_num, have)

            comm = raw_input('输入 n查看下一页 q退出\n')
            if comm == 'n':
                page += 1
                print '-'*60
            elif comm == 'q':
                sys.exit(0)
            else:
                print '非法操作'
                break
            
if __name__ == '__main__':
    argv = sys.argv[1:]
    if '-h' in argv:
        print help_doc
        sys.exit(0)
    if '-u' in argv or '-p' in argv:
        if '-u' in argv and '-p' in argv:
            usernm = argv[argv.index('-u')+1] #拿到用户名
            passwd = argv[argv.index('-p')+1] #拿到密码
        else:
            print 'error operation. type "lib -h" for help'
            sys.exit(0)
    bookmanager = BookManager(usernm, passwd)

    if '-s' in argv:
        name = argv[argv.index('-s')+1] #拿到搜索内容
        bookmanager.search(name)
        sys.exit(0)

    bookmanager.login() 
    if '-a' in argv:
        bookmanager.all()
    elif '-d' in argv:
        day = argv[argv.index('-d')+1] #拿到指定的天数
        bookmanager.check(int(day))
    elif '-his' in argv:
        start = argv[argv.index('-his')+1] #时期日期
        end = argv[argv.index('-his')+2]   #结束日期
        bookmanager.get_read_his(start, end)
    else:
        bookmanager.check()
    exit(0)
