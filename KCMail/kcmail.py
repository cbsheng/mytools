#coding:utf-8

from pyMail import  ReceiveMailDealer
from base import zip_, download, send_mail_by_zipfile
from constant import FileType
import sys
import os

try:
    import debug
    usernm = debug.usernm
    passwd = debug.passwd
    server_imap = debug.wangyi_imap
    server_smtp= debug.wangyi_smtp
    fpath = debug.fpath
    smtp_port = debug.smtp_port
except ImportError:
    usernm = passwd = qq = fpath = server_imap = server_smtp = smtp_port = None

if __name__ == '__main__':

    argv = os.sys.argv[1:]
    if '-u' in argv:
        '暂时使用'
        import getpass
        usernm= raw_input('请输入你的邮箱帐号: ')
        passwd= getpass.getpass(prompt='请输入你的邮箱密码: ')

    folder = raw_input('输入新文件夹名(默认名为new_folder)')
    fpath = raw_input('输入新文件夹存放路径(默认当前目录)')
    if not folder:
        folder = 'new_folder'
    if not fpath:
        fpath = './'
    abs_path = os.path.join(fpath, folder)

    if os.path.exists(folder + '/'):
        print '文件夹%s已存在!!!!'%folder
        sys.exit(0)
    os.mkdir(folder)

    mailmanger = ReceiveMailDealer(usernm, passwd, server_imap)

    t, nums = mailmanger.getUnread()
    nums = nums[0].split(' ')
    if nums == ['']:
        print '没有未读邮件'
        sys.exit(0)
    datas = {} #存放所有未读邮件的信息
    all_nums = [] #存放所有未读邮件的编号
    for num in nums:
        #加载所有未读邮件信息
        data = mailmanger.getMailInfo(num)
        datas.update({num : data})
        print '编号: %s  标题: %s  发件人: %s  附件个数: %d'%(num, datas[num]['subject'], datas[num]['from'][0], len(datas[num]['attachments']))
        all_nums.append(num)

    download_nums = raw_input('输入邮件编号(直接回车全选)')
    if not download_nums:
        download_nums = all_nums
    else:
        download_nums = download_nums.split(' ')
    if download_nums:
        subjects = set() #记录所有下载邮件的标题
        print '\n你选择的邮件编号有： ', [num for num in download_nums]
        for num in download_nums:
            if num in nums:
                subjects.add(datas[num]['subject'])
                attachments = datas[num]['attachments'] #取到该邮件的所有附件
                for atta in attachments:
                    filename = atta['name']
                    data = atta['data']
                    if filename.endswith('.zip'):
                        #如果是压缩文件
                        download(data, abs_path, filename, option=FileType.ZIP)
                    #elif fname.endswith('.rar'):
                    #    download(data, fpath, fname, option=fileType.RAR)
                    else:
                        #如果是普通文件
                        download(data, abs_path, filename, option=FileType.NORMAL)
        print '所有邮件里的附件下载完成\n'
    else:
        print '输入为空，自动退出'
        sys.exit(0)

    zip_(fpath + folder, folder)

    #生成一个 readme 文件记录下载了哪些邮件的附件
    readme = os.path.join(abs_path, 'readme.txt')
    if not os.path.exists(readme):
        f = open(readme, 'wb')
        f.write(' '.join(list(subjects)))
    else:
        f = open(readme, 'rb+')
        content_l =f.readline().split(' ')
        for subject in subjects:
            if subject in content_l:
                subjects.remove(subject)
        if subjects:
            f.seek(0,2) #文件位置指针移到最后
            f.write(' ' + ' '.join(list(subjects)))
    f.close()

    #将压缩文件作为附件发送
    if not raw_input('是否发送邮件?(直接回车确认,任意输入则取消发送邮件)'):
        receiveuser = raw_input('请输入接受方邮箱: ')
        send_mail_by_zipfile( receiveuser, 
                              os.path.join(fpath + folder, folder + '.zip'), 
                              usernm, passwd, 
                              server_smtp, smtp_port )
