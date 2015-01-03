#coding:utf-8

from pyMail import  ReceiveMailDealer, SendMailDealer
import sys
import os
import zipfile, rarfile

try:
    import debug
    usernm = debug.usernm
    passwd = debug.passwd
    server_imap = debug.wangyi_imap
    server_smtp= debug.wangyi_smtp
    fpath = debug.fpath
    stmp_port = debug.stmp_port
except ImportError:
    usernm = passwd = qq = fpath = server_imap = server_smtp = stmp_port = None

def send_mail_by_zipfile(receiveuser, zip_file, username=usernm, password=passwd, server=server_smtp, port=stmp_port):
    smailManager = SendMailDealer(username, password, server, port)
    subject = raw_input('请输入邮件标题(默认为压缩文件的名字):  ')
    text = raw_input('请输入邮件内容: ')
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
    if option == filetype.ZIP:
        #压缩文件
        
        f = open(downloadfile, 'wb')
        f.write(data) #暂存压缩文件
        f.close()

        unzip(downloadfile)
        os.remove(downloadfile) #删除暂存的压缩文件

    #elif option == filetype.RAR:
    #    f = open(downloadfile, 'wb')
    #    f.write(data) #暂存压缩文件
    #    f.close()
    #    unrar(downloadfile)
    #    os.remove(downloadfile) #删除暂存的压缩文件

    elif option == filetype.NORMAL:
        #非压缩文件
        f = open(downloadfile, 'wb')
        f.write(data)
        print '下载文件......%s成功'%filename
        f.close()

def zip_(path, zip_name):
    print '压缩文件夹 %s 里的所有文件'%folder
    f = zipfile.ZipFile(path +'/' + zip_name + '.zip', 'w', zipfile.ZIP_DEFLATED)
    for _, _, filenames in os.walk(path):
        for filename in filenames:
            if not filename.startswith('.') and filename != (zip_name + '.zip'):
                f.write(path + '/' + filename)
    f.close()
    print '压缩完毕, 压缩文件：%s\n'%zip_name

class filetype():
    ZIP = 1
    NORMAL = 2
    RAR = 3

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
                        download(data, abs_path, filename, option=filetype.ZIP)
                    #elif fname.endswith('.rar'):
                    #    download(data, fpath, fname, option=filetype.RAR)
                    else:
                        #如果是普通文件
                        download(data, abs_path, filename, option=filetype.NORMAL)
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
        send_mail_by_zipfile(receiveuser, os.path.join(fpath + folder, folder + '.zip'))
