import os
import inspect # remove ??
import types
import re
import hashlib
import numpy as np
import copy
import glob
import explanes.utils as expUtils
import traceback
import logging

if expUtils.runFromNoteBook():
    from tqdm.notebook import tqdm as tqdm
else:
    from tqdm import tqdm as tqdm

import collections

class OrderedClassMembers(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(self, name, bases, classdict):
        classdict['__ordered__'] = [key for key in classdict.keys()
                if key not in ('__module__', '__qualname__')]
        return type.__new__(self, name, bases, classdict)

class Factors(metaclass=OrderedClassMembers):
  _setting = None
  _changed = False
  _currentSetting = 0
  _settings = []
  _mask = []
  _nonSingleton = []

  def __setattr__(self, name, value):
    if hasattr(self, name) and type(inspect.getattr_static(self, name)) == types.FunctionType:
      raise Exception('the attribute '+name+' is shadowing a builtin function')
    if name is '_mask' or name[0] is not '_':
      self._changed = True
    if name[0] is not '_' and type(value) in {list, np.ndarray} and name not in self._nonSingleton:
      self._nonSingleton.append(name)
    return object.__setattr__(self, name, value)

  def __getattribute__(self, name):
    value = object.__getattribute__(self, name)
    # print(name)
    # print(type(inspect.getattr_static(self, name))) hasattr(self, '_setting')
    if name[0] != '_' and self._setting and type(inspect.getattr_static(self, name)) != types.FunctionType:
      idx = self.getFactorNames().index(name)
      # print(self.getFactorNames())
      # print(idx)
      # print(self._setting)
      if self._setting[idx] == -2:
        value = None
      else:
        if  type(inspect.getattr_static(self, name)) in {list, np.ndarray} :
          # print('filt setting ')
          # print(self._setting)
          # print(value)
          value = value[self._setting[idx]]
    return value

  def __iter__(self):
    # expand the mask to an iterable format aka -1 to full list
    #build a list of settings
    # print('iter mask: ')
    # print(self._mask)
    self.__setSettings__()
    # print('all settings: ')
    # print(self._settings)
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
    self._setting = self._settings[index]
      # print(self._mask)
    return  self

  def do(self, function, *parameters, logFileName=''):
    if logFileName:
      logging.basicConfig(filename=logFileName,
                level=logging.DEBUG,
                format='%(levelname)s: %(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S')

    print('Number of settings: '+str(len(self)))
    with tqdm(total=len(self)) as t:
      for setting in self:
        t.set_description(setting.describe())
        try:
          function(setting, *parameters)
        except Exception as e:
          if logFileName:
            print('setting '+setting.getId()+' failed')
            logging.info(traceback.format_exc())
          else:
            raise e
        t.update()

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
    # print('mask')
    self._mask = mask
    # print(nbFactors)
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
            if isinstance(mf, int) and mf == -1:
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
    # print(mask)
    if done == len(mask):
      return []

    s = self.__setSettingsMask__(mask, done+1)
    # print('mask[done]')
    # print(mask[done])
    # print('s')
    # print(s)
    if isinstance(mask[done], list):
      settings = []
      for mod in mask[done]:
        # print('mod')
        # print(mod)

        if len(s) > 0:
          for ss in s:
            if isinstance(ss, list):
                mList = list(ss)
            else:
                mList = [ss]
            mList.insert(0, mod)
            # print(mList)
            # print('mList')
            settings.append(mList)
            # print(settings)
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
    return [s for s in self.__dict__.keys() if s[0] is not '_']

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

  def alternative(self, factor, modality, relative=False):
      if isinstance(factor, str):
          factor = self.getFactorNames().index(factor)
      if isinstance(modality, str):
          factorName = self.getFactorNames()[factor]
          set = self._setting
          self._setting = None
          modality = self.__getattribute__(factorName).index(modality)
          self._setting = set
      if modality<0:
          relative = True
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

  def getId(self, type='long', sort=True, singleton=True, omitVoid=True, sep='_', omit=[]):
    id = []
    fNames = self.getFactorNames()
    if sort:
        fNames = sorted(fNames)
    if isinstance(omit, str):
      omit=[omit]
    for fIndex, f in enumerate(fNames):
      # print(getattr(self, f))
      if f[0] != '_' and getattr(self, f) is not None and f not in omit:
          if (singleton or f in self._nonSingleton) and (omitVoid and (isinstance(getattr(self, f), str) and getattr(self, f).lower() != 'none') or (not isinstance(getattr(self, f), str) and getattr(self, f) != 0)):
            if type is 'long' or type is 'hash':
              sf = f
            if type is 'shortUnderscore':
              sf = ''.join([itf[0] for itf in f.split('_')])
            if type is 'shortCapital':
              sf = f[0]+''.join([itf[0] for itf in re.findall('[A-Z][^A-Z]*', f)]).lower()
            id.append(sf)
            id.append(str(getattr(self, f)))
    id = sep.join(id)
    if type is 'hash':
      id  = hashlib.md5(id.encode("utf-8")).hexdigest()
    return id

  def __str__(self):
    cString = ''
    atrs = dict(vars(type(self)))
    atrs.update(vars(self))
    atrs = [a for a in atrs if a[0] is not '_']

    for atr in atrs:
      if type(inspect.getattr_static(self, atr)) != types.FunctionType:
        cString+=atr+': '+str(self.__getattribute__(atr))+'\r\n'
    return cString
