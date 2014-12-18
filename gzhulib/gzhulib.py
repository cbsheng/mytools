#coding:utf-8

import requests
from BeautifulSoup import BeautifulSoup
import re
import sys

#本地使用可以直接写死这两个变量
usernm = None
passwd = None

jelp_doc = '''
  Example:
     > gzhulib -u ***** -p ***** -a 
      C语言接口与实现：创建可重用软件的技术 20141227
      Python入门经典：以解决计算问题为导向的Python编程实践 20150110
      PHP动态网页设计 20150316
      C程序性能优化：20个实验与达人技巧 20141229
      Python网络编程基础 20141224
      计算机网络 20150316
      PHP语言精粹 20150316
     > gzhulib 
      没有即将过期的书籍
'''

class BookManager:
    def __init__(self, usernm, passwd):
        self.usernm = usernm
        self.passwd = passwd
        self.login_url = 'http://lib.gzhu.edu.cn/opac/LoginSystem.aspx'
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
            print 'post操作发生错误'
        
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
            books[int(td[0].text)] = dict( name=td[1].text,
                                           back_date=int(num))
        self.books = books
    
    def check(self):
        '''检查是否有书籍即将到期'''
        books = self.books
        from datetime import date
        today = int(date.strftime(date.today(), '%Y%m%d'))
        flag = False
        for _, book in books.items():
            if (today+ 3) >= book['back_date']:
                print "书名：%s "%book['name'] 
                if today < book['book_date']:
                    print "还有%天过期"%(book['back_date']-today)
                elif today == book['book_date']:
                    print "今天过期"
                else:
                    print "已经超过%天"%(today-book['back_date'])
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

if __name__ == '__main__':
    argv = sys.argv[1:]
    if '-u' in argv or '-p' in argv:
        if '-u' in argv and '-p' in argv:
            usernm = argv[argv.index('-u')+1]
            passwd = argv[argv.index('-p')+1]
        else:
            print 'error operation. type "lib -h" for help'
            sys.exit(0)
    bookmanager = BookManager(usernm, passwd)
    if '-a' in argv:
        bookmanager.login()
        bookmanager.all()
    elif '-h' in argv:
        print help_doc
    else:
        bookmanager.check()
    exit(0)
