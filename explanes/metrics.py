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
                            sgm = sg._f_get_child(metric)
                            if aggregationType:
                                value = getattr(np, aggregationType)(sgm)
                            else:
                                value = sgm[0]
                        row.append(value)
                if len(row):
                    for factorName in reversed(settings.getFactorNames()):
                        row.insert(0, setting.__getattribute__(factorName))
                table.append(row)
        h5.close()
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
                raise ValueError('The first dimensions of data must be equal to the length of settings. got %i and %i respectively' % (data.shape[0], len(settings)))

            table = self.reduceFromVar(settings, data);

        header = ''
        same = [True] * len(table[0])
        sameValue = [None] * len(table[0])
        for r in table:
            for cIndex, c in enumerate(r):
                if sameValue[cIndex] is None:
                    sameValue[cIndex] = c
                elif sameValue[cIndex] != c:
                    same[cIndex] = False

        for sIndex, s in enumerate(same):
            if s:
                header += columns[sIndex]+': '+str(sameValue[sIndex])
                columns.pop(sIndex)
                for r in table:
                    r.pop(sIndex)
        return (table, columns, header)

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
                    name = metric+aggregationType.capitalize()
                else :
                    name = metric+'_'+aggregationType
                columns.append(name)
        return columns

    def getMetricsNames(self):
      return [s for s in self.__dict__.keys() if s[0] is not '_']

    def __len__(self):
        return len(self.getMetricsNames())
