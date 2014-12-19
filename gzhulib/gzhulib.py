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
'''

class BookManager:
    def __init__(self, usernm, passwd):
        self.usernm = usernm
        self.passwd = passwd
        self.login_url = 'http://lib.gzhu.edu.cn/opac/LoginSystem.aspx'
        self.search_url= 'http://lib.gzhu.edu.cn:8080/bookle'
        self.books = {}

    def login(self):
        '''登录帐号，获取图书页面'''
        login_rsp  = requests.get(self.login_url)
        login_html = login_rsp.text
        login_soup = BeautifulSoup(login_html)
        checknum = login_soup.find(id='labAppendix').text

        para = {}
        for i in login_soup.findAll(type='hidden'):
            para.update( { i.get('name') : i.get('value') } )

        para.update({'UserName': self.usernm, 'Password':self.passwd, 'txtAppendix':checknum})
        try:
            rsp = requests.post(self.login_url, para)
        except:
            print 'http post操作发生错误'

        if not rsp.ok:
            print 'http code is not 200'
            exit(0)
        pattern = re.compile('\d+')
        book_soup = BeautifulSoup(rsp.text)
        table = book_soup.find(id='ItemsGrid')
        books = {}
        for item in table.findAll('tr')[1:]:
            td = item.findAll('td')
            num = pattern.search(td[7].text).group()
            books[int(td[0].text)] = dict( name=td[1].text.encode('utf-8'),
                                           back_date=int(num))
        self.books = books
    
    def check(self, day=3):
        '''检查是否有书籍即将过期或已过期'''
        books = self.books
        from datetime import date
        today = int(date.strftime(date.today(), '%Y%m%d'))
        flag = False
        #import ipdb;ipdb.set_trace()
        for _, book in books.items():
            if (today+ day) >= book['back_date']:
                print "书名：%s "%book['name'] 
                if today < book['back_date']:
                    print "还有%d天过期"%(book['back_date']-today)
                elif today == book['back_date']:
                    print "今天过期"
                else:
                    print "已经超过%d天"%(today-book['back_date'])
                flag = True
        if not flag:
            print "没有即将过期的书籍"

    def all(self):
        '''获取图书列表'''
        books = self.books
        if books:
            print '\n 归还日期   书名'
            for _, book in books.items():
                print ' %d   %s'%(book['back_date'], book['name'])
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
            try:
                res = requests.get(self.search_url, params=para)
            except:
                print "http get操作发生错误"
                sys.exit(0)

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
            elif comm == 'q':
                sys.exit(0)
            else:
                print '非法操作'
                break
            
if __name__ == '__main__':
    argv = sys.argv[1:]
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
    elif '-h' in argv:
        print help_doc
    elif '-d' in argv:
        day = argv[argv.index('-d')+1] #拿到指定的天数
        bookmanager.check(int(day))
    else:
        bookmanager.check()
    exit(0)