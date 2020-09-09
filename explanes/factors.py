import os
import inspect # remove ??
import types
import hashlib
import numpy as np
import copy
import glob
import explanes.utils as expUtils
import traceback
import logging
from joblib import Parallel, delayed

if expUtils.runFromNoteBook():
    from tqdm.notebook import tqdm as tqdm
else:
    from tqdm import tqdm as tqdm

class Factors():
  _setting = None
  _changed = False
  _currentSetting = 0
  _settings = []
  _mask = []
  _nonSingleton = []
  _factors = []
  _default = types.SimpleNamespace()

  def __setattr__(self, name, value):
    if not name == '_settings':
      _settings = []
    if not hasattr(self, name) and name[0] is not '_':
      self._factors.append(name)
    if hasattr(self, name) and type(inspect.getattr_static(self, name)) == types.FunctionType:
      raise Exception('the attribute '+name+' is shadowing a builtin function')
    if name is '_mask' or name[0] is not '_':
      self._changed = True
    if name[0] is not '_' and type(value) in {list, np.ndarray} and name not in self._nonSingleton:
      self._nonSingleton.append(name)
    return object.__setattr__(self, name, value)

  def __getattribute__(self, name):

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

  def __iter__(self):
    self.__setSettings__()
    self._currentSetting = 0
    return self

  def __next__(self):
    if self._currentSetting == len(self._settings):
      raise StopIteration
    else:
      self._setting = self._settings[self._currentSetting]
      # print(self._setting)
      self._currentSetting += 1
      return self

  def __getitem__(self, index):
    # print('get item')
    self.__setSettings__()
    # print(self._mask)
    return  self

  def setDefault(self, name, value, force=False):
    if hasattr(self, name):
      if not force and any(item in getattr(self, name) for item in [0, 'none']):
        print('Setting an explicit default modality to factor '+name+' should be handled with care as the factor already as an implicit default modality (O or none). This may lead to loss of data. Ensure that you have the flag <noneAndZero2void> set to False when using getId. You can remove this warning by setting the flag <force> to True.')
        if value not in getattr(self, name):
          print('The default modality of factor '+name+' should be available in the set of modalities.')
          raise ValueError
      self._default.__setattr__(name, value)
    else:
      print('Please set the factor '+name+' before choosing its default modality.')
      raise ValueError

  def doSetting(self, setting, function, logFileName, *parameters):
    failed = 0
    try:
      function(setting, *parameters)
    except Exception as e:
      if logFileName:
        failed = 1
        #print('setting '+setting.getId()+' failed')
        logging.info(traceback.format_exc())
      else:
        raise e
    return failed

  def do(self, function=None, *parameters, jobs=1, tqdmDisplay=True, logFileName=''):
    nbFailed = 0
    if logFileName:
      logging.basicConfig(filename=logFileName,
                level=logging.DEBUG,
                format='%(levelname)s: %(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S')

    print('Number of settings: '+str(len(self)))
    if jobs>1 or jobs<0:
      # print(jobs)
      result = Parallel(n_jobs=jobs, require='sharedmem')(delayed(self.doSetting)(setting, function, logFileName, *parameters) for setting in tqdm(self))
    else:
      with tqdm(total=len(self), disable= not tqdmDisplay) as t:
        for setting in self:
            description = ''
            if nbFailed:
                description = '[failed: '+str(nbFailed)+']'
            description += setting.describe()
            t.set_description(description)
            if function:
                nbFailed += self.doSetting(setting, function, logFileName, *parameters)
            else:
                print(setting.describe())
            t.update(1)
    return nbFailed

  def settings(self, mask=None):
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

  def __len__(self):
      self.__setSettings__()
      return len(self._settings)

  def __setSettings__(self):
      if self._changed:
        settings = []
        mask = copy.deepcopy(self._mask)
        self._setting = None

        # print('start get settings')
        # print(self._mask)
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

          # print('submask')
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
      return settings
    else:
      if len(s) > 0 and all(isinstance(ss, list) for ss in s):
        for ss in s:
          ss.insert(0, mask[done])
      else:
        s.insert(0, mask[done])
      return s

  def getFactorNames(self):
    return self._factors

  def clone(self):
    return copy.deepcopy(self)

  def nbModalities(self, factor):
      if isinstance(factor, int):
          name = self.getFactorNames()[factor]
      return len(object.__getattribute__(self, name))

  def clearPath(self, path, force=False, selector='*'):
      fileNames = []
      for s in self:
          for f in glob.glob(path+s.fileName()+selector):
              fileNames.append(f)
          for f in glob.glob(path+s.getId()+selector):
              fileNames.append(f)
      if len(fileNames) and (force or expUtils.query_yes_no('About to remove '+str(len(fileNames))+' files. Proceed ?')):
          for f in fileNames:
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

      f = self.clone()
      if relative:
          f._setting[factor] += modality
      else:
          f._setting[factor] = modality
      if f._setting[factor]< 0 or f._setting[factor] >= self.nbModalities(factor):
          return None
      else:
          return f

  def fileName(self):
      return self.getId('hash')

  def describe(self):
    return self.getId(singleton=False, sort=False, sep=' ')

  def getId(self, format='long', sort=True, singleton=True, noneAndZero2void=True, default2void=True, sep='_', omit=[]):
    id = []
    fNames = self.getFactorNames()
    if isinstance(omit, str):
      omit=[omit]
    elif isinstance(omit, int) :
      omit=[fNames[omit]]
    elif isinstance(omit, list) and len(omit) and isinstance(omit[0], int) :
      for oi, o in enumerate(omit):
        omit[oi]=fNames[o]
    if sort:
      fNames = sorted(fNames)
    for fIndex, f in enumerate(fNames):
      if f[0] != '_' and getattr(self, f) is not None and f not in omit:
          if (singleton or f in self._nonSingleton) and (not noneAndZero2void or (noneAndZero2void and (isinstance(getattr(self, f), str) and getattr(self, f).lower() != 'none') or  (not isinstance(getattr(self, f), str) and getattr(self, f) != 0))) and (not default2void or not hasattr(self._default, f) or (default2void and hasattr(self._default, f) and getattr(self._default, f) is not getattr(self, f))):
            id.append(expUtils.compressName(f, format))
            id.append(str(getattr(self, f)))
    if 'list' not in format:
      id = sep.join(id)
      if format is 'hash':
        id  = hashlib.md5(id.encode("utf-8")).hexdigest()
    return id

  def __str__(self):
    cString = ''
    atrs = dict(vars(type(self)))
    atrs.update(vars(self))
    atrs = [a for a in atrs if a[0] is not '_']

    for atr in atrs:
      if type(inspect.getattr_static(self, atr)) != types.FunctionType:
        cString+='  '+atr+': '+str(self.__getattribute__(atr))+'\r\n'
    return cString
