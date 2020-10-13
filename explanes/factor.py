import os
import inspect
import types
import hashlib
import numpy as np
import tables as tb
import pandas as pd
import copy
import glob
import explanes.util as eu
import traceback
import logging
from joblib import Parallel, delayed
from subprocess import call
import time

if eu.inNotebook():
    from tqdm.notebook import tqdm as tqdm
else:
    from tqdm import tqdm as tqdm

class Factor():
  """one liner

  Desc

  Examples
  --------

  """
  _setting = None
  _changed = False
  _currentSetting = 0
  _settings = []
  _mask = []
  _nonSingleton = []
  _factors = []
  _default = types.SimpleNamespace()
  _parallel = False

  def __setattr__(
    self,
    name,
    value
    ):
    if not name == '_settings':
      _settings = []
    if not hasattr(self, name) and name[0] != '_':
      self._factors.append(name)
    if hasattr(self, name) and type(inspect.getattr_static(self, name)) == types.FunctionType:
      raise Exception('the attribute '+name+' is shadowing a builtin function')
    if name == '_mask' or name[0] != '_':
      self._changed = True
    if name[0] != '_' and type(value) in {list, np.ndarray} and name not in self._nonSingleton:
      self._nonSingleton.append(name)
    return object.__setattr__(self, name, value)

  def __getattribute__(
    self,
    name
    ):
    """one liner

  	Desc

  	Parameters
  	----------

  	Returns
  	-------

  	See Also
  	--------

  	Examples
  	--------

    """
    value = object.__getattribute__(self, name)
    if name[0] != '_' and self._setting and type(inspect.getattr_static(self, name)) != types.FunctionType:
      idx = self.getFactorNames().index(name)
      if self._setting[idx] == -2:
        value = None
      else:
        if  type(inspect.getattr_static(self, name)) in {list, np.ndarray} :
          try:
            value = value[self._setting[idx]]
          except IndexError:
            value = 'null'
            print('Error: factor '+name+' have modalities 0 to '+str(len(value)-1)+'. Requested '+str(self._setting[idx]))
            raise
    return value

  def __iter__(
    self
    ):
    """one liner

  	Desc

    """
    self.__setSettings__()
    self._currentSetting = 0
    return self

  def __next__(
    self
    ):
    """one liner

  	Desc

    """
    if self._currentSetting == len(self._settings):
      raise StopIteration
    else:
      self._setting = self._settings[self._currentSetting]
      # print(self._setting)
      self._currentSetting += 1
      if self._parallel:
        return copy.deepcopy(self)
      else:
        return self #  copy.deepcopy(self)

  def __getitem__(self, index):
    # print('get item')
    self.__setSettings__()
    # print(self._mask)
    return  self

  def setDefault(
    self,
    name,
    value,
    force=False
    ):
    """one liner

  	Desc

  	Parameters
  	----------

  	Returns
  	-------

  	See Also
  	--------

  	Examples
  	--------

    """
    if hasattr(self, name):
      if not force and any(item in getattr(self, name) for item in [0, 'none']):
        print('Setting an explicit default modality to factor '+name+' should be handled with care as the factor already as an implicit default modality (O or none). This may lead to loss of data. Ensure that you have the flag <hideNonAndZero> set to False when using method id(). You can remove this warning by setting the flag <force> to True.')
        if value not in getattr(self, name):
          print('The default modality of factor '+name+' should be available in the set of modalities.')
          raise ValueError
      self._default.__setattr__(name, value)
    else:
      print('Please set the factor '+name+' before choosing its default modality.')
      raise ValueError

  def doFunction(
    self,
    function,
    experiment,
    logFileName,
    *parameters
    ):
    failed = 0
    try:
      function(self, experiment, *parameters)
    except Exception as e:
      if logFileName:
        failed = 1
        #print('setting '+setting.id()+' failed')
        logging.info(traceback.format_exc())
      else:
        raise e
    return failed

  def do(
    self,
    function=None,
    experiment=None,
    *parameters,
    nbJobs=1,
    progress=True,
    logFileName='',
    mailInterval=0):
    """Iterate over the setting set and operate the function with the given parameters.

    This function is wrapped by :meth:`explanes.experiment.Experiment.do`, which should be more convenient to use. Please refer to this method for usage.

    See Also
    --------

    explanes.experiment.Experiment.do

    """
    nbFailed = 0
    if logFileName:
      logging.basicConfig(filename=logFileName,
                level=logging.DEBUG,
                format='%(levelname)s: %(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S')
    if progress:
      print('Number of settings: '+str(len(self)))
    if nbJobs>1 or nbJobs<0:
      # print(nbJobs)
      self._parallel = True
      result = Parallel(n_jobs=nbJobs, require='sharedmem')(delayed(setting.doSetting)(function, experiment, logFileName, *parameters) for setting in self)
      self._parallel = False
    else:
      startTime = time.time()
      stepTime = startTime
      with tqdm(total=len(self), disable= not progress) as t:
        for iSetting, setting in enumerate(self):
            description = ''
            if nbFailed:
                description = '[failed: '+str(nbFailed)+']'
            description += setting.describe()
            t.set_description(description)
            if function:
                nbFailed += setting.doFunction(function, experiment, logFileName, *parameters)
            else:
                print(setting.describe())
            delay = (time.time()-stepTime)
            if mailInterval>0 and iSetting<len(self)-1  and delay > mailInterval/(60**2) :
              stepTime = time.time()
              percentage = int((iSetting+1)/len(self)*100)
              message = '{}% of settings done: {} over {} <br>Time elapsed: {}'.format(percentage, iSetting+1, len(self), time.strftime('%dd %Hh %Mm %Ss', time.gmtime(stepTime-startTime)))
              experiment.sendMail('progress {}% '.format(percentage), message)
            t.update(1)
    return nbFailed

  def settings(
    self,
    mask=None
    ):
    """one liner

  	Desc

    """
    mask = copy.deepcopy(mask)
    nbFactors = len(self.getFactorNames())
    if mask is None or len(mask)==0 or (len(mask)==1 and len(mask)==0) :
       mask = [[-1]*nbFactors]
    if isinstance(mask, list) and not all(isinstance(x, list) for x in mask):
        mask = [mask]


    for im, m in enumerate(mask):
      if len(m) < nbFactors:
        mask[im] = m+[-1]*(nbFactors-len(m))
      for il, l in enumerate(m):
          if not isinstance(l, list) and l > -1:
              mask[im][il] = [l]
    self._mask = mask
    return self

  def __len__(
    self
    ):
    """one liner

  	Desc

    """
    self.__setSettings__()
    return len(self._settings)

  def __setSettings__(
    self
    ):
    """one liner

  	Desc

    """
    if self._changed:
      settings = []
      mask = copy.deepcopy(self._mask)
      self._setting = None

      for m in mask:
        # handle -1 in mask
        for mfi, mf in enumerate(m):
          if isinstance(mf, int) and mf == -1 and mfi<len(self.getFactorNames()):
            attr = self.__getattribute__(self.getFactorNames()
            [mfi])
            # print(attr)
            # print(isinstance(attr, int))
            if isinstance(attr, list) or isinstance(attr, np.ndarray):
              m[mfi] = list(range(len(attr)))
            else:
              m[mfi] = [0]

        s = self.__setSettingsMask__(m, 0)
        if all(isinstance(ss, list) for ss in s):
          for ss in s:
            settings.append(ss)
        else:
          settings.append(s)
      self._changed = False
      self._settings = settings

  def __setSettingsMask__(self, mask, done):
    if done == len(mask):
      return []

    s = self.__setSettingsMask__(mask, done+1)
    if isinstance(mask[done], list):
      settings = []
      for mod in mask[done]:
        if len(s) > 0:
          for ss in s:
            if isinstance(ss, list):
                mList = list(ss)
            else:
                mList = [ss]
            mList.insert(0, mod)
            settings.append(mList)
        else:
            mList = list(s)
            mList.insert(0, mod)
            settings.append(mList)
    else:
      settings = s
      if len(settings) > 0 and all(isinstance(ss, list) for ss in settings):
        for ss in settings:
          ss.insert(0, mask[done])
      else:
        settings.insert(0, mask[done])
    return settings

  def getFactorNames(
    self
    ):
    """Returns the list of factors defined in the Class.

  	Returns a list of str with the names of the factors defined in the Class.

    """
    return self._factors

  def nbModalities(
    self,
    factor
    ):
    """Returns the number of :term:`modalities<modality>` for a given :term:`factor`.

  	Returns the number of :term:`modalities<modality>` for a given :term:`factor`.

    """
    if isinstance(factor, int):
      name = self.getFactorNames()[factor]
    return len(object.__getattribute__(self, name))

  def cleanH5(self, path, reverse=False, force=False, settingEncoding={}):
    h5 = tb.open_file(path, mode='a')
    if reverse:
      ids = [setting.id(**settingEncoding) for setting in self]
      for g in h5.iter_nodes('/'):
        if g._v_name not in ids:
          h5.remove_node(h5.root, g._v_name, recursive=True)
    else:
      for setting in self:
        groupName = setting.id(**settingEncoding)
        if h5.root.__contains__(groupName):
          h5.remove_node(h5.root, groupName, recursive=True)
    h5.close()

    # repack
    outfilename = path+'Tmp'
    command = ["ptrepack", "-o", "--chunkshape=auto", "--propindexes", path, outfilename]
    # print('Original size is %.2fMiB' % (float(os.stat(path).st_size)/1024**2))
    if call(command) != 0:
      print('Unable to repack. Is ptrepack installed ?')
    else:
      # print('Repacked size is %.2fMiB' % (float(os.stat(outfilename).st_size)/1024**2))
      os.rename(outfilename, path)


  def cleanDataSink(
    self,
    path,
    reverse=False,
    force=False,
    selector='*',
    settingEncoding={},
    archivePath=''
    ):
    """Clean a data sink by considering the settings set.

  	Returns the number of :term:`modalities<modality>`, for a given :term:`factor`. This method is more conveniently used by considering the method explanes.experiment.Experiment.cleanDataSink, please see its documentation for usage.

    """
    path = os.path.expanduser(path)
    if path.endswith('.h5'):
      self.cleanH5(path, reverse, force, settingEncoding)
    else:
      fileNames = []
      for setting in self:
          # print(path+'/'+setting.id(**settingEncoding)+selector)
          for f in glob.glob(path+'/'+setting.id(**settingEncoding)+selector):
              fileNames.append(f)
      if reverse:
        complete = []
        for f in glob.glob(path+'/'+selector):
            complete.append(f)
        # print(fileNames)
        fileNames = [i for i in complete if i not in fileNames]
      #   print(complete)
      # print(fileNames)
      # print(len(fileNames))
      if archivePath:
        destination = 'move to '+archivePath+' '
      else:
        destination = 'remove '
      if len(fileNames) and (force or eu.query_yes_no('About to '+destination+str(len(fileNames))+' files from '+path+' \n Proceed ?')):
          for f in fileNames:
              if archivePath:
                os.rename(f, archivePath+'/'+os.path.basename(f))
              else:
                os.remove(f)

  def alternative(self, factor, modality, positional=False, relative=False):
      if isinstance(modality, int) and modality<0:
          relative = True
      if isinstance(factor, str):
          factor = self.getFactorNames().index(factor)
      if not positional and not relative:
          factorName = self.getFactorNames()[factor]
          set = self._setting
          self._setting = None
          modalities = self.__getattribute__(factorName)
          modality = modalities.index(modality)
          self._setting = set

      f = copy.deepcopy(self)
      if relative:
          f._setting[factor] += modality
      else:
          f._setting[factor] = modality
      if f._setting[factor]< 0 or f._setting[factor] >= self.nbModalities(factor):
          return None
      else:
          return f

  def describe(self):
    return self.id(singleton=False, sort=False, factorSeparator=' ', hideNonAndZero=False)

  def id(self, format='long', sort=True, singleton=True, hideNonAndZero=True, hideDefault=True, factorSeparator='_', hideFactor=[]):
    id = []
    fNames = self.getFactorNames()
    if isinstance(hideFactor, str):
      hideFactor=[hideFactor]
    elif isinstance(hideFactor, int) :
      hideFactor=[fNames[hideFactor]]
    elif isinstance(hideFactor, list) and len(hideFactor) and isinstance(hideFactor[0], int) :
      for oi, o in enumerate(hideFactor):
        hideFactor[oi]=fNames[o]
    if sort:
      fNames = sorted(fNames)
    for fIndex, f in enumerate(fNames):
      if f[0] != '_' and getattr(self, f) is not None and f not in hideFactor:
          if (singleton or f in self._nonSingleton) and (not hideNonAndZero or (hideNonAndZero and (isinstance(getattr(self, f), str) and getattr(self, f).lower() != 'none') or  (not isinstance(getattr(self, f), str) and getattr(self, f) != 0))) and (not hideDefault or not hasattr(self._default, f) or (hideDefault and hasattr(self._default, f) and getattr(self._default, f) != getattr(self, f))):
            id.append(eu.compressDescription(f, format))
            id.append(str(getattr(self, f)))
    if 'list' not in format:
      id = factorSeparator.join(id)
      if format == 'hash':
        id  = hashlib.md5(id.encode("utf-8")).hexdigest()
    return id

  def __str__(self):
    cString = ''
    l = 1
    for ai, atr in enumerate(self._factors):
      cString+='  '+str(ai)+'  '+atr+': '+str(self.__getattribute__(atr))+'\r\n'
    return cString

  def asPandaFrame(self):
    l = 1
    for ai, atr in enumerate(self._factors):
      if isinstance(self.__getattribute__(atr), list):
        l = max(l, len(self.__getattribute__(atr)))
      elif isinstance(self.__getattribute__(atr), np.ndarray):
        l = max(l, len(self.__getattribute__(atr)))

    table = []
    for atr in self._factors:
      line = []
      line.append(atr)
      for il in range(l):
        if isinstance(self.__getattribute__(atr), list) and len(self.__getattribute__(atr)) > il :
          line.append(self.__getattribute__(atr)[il])
        elif isinstance(self.__getattribute__(atr), np.ndarray) and len(self.__getattribute__(atr)) > il :
          line.append(self.__getattribute__(atr)[il])
        elif il<1:
          line.append(self.__getattribute__(atr))
        else:
          line.append('')
      table.append(line)
    columns = []
    columns.append('Factor')
    for il in range(l):
      columns.append(il)
    return pd.DataFrame(table, columns=columns)
