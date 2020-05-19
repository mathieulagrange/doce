import os
import inspect
import types
import re
import hashlib
import numpy as np

class Metrics():
    units = types.SimpleNamespace()
    pass

    def reduceFromVar(self, settings, data):
        table = []
        for sIndex, setting in enumerate(settings):
            row = []
            for factorName in settings.getFactorNames():
                row.append(setting.__getattribute__(factorName))
            for mIndex, metric in enumerate(self.getMetricsNames()):
                for aggregationType in self.__getattribute__(metric):
                    if aggregationType:
                        value = getattr(np, aggregationType)(data[sIndex, mIndex, :])
                    else:
                        value = data[sIndex, mIndex]
                    row.append(value)
            table.append(row)
        return table

    def reduceFromNpy(self, settings, dataPath, naming = 'long'):
        table = []
        for sIndex, setting in enumerate(settings):
            row = []
            for mIndex, metric in enumerate(self.getMetricsNames()):
                fileName = dataPath+setting.getId(naming)+'_'+metric+'.npy'
                if os.path.exists(fileName):
                    for aggregationType in self.__getattribute__(metric):
                        data = np.load(fileName)
                        if aggregationType:
                            value = getattr(np, aggregationType)(data)
                        else:
                            value = float(data)
                        row.append(value)
            if len(row):
                for factorName in reversed(settings.getFactorNames()):
                    row.insert(0, setting.__getattribute__(factorName))
                table.append(row)
        return table

    def reduceFromH5(self, settings, data, naming = 'long'):
        return table

    def reduce(self, settings, data, aggregationStyle = 'capitalize', naming = 'long'):
        columns = self.getHeader(settings, aggregationStyle)
        if isinstance(data, str):
            if data.endswith('.h5'):
                table = self.reduceFromH5(settings, data)
            else:
                table = self.reduceFromNpy(settings, data, naming)
        else:
            # check consistency between settings and data
            if (len(settings) != data.shape[0]):
                raise ValueError('the first dimensions of data must be equal to the length of settings')

            table = self.reduceFromVar(settings, data);
        return (table, columns)

    def getHeader(self, settings, aggregationStyle):
        columns = []
        for factorName in settings[0].getFactorNames():
            columns.append(factorName)
        for metric in self.getMetricsNames():
            for aggregationType in self.__getattribute__(metric):
                if aggregationStyle is 'capitalize':
                    name = metric+aggregationType.capitalize()
                else :
                    name = metric+'_'+aggregationType
                columns.append(name)
        return columns

    def getMetricsNames(self):
      return [s for s in self.__dict__.keys() if s[0] is not '_']

    def __len__(self):
        return len([s for s in self.__dict__.keys() if s[0] is not '_'])

class Factors():
  pass

  # def __setattr__(self, name, value):
  #   return object.__setattr__(self, name, value)
  def __getattribute__(self, name):
    value = object.__getattribute__(self, name)
    # print(name)
    # print(type(inspect.getattr_static(self, name)))
    if name[0] != '_' and hasattr(self, '_setting') and type(inspect.getattr_static(self, name)) != types.FunctionType:
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
    self._settings = self.getSettings(self._mask)
    # print('all settings')
    # print(self._settings)
   # self._settings = self._mask]
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
      self._settings = self.getSettings(self._mask)
      self._setting = self._settings[index]
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
    # print('mask')
    # print(mask)
    self._mask = mask
    # print(nbFactors)
    return self

  def __len__(self):
      self._settings = self.getSettings(self._mask)
      return len(self._settings)

  def getSettings(self, mask=None):
    settings = []
    for m in mask:
      # handle -1 in mask
      for mfi, mf in enumerate(m):
        if isinstance(mf, int) and mf == -1:
          attr = self.__getattribute__(list(self.__dict__.keys())[mfi])
          # print(type(attr))
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
    # print(settings)
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
