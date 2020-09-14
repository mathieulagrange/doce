import smtplib
import types
import inspect
import os
import time
import explanes as el

class Experiment():
  """

	Parameters
	----------

	Returns
	-------

	Examples
	--------

  """

  # list of attributes (preserving order of insertion for aloder versions of python)
  _atrs = []

  def __init__(self):
    self.project = types.SimpleNamespace()
    self.project.name = ''
    self.project.description = ''
    self.project.author = ''
    self.project.address = ''
    self.project.runId = str(int(time.time()))
    self.factor = el.Factor()
    self.parameter = types.SimpleNamespace()
    self.metric = el.Metric()
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
    """Create directories whose path described in experiment.path are not available.

    For each path set in experiment.path, create the directory if not existing. The user may be prompted before creation.

  	Parameters
  	----------

    force : bool
      If True, do not prompt the user before creating the missing directories.

      If False, prompt the user before creation of each missing directory.
    """
    for sns in self.__getattribute__('path').__dict__.keys():
      path = self.__getattribute__('path').__getattribute__(sns)
      if path and not os.path.exists(os.path.expanduser(path)):
        if force or el.util.query_yes_no(sns+' path: '+path+' does not exist. Do you want to create it ?'):
          os.makedirs(os.path.expanduser(path))

  def __str__(self, format='str'):
    """Provide a textual description of the experiment

    List all members of the class and theirs values

    parameters
    ----------
    format : str
      If 'str', return the description as a string.

      If 'html', return the description with an html format.

  	Returns
  	-------
    description : str
        If format == 'str' : a carriage return separated enumaration of the members of the class experiment.

        If format == 'html' : an html version of the description

  	Examples
  	--------

    >>> import explanes as el
    >>> print(el.Experiment())
    project:
      name:
      description:
      author:
      address:
      runId: 1600099391
    factor:
    parameter:
    metric:
    path:
      input:
      processing:
      storage:
      output:
    host:
    []

    >>> import explanes as el
    >>> print(el.Experiment().__str__(format='html'))
    <h3> <div>project: </div><div>  name: </div><div>  description: </div><div>  author: </div><div>  address: </div><div>  runId: 1600100112</div><div>factor: </div><div>parameter: </div><div>metric: </div><div>path: </div><div>  input: </div><div>  processing: </div><div>  storage: </div><div>  output: </div><div>host: </div><div>[]</div></h3>
    """
    description = ''
    for atr in self._atrs:
      if type(inspect.getattr_static(self, atr)) != types.FunctionType:
        if type(self.__getattribute__(atr)) == types.SimpleNamespace:
          description += atr+': \r\n'
          for sns in self.__getattribute__(atr).__dict__.keys():
            description+='  '+sns+': '+str(self.__getattribute__(atr).__getattribute__(sns))+'\r\n'
        elif isinstance(self.__getattribute__(atr), str):
          description+='  '+atr+': '+str(self.__getattribute__(atr))+'\r\n'
        else:
          description+=atr+': \r\n'+str(self.__getattribute__(atr))#+'\r\n'
    if format is 'html':
      description = '<div>'+description.replace('\r\n', '</div><div>').replace('\t', '&emsp;')+'</div>'
    return description

  def sendMail(self, title='', msg=''):
    header = 'From: expLanes mailer <expcode.mailer@gmail.com> \r\nTo: '+self.project.author+' '+self.project.address+'\r\nMIME-Version: 1.0 \r\nContent-type: text/html \r\nSubject: [expLanes] '+self.project.name+' id '+self.project.runId+' '+title+'\r\n'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('expcode.mailer@gmail.com', 'tagsqtlirkznoxro')
    server.sendmail("expcode.mailer@gmail.com", self.project.address, header+msg+'<h3> '+self.__str__(format = 'html')+'</h3>')
    server.quit

  def do(self, mask, function=None, jobs=1, tqdmDisplay=True, logFileName='', *parameters):
    return self.factor.settings(mask).do(function, self, *parameters, jobs=jobs, tqdmDisplay=tqdmDisplay, logFileName=logFileName)

  def cleanPath(self, path, mask, reverse=False, force=False, selector='*', idFormat={}):

    if '/' not in path and '\\' not in path:
      path = self.__getattribute__('path').__getattribute__(path)
    if path:
      self.factor.settings(mask).cleanPath(path, reverse, force, selector, idFormat, archivePath=self._archivePath)

  def cleanPaths(self, mask, reverse=False, force=False, selector='*', idFormat={}):
    for sns in self.__getattribute__('path').__dict__.keys():
      print('checking '+sns+' path')
      self.cleanPath(sns, mask, reverse, force, selector, idFormat)
