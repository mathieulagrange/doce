import smtplib
import types
import inspect

class Config():
    project = types.SimpleNamespace()
    project.name = ''
    project.description = ''
    project.author = ''
    project.address = ''
    path = types.SimpleNamespace()
    path.input = ''
    path.processing = ''
    path.storage = ''
    path.output = ''

    def __str__(self):
        cString = ''
        atrs = dict(vars(type(self)))
        atrs.update(vars(self))
        atrs = [a for a in atrs if a[0] is not '_']

        for atr in atrs:
            if type(inspect.getattr_static(self, atr)) != types.FunctionType:
                if type(self.__getattribute__(atr)) == types.SimpleNamespace:
                    cString += atr+'\r\n'
                    for sns in self.__getattribute__(atr).__dict__.keys():
                        cString+='\t '+sns+': '+self.__getattribute__(atr).__getattribute__(sns)+'\r\n'
                else:
                    cString+='  '+atr+': '+self.__getattribute__(atr)+'\r\n'
        return cString

    def toHtml(self):
        return '<h3> '+self.__str__().replace('\r\n', '<br>').replace('\t', '&emsp;')+'</h3>'

    def sendMail(self, msg):

        header = 'From: expLanes mailer <expcode.mailer@gmail.com> \r\nTo: '+self.project.author+' '+self.project.address+'\r\nMIME-Version: 1.0 \r\nContent-type: text/html \r\nSubject: [expLanes] '+self.project.name+'\r\n'

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('expcode.mailer@gmail.com', 'tagsqtlirkznoxro')
        server.sendmail("expcode.mailer@gmail.com", self.project.address, header+msg+self.toHtml())
        server.quit()
