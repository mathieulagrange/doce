import smtplib
import types
import inspect
import os
import time
import explanes.utils as expUtils
import explanes.factors as expFactors
import explanes.metrics as expMetrics

class Config():
  _atrs = []

  def __init__(self):
    self.project = types.SimpleNamespace()
    self.project.name = ''
    self.project.description = ''
    self.project.author = ''
    self.project.address = ''
    self.project.runId = str(int(time.time()))
    self.factor = expFactors.Factors()
    self.parameter = types.SimpleNamespace()
    self.metric = expMetrics.Metrics()
    self.path = types.SimpleNamespace()
    self.path.input = ''
    self.path.processing = ''
    self.path.storage = ''
    self.path.output = ''
    self.host = []

  def __setattr__(self, name, value):
    if not hasattr(self, name) and name[0] is not '_':
      self._atrs.append(name)
    return object.__setattr__(self, name, value)

  def makePaths(self, force=False):
    for sns in self.__getattribute__('path').__dict__.keys():
      path = self.__getattribute__('path').__getattribute__(sns)
      if path and not os.path.exists(os.path.expanduser(path)):
        if force or expUtils.query_yes_no(sns+' path: '+path+' does not exist. Do you want to create it ?'):
          os.makedirs(os.path.expanduser(path))

  def __str__(self):
    cString = ''
    # atrs = dict(vars(type(self)))
    # atrs.update(vars(self))
    # atrs = [a for a in atrs if a[0] is not '_']
    print(self._atrs)
    for atr in self._atrs:
      if type(inspect.getattr_static(self, atr)) != types.FunctionType:
        if type(self.__getattribute__(atr)) == types.SimpleNamespace:
          cString += atr+': \r\n'
          for sns in self.__getattribute__(atr).__dict__.keys():
            cString+='  '+sns+': '+str(self.__getattribute__(atr).__getattribute__(sns))+'\r\n'
        elif isinstance(self.__getattribute__(atr), str):
          cString+='  '+atr+': '+str(self.__getattribute__(atr))+'\r\n'
        else:
          cString+=atr+': \r\n'+str(self.__getattribute__(atr))#+'\r\n'
    return cString

  def toHtml(self):
    return '<h3> '+self.__str__().replace('\r\n', '<br>').replace('\t', '&emsp;')+'</h3>'

  def sendMail(self, title='', msg=''):
    header = 'From: expLanes mailer <expcode.mailer@gmail.com> \r\nTo: '+self.project.author+' '+self.project.address+'\r\nMIME-Version: 1.0 \r\nContent-type: text/html \r\nSubject: [expLanes] '+self.project.name+' id '+self.project.runId+' '+title+'\r\n'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('expcode.mailer@gmail.com', 'tagsqtlirkznoxro')
    server.sendmail("expcode.mailer@gmail.com", self.project.address, header+msg+self.toHtml())
    server.quit

  def do(self, mask, function, jobs=1, tqdmDisplay=True, logFileName='', *parameters):
    return self.factor.settings(mask).do(function, self, *parameters, jobs=jobs, tqdmDisplay=tqdmDisplay, logFileName=logFileName)

  def clearPath(self, mask, path, force=False, selector='*'):
    return self.factor.settings(mask).clearPath(path, force, selector)

  def clearPaths(self, mask, force=False, selector='*'):
    for sns in self.__getattribute__('path').__dict__.keys():
      path = self.__getattribute__('path').__getattribute__(sns)
      self.clearPath(mask, path, force, selector)
