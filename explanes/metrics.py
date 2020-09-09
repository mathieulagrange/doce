import os
import inspect
import types
import re
import hashlib
import numpy as np
import tables as tb
import explanes.utils as expUtils
import copy

class Metrics():
    _unit = types.SimpleNamespace()
    _description = types.SimpleNamespace()
    _metrics = []

    def __setattr__(self, name, value):
      if not hasattr(self, name) and name[0] is not '_':
        self._metrics.append(name)
      return object.__setattr__(self, name, value)

    def reduceFromNpy(self, settings, dataPath, **kwargs):
        table = []
        metricHasData = np.zeros((len(self.getMetricsNames())))
        for sIndex, setting in enumerate(settings):
            row = []
            for mIndex, metric in enumerate(self.getMetricsNames()):
                fileName = dataPath+setting.getId(**kwargs)+'_'+metric+'.npy'
                if os.path.exists(fileName):
                    metricHasData[mIndex] = 1
                    data = np.load(fileName)
                    for aggregationType in self.__getattribute__(metric):
                        row.append(self.getValue(aggregationType, data))
            if len(row):
                for factorName in reversed(settings.getFactorNames()):
                    row.insert(0, setting.__getattribute__(factorName))
                table.append(row)
        return (table, metricHasData)

    def reduceFromH5(self, settings, dataPath, **kwargs):
        table = []
        h5 = tb.open_file(dataPath, mode='r')
        metricHasData = np.zeros((len(self.getMetricsNames())))
        for sIndex, setting in enumerate(settings):
            row = []
            if h5.root.__contains__(setting.getId(**kwargs)):
                sg = h5.root._f_get_child(setting.getId(**kwargs))
                for mIndex, metric in enumerate(self.getMetricsNames()):
                    for aggregationType in self.__getattribute__(metric):
                        value = np.nan
                        if sg.__contains__(metric):
                            metricHasData[mIndex] = 1
                            data = sg._f_get_child(metric)
                        row.append(self.getValue(aggregationType, data))
                if len(row):
                    for factorName in reversed(settings.getFactorNames()):
                        row.insert(0, setting.__getattribute__(factorName))
                table.append(row)
        h5.close()
        return (table, metricHasData)

    def getValue(self, aggregationType, data):
      indexPercent=-1
      if aggregationType:
        if isinstance(aggregationType, int):
          if data.size>1:
            value = float(data[aggregationType])
          else:
            value = float(data)
        elif isinstance(aggregationType, str):
          indexPercent = aggregationType.find('%')
          if indexPercent>-1:
            aggregationType = aggregationType.replace('%', '')
          ags = aggregationType.split('-')
          aggregationType = ags[0]
          if len(ags)>1:
            ignore = int(ags[1])
            if ignore == 0:
              value = getattr(np, aggregationType)(data[1:])
            elif ignore == 1:
              value = getattr(np, aggregationType)(data[::2])
          else :
            value = getattr(np, aggregationType)(data)
      else:
          data = np.array(data)
          if data.size>1:
            value = float(data[0])
          else:
            value = float(data)
      if indexPercent>-1:
        value *= 100
      return value

    def reduce(self, settings, data, aggregationStyle = 'capitalize', factorDisplayStyle='long', **kwargs):

        if isinstance(data, str):
            if data.endswith('.h5'):
                (table, metricHasData) = self.reduceFromH5(settings, data)
            else:
                (table, metricHasData) = self.reduceFromNpy(settings, data, **kwargs)

        columns = self.getColumns(settings, metricHasData, aggregationStyle, factorDisplayStyle)
        header = ''
        if len(table)>1:
            (same, sameValue) = expUtils.sameColumnsInTable(table)

            sameIndex = [i for i, x in enumerate(same) if x and i<len(settings.getFactorNames())]
            for s in sameIndex:
                header += expUtils.compressName(columns[s], factorDisplayStyle)+': '+str(sameValue[s])+' '
            # print(sameIndex)
            # print(columns)
            for s in sorted(sameIndex, reverse=True):
                    columns.pop(s)
                    # same.pop(sIndex)
                    for r in table:
                        r.pop(s)
        return (table, columns, header)

    def get(self, metric, settings, data, aggregationStyle = 'capitalize', **kwargs):
      if isinstance(data, str):
        if data.endswith('.h5'):
          (array, description) = self.getFromH5(metric, settings, data) # todo
        else:
          (array, description) = self.getFromNpy(metric, settings, data, **kwargs)

      header = ''
      if description:
        (same, sameValue) = expUtils.sameColumnsInTable(description)
        for si, s in enumerate(same):
          if si>1 and not s:
            same[si-1] = False
        sameIndex = [i for i, x in enumerate(same) if x]
        #print(sameIndex)
        for s in sameIndex:
            header += description[0][s]+' '
        # print(sameIndex)
        # print(columns)
        for s in sorted(sameIndex, reverse=True):
                for r in description:
                    r.pop(s)
      return (array, description, header)

    def getFromH5(self, metric, settings, dataPath, **kwargs):
      h5 = tb.open_file(dataPath, mode='r')
      data = []
      description = []
      descriptionFormat = copy.deepcopy(kwargs)
      descriptionFormat['format'] = 'list'
      descriptionFormat['noneAndZero2void'] = False
      descriptionFormat['default2void'] = False
      for setting in settings:
        if h5.root.__contains__(setting.getId(**kwargs)):
            sg = h5.root._f_get_child(setting.getId(**kwargs))
            if sg.__contains__(metric):
                data.append(sg._f_get_child(metric))
                description.append(setting.getId(**descriptionFormat))
      h5.close()
      return (data, description)

    def getFromNpy(self, metric, settings, dataPath, **kwargs):
      data = []
      description = []
      descriptionFormat = copy.deepcopy(kwargs)
      descriptionFormat['format'] = 'list'
      descriptionFormat['noneAndZero2void'] = False
      descriptionFormat['default2void'] = False
      for setting in settings:
        fileName = dataPath+setting.getId(**kwargs)+'_'+metric+'.npy'
        if os.path.exists(fileName):
          data.append(np.load(fileName))
          description.append(setting.getId(**descriptionFormat))

      return (data, description)

    def h5addSetting(self, h5, setting, metricDimensions=[], **kwargs):
        groupName = setting.getId(**kwargs)
        if not h5.__contains__('/'+groupName):
            sg = h5.create_group('/', groupName, setting.getId(format='long', sep=' '))
        else:
            sg = h5.root._f_get_child(groupName)
        for mIndex, metric in enumerate(self.getMetricsNames()):
            if not metricDimensions:
                if sg.__contains__(metric):
                    sg._f_get_child(metric)._f_remove()
                h5.create_earray(sg, metric, tb.Float64Atom(), (0,), getattr(self._description, metric))
            else:
                if not sg.__contains__(metric):
                    h5.create_array(sg, metric, np.zeros(( metricDimensions[mIndex])), getattr(self._description, metric))
        return sg

    def getColumns(self, settings, metricHasData, aggregationStyle, factorDisplayStyle):
        columns = []
        for factorName in settings.getFactorNames():
            columns.append(expUtils.compressName(factorName, factorDisplayStyle))
        for mIndex, metric in enumerate(self.getMetricsNames()):
            if metricHasData[mIndex]:
              for aggregationType in self.__getattribute__(metric):
                  if aggregationStyle is 'capitalize':
                      name = metric+str(aggregationType).capitalize()
                  else :
                      name = metric+'_'+aggregationType
                  columns.append(name)
        return columns

    def getMetricsNames(self):
      return self._metrics

    def __len__(self):
        return len(self.getMetricsNames())

    def __str__(self):
      cString = ''
      atrs = dict(vars(type(self)))
      atrs.update(vars(self))
      atrs = [a for a in atrs if a[0] is not '_']

      for atr in atrs:
        if type(inspect.getattr_static(self, atr)) != types.FunctionType:
          cString+='  '+atr+': '+str(self.__getattribute__(atr))+'\r\n'
      return cString
