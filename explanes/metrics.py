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
        for factorName in settings.getFactorNames():
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
