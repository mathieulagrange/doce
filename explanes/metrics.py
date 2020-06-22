import os
import inspect
import types
import re
import hashlib
import numpy as np
import tables as tb

class Metrics():
    _unit = types.SimpleNamespace()
    _description = types.SimpleNamespace()
    _metrics = []

    def __setattr__(self, name, value):
      if not hasattr(self, name) and name[0] is not '_':
        self._metrics.append(name)
      return object.__setattr__(self, name, value)

    def reduceFromVar(self, settings, data):
        table = []
        for sIndex, setting in enumerate(settings):
            row = []
            for factorName in settings.getFactorNames():
                row.append(setting.__getattribute__(factorName))
            for mIndex, metric in enumerate(self.getMetricsNames()):
                for aggregationType in self.__getattribute__(metric):
                    # if aggregationType:
                    #     value = getattr(np, aggregationType)()
                    # else:
                    #     value = data[sIndex, mIndex]
                    row.append(self.getValue(aggregationType, data[sIndex, mIndex, :]))
            table.append(row)
        return table

    def reduceFromNpy(self, settings, dataPath, naming = 'long'):
        table = []
        for sIndex, setting in enumerate(settings):
            row = []
            for mIndex, metric in enumerate(self.getMetricsNames()):
                fileName = dataPath+setting.getId(naming)+'_'+metric+'.npy'
                if os.path.exists(fileName):
                    data = np.load(fileName)
                    for aggregationType in self.__getattribute__(metric):
                        row.append(self.getValue(aggregationType, data))
            if len(row):
                for factorName in reversed(settings.getFactorNames()):
                    row.insert(0, setting.__getattribute__(factorName))
                table.append(row)
        return table

    def reduceFromH5(self, settings, dataPath):
        table = []
        h5 = tb.open_file(dataPath, mode='r')
        for sIndex, setting in enumerate(settings):
            row = []
            if h5.root.__contains__(setting.getId(type='shortCapital')):
                sg = h5.root._f_get_child(setting.getId(type='shortCapital'))

                for mIndex, metric in enumerate(self.getMetricsNames()):
                    for aggregationType in self.__getattribute__(metric):
                        value = np.nan
                        if sg.__contains__(metric):
                            data = sg._f_get_child(metric)
                            # if aggregationType:
                            #     value = getattr(np, aggregationType)(sgm)
                            # else:
                            #     value = sgm[0]
                        row.append(self.getValue(aggregationType, data))
                if len(row):
                    for factorName in reversed(settings.getFactorNames()):
                        row.insert(0, setting.__getattribute__(factorName))
                table.append(row)
        h5.close()
        return table

    def getValue(self, aggregationType, data):
      # print(aggregationType)
      # print(data)
      if aggregationType:
        if isinstance(aggregationType, int):
          if data.size>1:
            value = float(data[aggregationType])
          else:
            value = float(data)
        elif isinstance(aggregationType, str):
          value = getattr(np, aggregationType)(data)
      else:
          # print(data)
          # print(data.size)
          # print(type(data))
          if data.size>1:
            value = float(data[0])
          else:
            value = float(data)
      return value

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
                raise ValueError('The first dimensions of data must be equal to the length of settings. got %i and %i respectively' % (data.shape[0], len(settings)))

            table = self.reduceFromVar(settings, data);

        header = ''
        if len(table)>1:
            same = [True] * len(table[0])
            sameValue = [None] * len(table[0])

            for r in table:
                for cIndex, c in enumerate(r):
                    if sameValue[cIndex] is None:
                        sameValue[cIndex] = c
                    elif sameValue[cIndex] != c:
                        same[cIndex] = False

            sameIndex = [i for i, x in enumerate(same) if x] #  and i<len(settings.getFactorNames())
            for s in sameIndex:
                header += columns[s]+': '+str(sameValue[s])+' '
            # print(sameIndex)
            # print(columns)
            for s in sorted(sameIndex, reverse=True):
                    columns.pop(s)
                    # same.pop(sIndex)
                    for r in table:
                        r.pop(s)
        return (table, columns, header)

    def get(self, metric, settings, data, aggregationStyle = 'capitalize', naming = 'long'):
      if isinstance(data, str):
        if data.endswith('.h5'):
          (array, description) = self.getFromH5(metric, settings, data) # todo
        else:
          (array, description) = self.getFromNpy(metric, settings, data, naming)
      else:
        # check consistency between settings and data
        if (len(settings) != data.shape[0]):
          raise ValueError('The first dimensions of data must be equal to the length of settings. got %i and %i respectively' % (data.shape[0], len(settings)))

        (array, description) = self.getFromVar(metric, settings, data); # todo
      return (array, description)

    def getFromNpy(self, metric, settings, dataPath, naming = 'long'):
      table = []
      nbSettings = 0
      firstTry = True
      for sIndex, setting in enumerate(settings):
        fileName = dataPath+setting.getId(naming)+'_'+metric+'.npy'
        if os.path.exists(fileName):
          nbSettings+=1
          if firstTry:
            firstTry = False
            data = np.load(fileName)
            nbValues = data.shape[0]
      data = [] #np.zeros((nbSettings, nbValues))
      description = []
      sIndex = 0
      for setting in settings:
        fileName = dataPath+setting.getId(naming)+'_'+metric+'.npy'
        if os.path.exists(fileName):
          #data[sIndex, :] = np.load(fileName)
          data.append(np.load(fileName))
          description.append(setting.getId())
          sIndex += 1

      return (data, description)

    def h5addSetting(self, h5, setting, metricDimensions=[]):
        if not h5.__contains__('/'+setting.getId(type='shortCapital')):
            sg = h5.create_group('/', setting.getId(type='shortCapital'), setting.getId(type='long', sep=' '))
        else:
            sg = h5.root._f_get_child(setting.getId(type='shortCapital'))
        for mIndex, metric in enumerate(self.getMetricsNames()):
            if not metricDimensions:
                if sg.__contains__(metric):
                    sg._f_get_child(metric)._f_remove()
                h5.create_earray(sg, metric, tb.Float64Atom(), (0,), getattr(self._description, metric))
            else:
                if not sg.__contains__(metric):
                    h5.create_array(sg, metric, np.zeros(( metricDimensions[mIndex])), getattr(self._description, metric))
        return sg

    def getHeader(self, settings, aggregationStyle):
        columns = []
        for factorName in settings.getFactorNames():
            columns.append(factorName)
        for metric in self.getMetricsNames():
            for aggregationType in self.__getattribute__(metric):
                if aggregationStyle is 'capitalize':
                    name = metric+str(aggregationType).capitalize()
                else :
                    name = metric+'_'+aggregationType
                columns.append(name)
        return columns

    def getMetricsNames(self):
      return self._metrics
      # return [s for s in self.__dict__.keys() if s[0] is not '_']

    def __len__(self):
        return len(self.getMetricsNames())
