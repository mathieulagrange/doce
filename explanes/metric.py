import os
import inspect
import types
import re
import hashlib
import numpy as np
import tables as tb
import explanes.util as eu
import copy

class Metric():
  """Stores information about the way evaluation metrics are stored and manipulated.

  Stores information about the way evaluation metrics are stored and manipulated. Each member of this class describes an evaluation metric and the way it may be abstracted. Two NameSpaces (explanes.metric.Metric._unit, explanes.metric.Metric._description) are available to respectively provide information about the unit of the metric and its semantic.

  Each metric may be reduced by any mathematical operation that operate on a vector made available by the numpy library with default parameters.

  Two pruning strategies can be complemented to this description in order to remove some items of the metric vector before being abstracted.

  One can select one value of the vector by providing its index.

  Examples
  --------

  >>> import explanes as el
  >>> m = el.metric.Metric()
  >>> m.duration = ['mean', 'std']
  >>> m._unit.duration = 'second'
  >>> m._description = 'duration of the processing'

  It is sometimes useful to store complementary data useful for plotting that must not be considered during the reduction.

  >>> m.metric1 = ['median-0', 'min-0', 'max-0']

  In this case, the first value will be removed before reduction.

  >>> m.metric2 = ['median-2', 'min-2', 'max-2', '0%']

  In this case, the odd values will be removed before reduction and the last reduction will select the first value of the metric vector which will be expressed in percents by multiplying the result by 100.
  """

  _unit = types.SimpleNamespace()
  _description = types.SimpleNamespace()
  _metrics = []

  def __setattr__(
    self,
    name,
    value
    ):
    if not hasattr(self, name) and name[0] != '_':
      self._metrics.append(name)
    return object.__setattr__(self, name, value)

  def reduceFromNpy(
    self,
    settings,
    dataPath,
    idFormat={}
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering numpy storage. For each metric, a .npy file is assumed to be available which the following naming convention: <id_of_setting>_<metricName>.npy.

    The method :meth:`explanes.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    explanes.metric.Metric.reduce

    """
    table = []
    metricHasData = np.zeros((len(self.getMetricNames())))
    for sIndex, setting in enumerate(settings):
      row = []
      for mIndex, metric in enumerate(self.getMetricNames()):
        fileName = dataPath+setting.getId(**idFormat)+'_'+metric+'.npy'
        if os.path.exists(fileName):
            metricHasData[mIndex] = 1
            data = np.load(fileName)
            for reductionType in self.__getattribute__(metric):
              row.append(self.reduceMetric(data, reductionType))
      if len(row):
        for factorName in reversed(settings.getFactorNames()):
          row.insert(0, setting.__getattribute__(factorName))
        table.append(row)
    return (table, metricHasData)

  def reduceFromH5(
    self,
    settings,
    dataPath,
    idFormat={}
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering h5 storage.

    The method :meth:`explanes.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    explanes.metric.Metric.reduce

    """
    table = []
    h5 = tb.open_file(dataPath, mode='r')
    metricHasData = np.zeros((len(self.getMetricNames())))
    for sIndex, setting in enumerate(settings):
      row = []
      if h5.root.__contains__(setting.getId(**idFormat)):
        sg = h5.root._f_get_child(setting.getId(**idFormat))
        # print(sg._v_name)
        # print(setting.getId(**idFormat))
        for mIndex, metric in enumerate(self.getMetricNames()):
          for reductionType in self.__getattribute__(metric):
            value = np.nan
            if sg.__contains__(metric):
              metricHasData[mIndex] = 1
              data = sg._f_get_child(metric)
            row.append(self.reduceMetric(data, reductionType))
        if len(row):
          for factorName in reversed(settings.getFactorNames()):
            row.insert(0, setting.__getattribute__(factorName))
        table.append(row)
    h5.close()
    return (table, metricHasData)

  def reduceMetric(
    self,
    data,
    reductionType
    ):
    """Apply reduction directive to a metric vector after potentially remove non wanted items from the vector.

    The data vector is reduced by considering the reduction directive after potentially remove non wanted items from the vector.

    Examples
    --------

    >>> import explanes as el
    >>> import numpy as np
    >>> data = np.linspace(1, 10, num=10)
    [ 1.  2.  3.  4.  5.  6.  7.  8.  9. 10.]
    >>> m  =el.metric.Metric()
    >>> m.reduceMetric(data, 0)
    1.0
    >>> m.reduceMetric(data, 8)
    9.0
    >>> m.reduceMetric(data, 'sum%')
    5500.0
    >>> m.reduceMetric(data, 'sum-0')
    54.0
    >>> m.reduceMetric(data, 'sum-1')
    25.0
    >>> m.reduceMetric(data, 'sum-2')
    30.0

    """
    indexPercent=-1
    if reductionType:
      if isinstance(reductionType, int):
        if data.size>1:
          value = float(data[reductionType])
        else:
          value = float(data)
      elif isinstance(reductionType, str):
        indexPercent = reductionType.find('%')
        if indexPercent>-1:
          reductionType = reductionType.replace('%', '')
        ags = reductionType.split('-')
        reductionType = ags[0]
        if len(ags)>1:
          ignore = int(ags[1])
          if ignore == 0:
            value = getattr(np, reductionType)(data[1:])
          elif ignore == 1:
            value = getattr(np, reductionType)(data[::2])
          elif ignore == 2:
            value = getattr(np, reductionType)(data[1::2])
          else:
            print('Unrecognized pruning directive')
            raise ValueError
        else :
          value = getattr(np, reductionType)(data)
    else:
      data = np.array(data)
      if data.size>1:
        value = float(data[0])
      else:
        value = float(data)
    if indexPercent>-1:
      value *= 100
    return value

  def reduce(
    self,
    settings,
    data,
    reducedMetricDisplay = 'capitalize',
    factorDisplay='long',
    idFormat={}
    ):
    """Apply the reduction directives described in each members of explanes.metric.Metric objects for the settings given as paramters.

    Desc

    Parameters
    ----------

    settings: explanes.factor.Factor

    data: str

    reducedMetricDisplay : str

    factorDisplay : str

    idFormat : dict

    Returns
    -------

    table : list of lists of literals

    columnHeader : list of str

    constantColumnDescription : str

    Examples
    --------

    """
    if isinstance(data, str):
      if data.endswith('.h5'):
        (table, metricHasData) = self.reduceFromH5(settings, data, idFormat)
      else:
        (table, metricHasData) = self.reduceFromNpy(settings, data, idFormat)

    columnHeader = self.getColumnHeader(settings, factorDisplay, metricHasData, reducedMetricDisplay)
    constantColumnDescription = ''
    if len(table)>1:
      (ccIndex, ccValue) = eu.constantColumn(table)

      ccIndex = [i for i, x in enumerate(ccIndex) if x and i<len(settings.getFactorNames())]
      for s in ccIndex:
        constantColumnDescription += eu.compressDescription(columnHeader[s], factorDisplay)+': '+str(ccValue[s])+' '
      for s in sorted(ccIndex, reverse=True):
        columnHeader.pop(s)
        for r in table:
          r.pop(s)
    return (table, columnHeader, constantColumnDescription)

  def get(
    self,
    metric,
    settings,
    data,
    reducedMetricDisplay = 'capitalize',
    idFormat={}
    ):
    """one liner

    Desc

    Examples
    --------

    """
    if isinstance(data, str):
      if data.endswith('.h5'):
        (array, description) = self.getFromH5(metric, settings, data) # todo
      else:
        (array, description) = self.getFromNpy(metric, settings, data, idFormat)

    constantColumnDescription = ''
    if description:
      (ccIndex, ccValue) = eu.constantColumn(description)
      for si, s in enumerate(ccIndex):
        if si>1 and not s:
          ccIndex[si-1] = False
      ccIndex = [i for i, x in enumerate(same) if x]
      for s in ccIndex:
        constantColumnDescription += description[0][s]+' '
      for s in sorted(ccIndex, reverse=True):
        for r in description:
          r.pop(s)
    return (array, description, constantColumnDescription)

  def getFromH5(
    self,
    metric,
    settings,
    dataPath,
    idFormat={}
    ):
    """one liner

    Desc

    Examples
    --------

    """
    h5 = tb.open_file(dataPath, mode='r')
    data = []
    description = []
    descriptionFormat = copy.deepcopy(kwargs)
    descriptionFormat['format'] = 'list'
    descriptionFormat['noneAndZero2void'] = False
    descriptionFormat['default2void'] = False
    for setting in settings:
      if h5.root.__contains__(setting.getId(idFormat)):
        sg = h5.root._f_get_child(setting.getId(idFormat))
        if sg.__contains__(metric):
          data.append(sg._f_get_child(metric))
          description.append(setting.getId(**descriptionFormat))
    h5.close()
    return (data, description)

  def getFromNpy(
    self,
    metric,
    settings,
    dataPath,
    idFormat={}
    ):
    """one liner

    Desc

    Examples
    --------

    """
    data = []
    description = []
    descriptionFormat = copy.deepcopy(idFormat)
    descriptionFormat['format'] = 'list'
    descriptionFormat['noneAndZero2void'] = False
    descriptionFormat['default2void'] = False
    for setting in settings:
      fileName = dataPath+setting.getId(idFormat)+'_'+metric+'.npy'
      if os.path.exists(fileName):
        data.append(np.load(fileName))
        description.append(setting.getId(**descriptionFormat))

    return (data, description)

  def h5addSetting(
    self,
    h5,
    setting,
    metricDimensions=[],
    idFormat={}
    ):
    """one liner

    Desc

    Examples
    --------

    """
    groupName = setting.getId(**idFormat)
    # print(groupName)
    if not h5.__contains__('/'+groupName):
      sg = h5.create_group('/', groupName, setting.getId(format='long', sep=' '))
    else:
      sg = h5.root._f_get_child(groupName)
    for mIndex, metric in enumerate(self.getMetricNames()):
      if hasattr(self._description, metric):
        description = getattr(self._description, metric)
      else:
        description = metric

      if hasattr(self._unit, metric):
        description += ' in ' + getattr(self._unit, metric)

      if not metricDimensions:
        if sg.__contains__(metric):
          sg._f_get_child(metric)._f_remove()
        h5.create_earray(sg, metric, tb.Float64Atom(), (0,), description)
      else:
        if not sg.__contains__(metric):
          h5.create_array(sg, metric, np.zeros(( metricDimensions[mIndex])), description)
    return sg

  def getColumnHeader(
    self,
    factor,
    factorDisplay='long',
    metricHasData=[],
    reducedMetricDisplay = 'capitalize',
    ):
    """Builds the column header of the reduction table.

    This method builds the column header of the reduction table by formating the Factor names from the explanes.factor.Factor class and by describing the reduced metrics.

    Parameters
    ----------

    factor : explanes.factor.Factor
    factorDisplay : str (optional)
    metricHasData : list
    reducedMetricDisplay : str (optional)

    Examples
    --------

    """
    columnHeader = []
    for factorName in settings.getFactorNames():
      columnHeader.append(eu.compressDescription(factorName, factorDisplay))
    for mIndex, metric in enumerate(self.getMetricNames()):
      if metricHasData[mIndex]:
        for reductionType in self.__getattribute__(metric):
          if reducedMetricDisplay == 'capitalize':
            name = metric+str(reductionType).capitalize()
          else :
            name = metric+'_'+reductionType
          columnHeader.append(name)
    return columnHeader

  def getMetricNames(
    self
    ):
    """Returns a list of str with the names of the metrics.

    Returns a list of str with the names of the metricsdefined as members of the explanes.metric.Metric object.

    Examples
    --------

    >>> import explanes as el
    >>> m = el.metric.Metric()
    >>> m.duration = ['mean']
    >>> m.mse = ['mean']
    >>> m.getMetricNames()
    ['duration', 'mse']
    """
    return self._metrics

  def __len__(
    self
    ):
    """Returns the number of metrics.

    Returns the number of metrics defined as members of the explanes.metric.Metric object.

    Examples
    --------

    >>> import explanes as el
    >>> m = el.metric.Metric()
    >>> m.duration = ['mean']
    >>> m.mse = ['mean']
    >>> len(m)
    2
    """
    return len(self.getMetricNames())

  def __str__(
    self
    ):
    """Returns a str describing the explanes.metric.Metric.

    Returns a str describing the explanes.metric.Metric by listing each member of the object.

    Examples
    --------

    >>> import explanes as el
    >>> import numpy as np
    >>> m = el.metric.Metric()
    >>> m.duration = ['mean']
    >>> m._unit.duration = 'seconds'
    >>> m._description.duration = 'duration of the trial'
    >>> m.mse = ['mean']
    >>> m._unit.mse = ''
    >>> m._description.mse = 'Mean Square Error'
    >>> print(m)

    """
    cString = ''
    atrs = dict(vars(type(self)))
    atrs.update(vars(self))
    atrs = [a for a in atrs if a[0] !=  '_']

    for atr in atrs:
      if type(inspect.getattr_static(self, atr)) != types.FunctionType:
        cString+='  '+atr+': '+str(self.__getattribute__(atr))
        if hasattr(self._description, atr):
          cString+=', the '+str(self._description.__getattribute__(atr))+''
        if hasattr(self._unit, atr) and self._unit.__getattribute__(atr):
          cString+=' in '+str(self._unit.__getattribute__(atr))
        cString += '.\r\n'
    return cString
