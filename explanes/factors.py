import os
import inspect
import types
import re
import hashlib
import numpy as np
import copy

class Factors():
  _setting = None

  def __setattr__(self, name, value):
      if name is '_mask':
        print('mod mask')
        print(value)
      return object.__setattr__(self, name, value)
  def __getattribute__(self, name):
    value = object.__getattribute__(self, name)
    # print(name)
    # print(type(inspect.getattr_static(self, name))) hasattr(self, '_setting')
    if name[0] != '_' and self._setting and type(inspect.getattr_static(self, name)) != types.FunctionType:
      idx = list(self.__dict__.keys()).index(name)
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
    print('iter mask: ')
    print(self._mask)
    self._settings = self.getSettings(self._mask)
    print('all settings: ')
    print(self._settings)
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
      print('get item')
      self._settings = self.getSettings(self._mask)
      self._setting = self._settings[index]
      print(self._mask)
      return  self

  def __call__(self, mask=None):
    nbFactors = len([s for s in self.__dict__.keys() if s[0] is not '_'])
    if mask is None or len(mask)==0 or (len(mask)==1 and len(mask)==0) :
       mask = [[-1]*nbFactors]
    if isinstance(mask, list) and not isinstance(mask[0], list):
        mask = [mask]


    for im, m in enumerate(mask):
      if len(m) < nbFactors:
        mask[im] = m+[-1]*(nbFactors-len(m))
      for il, l in enumerate(m):
          if not isinstance(l, list) and l > -1:
              mask[im][il] = [l]
    print('mask')
    print(mask)
    self._mask = mask
    # print(nbFactors)
    return self

  def __len__(self):
      self._settings = self.getSettings(self._mask)
      return len(self._settings)

  def getSettings(self, mask=None):
    settings = []
    mask = copy.deepcopy(mask)
    self._setting = None
    
    print('start get settings')
    print(self._mask)
    for m in mask:
      # handle -1 in mask
      for mfi, mf in enumerate(m):
        if isinstance(mf, int) and mf == -1:
          attr = self.__getattribute__(list(self.__dict__.keys())[mfi])
          # print(attr)
          # print(isinstance(attr, int))
          if isinstance(attr, list) or isinstance(attr, np.ndarray):
            m[mfi] = list(range(len(attr)))
          else:
            m[mfi] = 0

      # print('submask')
      s = self.getSettingsMask(m, 0)
      if all(isinstance(ss, list) for ss in s):
        for ss in s:
          settings.append(ss)
      else:
        settings.append(s)

    return settings

  def getSettingsMask(self, mask, done):
    # print(mask)
    if done == len(mask):
      return []

    s = self.getSettingsMask(mask, done+1)
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

  def getId(self, type='long', sep='_'):
    id = []
    for f in sorted(self.__dict__.keys()):
      # print(getattr(self, f))
      if f[0] != '_' and getattr(self, f) is not None:
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
