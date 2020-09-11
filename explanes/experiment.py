import smtplib
import types
import inspect
import os
import time
import explanes.util as eu
import explanes.factor as ef
import explanes.metric as em

class Experiment():
  _atrs = []

  def __init__(self):
    self.project = types.SimpleNamespace()
    self.project.name = ''
    self.project.description = ''
    self.project.author = ''
    self.project.address = ''
    self.project.runId = str(int(time.time()))
    self.factor = ef.Factor()
    self.parameter = types.SimpleNamespace()
    self.metric = em.Metric()
    self.path = types.SimpleNamespace()
    self.path.input = ''
    self.path.processing = ''
    self.path.storage = ''
    self.path.output = ''
    self.host = []
    self._idFormat = {}
    self._archivePath = ''
    self._factorFormatInReduce = 'shortCapital'

  def __setattr__(self, name, value):
    if not hasattr(self, name) and name[0] != '_':
      self._atrs.append(name)
    return object.__setattr__(self, name, value)

  def makePaths(self, force=False):
    for sns in self.__getattribute__('path').__dict__.keys():
      path = self.__getattribute__('path').__getattribute__(sns)
      if path and not os.path.exists(os.path.expanduser(path)):
        if force or eu.query_yes_no(sns+' path: '+path+' does not exist. Do you want to create it ?'):
          os.makedirs(os.path.expanduser(path))

  def __str__(self):
    cString = ''
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

  def do(self, mask, function=None, jobs=1, tqdmDisplay=True, logFileName='', *parameters):
    return self.factor.settings(mask).do(function, self, *parameters, jobs=jobs, tqdmDisplay=tqdmDisplay, logFileName=logFileName)

  def clean(self, path, mask, reverse=False, force=False, selector='*', idFormat={}):

    if '/' not in path and '\\' not in path:
      path = self.__getattribute__('path').__getattribute__(path)
    if path:
      self.factor.settings(mask).clean(path, reverse, force, selector, idFormat, archivePath=self._archivePath)

  def cleanExperiment(self, mask, reverse=False, force=False, selector='*', idFormat={}):
    for sns in self.__getattribute__('path').__dict__.keys():
      print('checking '+sns+' path')
      self.clean(sns, mask, reverse, force, selector, idFormat)
