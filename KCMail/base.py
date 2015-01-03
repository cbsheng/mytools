#coding:utf-8
from constant import FileType
from pyMail import SendMailDealer
import zipfile, rarfile
import os, sys

def send_mail_by_zipfile(receiveuser, zip_file, usernm, passwd, server, port):
    '''使用 pyMail 里的 SendMailDealer 类发送压缩文件'''
    smailManager = SendMailDealer(usernm, passwd, server, port)
    subject = raw_input('请输入邮件标题(默认为压缩文件的名字):  ')
    text = raw_input('请输入邮件正文内容: ')
    if not subject:
        subject = os.path.basename(zip_file)[:-4]
    if not text:
        text = ''
    smailManager.setMailInfo(receiveuser, subject, text, 'html', zip_file)
    smailManager.sendMail()

def check_rename(abs_path_fname):
    '''检查文件是否已存在'''
    if os.path.exists(abs_path_fname):
        fname = os.path.basename(abs_path_fname)
        fpath = os.path.dirname(abs_path_fname)
        new_fname = 'new_' + fname
        print '%s 已经存在，将自动改名为 %s'%(fname, new_fname)
        return os.path.join(fpath, new_fname)
    return abs_path_fname

def unzip(fname):
    '''解压 zip 文件'''
    basename = os.path.basename(fname)
    dirname = os.path.dirname(fname)
    zobj = zipfile.ZipFile(fname)
    print '###开始解压文件.......... %s'%basename
    for name in zobj.namelist():
        if not name.startswith('__MACOSX'):  #‘__MACOSX’为 mac 下压缩文件特有的
            abs_path_fname = check_rename(os.path.join(dirname, name))
            f = open(abs_path_fname, 'wb' )
            f.write(zobj.read(name))
            print '下载文件......%s成功'%name
            f.close()
    print '###解压完成'

def unrar(fname):
    '''解压 rar 文件'''
    basename = os.path.basename(fname)
    print '开始解压文件.......... %s'%basename
    robj = rarfile.RarFile(fname)
    for name in robj.namelist():
        name = str(name)
        if not name == basename[:-4]: 
            #rar 压缩文件会有一个等于文件名的0字节文件,需要忽略
            f = open(name[len(basename )+ 2:], 'wb')
            f.write(robj.read(name)) #TODO rarfile 库对于读取 doc/ppt 文件存在问题
            print '下载文件......%s成功'%name
            f.close()
    print '解压完成'

def download(data, filepath, filename, option=None):
    '''对压缩文件和非压缩文件进行下载. fpath:路径, fname:文件名'''
    if not option:
        print '文件类型不明确!!!!!'
        sys.exit(0)

    downloadfile = os.path.join(filepath, filename)
    downloadfile = check_rename(downloadfile)
    if option == FileType.ZIP:
        #压缩文件
        
        f = open(downloadfile, 'wb')
        f.write(data) #暂存压缩文件
        f.close()

        unzip(downloadfile)
        os.remove(downloadfile) #删除暂存的压缩文件

    #elif option == FileType.RAR:
    #    f = open(downloadfile, 'wb')
    #    f.write(data) #暂存压缩文件
    #    f.close()
    #    unrar(downloadfile)
    #    os.remove(downloadfile) #删除暂存的压缩文件

    elif option == FileType.NORMAL:
        #非压缩文件
        f = open(downloadfile, 'wb')
        f.write(data)
        print '下载文件......%s成功'%filename
        f.close()

def zip_(path, zip_name):
    print '压缩文件夹 %s 里的所有文件' % os.path.basename(path)
    f = zipfile.ZipFile(os.path.join(path, zip_name + '.zip'), 'w', zipfile.ZIP_DEFLATED)
    for _, _, filenames in os.walk(path):
        for filename in filenames:
            if not filename.startswith('.') and filename != (zip_name + '.zip'):
                f.write(path + '/' + filename)
    f.close()
    print '压缩完毕, 压缩文件：%s\n'%zip_name
