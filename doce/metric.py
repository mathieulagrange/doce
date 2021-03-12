import os
import inspect
import types
import numpy as np
import tables as tb
import doce.util as eu
import copy
from itertools import compress
import time

class Metric():
  """Stores information about the way evaluation metrics are stored and manipulated.

  Stores information about the way evaluation metrics are stored and manipulated. Each member of this class describes an evaluation metric and the way it may be abstracted. Two NameSpaces (doce.metric.Metric._unit, doce.metric.Metric._description) are available to respectively provide information about the unit of the metric and its semantic.

  Each metric may be reduced by any mathematical operation that operate on a vector made available by the numpy library with default parameters.

  Two pruning strategies can be complemented to this description in order to remove some items of the metric vector before being abstracted.

  One can select one value of the vector by providing its index.

  Examples
  --------

  >>> import doce
  >>> m = doce.metric.Metric()
  >>> m.duration = ['mean', 'std']
  >>> m._unit.duration = 'second'
  >>> m._description = 'duration of the processing'

  It is sometimes useful to store complementary data useful for plotting that must not be considered during the reduction.

  >>> m.metric1 = ['median-0', 'min-0', 'max-0']

  In this case, the first value will be removed before reduction.

  >>> m.metric2 = ['median-2', 'min-2', 'max-2', '0%']

  In this case, the odd values will be removed before reduction and the last reduction will select the first value of the metric vector, expressed in percents by multiplying it by 100.
  """
  def __init__(self):
    self._unit = types.SimpleNamespace()
    self._description = types.SimpleNamespace()
    self._metrics = []

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
    dataLocation,
    settingEncoding={},
    verbose = False,
    reductionDirectiveModule = None
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering numpy storage. For each metric, a .npy file is assumed to be available which the following naming convention: <id_of_setting>_<metricName>.npy.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """
    table = []
    metricHasData = [False] * len(self.name())
    nbReducedMetrics = 0
    for mIndex, metric in enumerate(self.name()):
      for reductionType in self.__getattribute__(metric):
        nbReducedMetrics += 1
    reducedMetrics = [False] * nbReducedMetrics
    for sIndex, setting in enumerate(settings):
      row = []
      idx = 0
      for mIndex, metric in enumerate(self.name()):
        fileName = dataLocation+setting.id(**settingEncoding)+'_'+metric+'.npy'
        if os.path.exists(fileName):
          if verbose:
            print('Found '+fileName+', last modified '+time.ctime(os.path.getmtime(fileName)))
          metricHasData[mIndex] = True
          data = np.load(fileName)
          for reductionType in self.__getattribute__(metric):
            reducedMetrics[idx] = True
            idx+=1
            row.append(self.reduceMetric(data, reductionType, reductionDirectiveModule))
        else:
          if verbose:
            print('** Unable to find '+fileName)
          for reductionType in self.__getattribute__(metric):
            row.append(np.nan)
            idx+=1
      if len(row) and not all(np.isnan(c) for c in row):
        for factorName in reversed(settings.factors()):
          row.insert(0, setting.__getattribute__(factorName))
        table.append(row)
    nbFactors = len(settings.factors())
    for ir, row in enumerate(table):
      table[ir] = row[:nbFactors]+list(compress(row[nbFactors:], reducedMetrics))
    return (table, metricHasData)

  def reduceFromH5(
    self,
    settings,
    dataLocation,
    settingEncoding={},
    verbose = False
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering h5 storage.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """
    table = []
    h5 = tb.open_file(dataLocation, mode='r')
    metricHasData = [False] * len(self.name())
    for sIndex, setting in enumerate(settings):
      row = []
      if verbose:
        print('Seeking Group '+setting.id(**settingEncoding))
      if h5.root.__contains__(setting.id(**settingEncoding)):
        settingGroup = h5.root._f_get_child(setting.id(**settingEncoding))
        # print(settingGroup._v_name)
        # print(setting.id(**settingEncoding))
        for mIndex, metric in enumerate(self.name()):
          for reductionType in self.__getattribute__(metric):
            value = np.nan
            if settingGroup.__contains__(metric):
              metricHasData[mIndex] = True
              data = settingGroup._f_get_child(metric)
            row.append(self.reduceMetric(data, reductionType, reductionDirectiveModule))
        if len(row) and not all(np.isnan(c) for c in row):
          for factorName in reversed(settings.factors()):
            row.insert(0, setting.__getattribute__(factorName))
        table.append(row)
    h5.close()
    return (table, metricHasData)

  def reduceMetric(
    self,
    data,
    reductionType,
    reductionDirectiveModule=None
    ):
    """Apply reduction directive to a metric vector after potentially remove non wanted items from the vector.

    The data vector is reduced by considering the reduction directive after potentially remove non wanted items from the vector.

    Parameters
    ----------

    data : numpy array
      1-D vector to be reduced.

    reductionType : str
      type of reduction to be applied to the data vector. Can be any method supplied by the reductionDirectiveModule. If unavailable, a numpy method with this name that can applied to a vector and returns a value is searched for. Selectors and layout can also be specified.

    reductionDirectiveModule : str (optional)
      Python module to perform the reduction. If None, numpy is considered.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> data = np.linspace(1, 10, num=10)
    >>> print(data)
    [ 1.  2.  3.  4.  5.  6.  7.  8.  9. 10.]
    >>> m  =doce.metric.Metric()
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

    if reductionDirectiveModule == 'None':
      reductionDirectiveModule = np
    reductionTypeDirective = reductionType
    indexPercent = -1
    if isinstance(reductionType, str):
      reductionTypeDirective = reductionType.replace('%', '').split('-')[0]
      indexPercent = reductionType.find('%')
      # print(reductionTypeDirective)

    if isinstance(reductionTypeDirective, int) or not reductionDirectiveModule or not hasattr(reductionDirectiveModule, reductionTypeDirective):
      reductionDirectiveModule = np
      data = data.flatten()

    if reductionTypeDirective and isinstance(reductionType, str) and not hasattr(reductionDirectiveModule, reductionTypeDirective):
      return np.nan

    # indexPercent=-1
    if reductionTypeDirective:
      if isinstance(reductionTypeDirective, int):
        if data.size>1:
          value = float(data[reductionTypeDirective])
        else:
          value = float(data)
      elif isinstance(reductionTypeDirective, str):
        ags = reductionTypeDirective.split('-')
        if len(ags)>1:
          ignore = int(ags[1])
          if ignore == 0:
            value = getattr(reductionDirectiveModule, reductionTypeDirective)(data[1:])
          elif ignore == 1:
            value = getattr(reductionDirectiveModule, reductionTypeDirective)(data[::2])
          elif ignore == 2:
            value = getattr(reductionDirectiveModule, reductionTypeDirective)(data[1::2])
          else:
            print('Unrecognized pruning directive')
            raise ValueError
        else :
          value = getattr(reductionDirectiveModule, reductionTypeDirective)(data)
    else:
      if not isinstance(data, np.ndarray):
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
    dataLocation,
    settingEncoding={},
    factorDisplay='long',
    factorDisplayLength=2,
    metricDisplay='long',
    metricDisplayLength=2,
    reducedMetricDisplay = 'capitalize',
    verbose = False,
    reductionDirectiveModule=None,
    expandFactor=None,
    metricSelector=None
    ):
    """Apply the reduction directives described in each members of doce.metric.Metric objects for the settings given as parameters.

    For each setting in the iterable settings, available data corresponding to the metrics specified as members of the doce.metric.Metric object are reduced using specified reduction methods.

    Parameters
    ----------

    settings: doce.factor.Factor
      iterable settings.

    dataLocation: str
      In the case of .npy storage, a valid path to the main directory. In the case of .h5 storage, a valid path to an .h5 file.

    settingEncoding : dict
      Encoding of the setting. See doce.factor.Factor.id for references.

    reducedMetricDisplay : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric is done in a Camel case fashion: metricReduction.

      If set to 'underscore', the description of the reduced metric is done in a Python case fashion: metric_reduction.

    factor : doce.factor.Factor
      The doce.factor.Factor describing the factors of the experiment.

    factorDisplay : str (optional)
      The expected format of the display of factors. 'long' (default) do not lead to any reduction. If factorDisplay contains 'short', a reduction of each word is performed. 'shortUnderscore' assumes pythonCase delimitation. 'shortCapital' assumes camelCase delimitation. 'short' attempts to perform reduction by guessing the type of delimitation.

    factorDisplayLength : int (optional)
      If factorDisplay has 'short', factorDisplayLength specifies the maximal length of each word of the description of the factor.

    verbose : bool
      In the case of .npy metric storage, if verbose is set to True, print the fileName seeked for each metric as well as its time of last modification.

      In the case of .h5 metric storage, if verbose is set to True, print the group seeked for each metric.

    Returns
    -------

    settingDescription : list of lists of literals
      A settingDescription, stored as a list of list of literals of the same size. The main list stores the rows of the settingDescription.

    columnHeader : list of str
      The column header of the settingDescription as a list of str, describing the factors (left side), and the reduced metrics (right side).

    constantSettingDescription : str
      When a factor is equally valued for all the settings, the factor column is removed from the settingDescription and stored in constantSettingDescription along its value.

    nbColumnFactor : int
      The number of factors in the column header.

    Examples
    --------

    explanes supports metrics storage using an .npy file per metric per setting.

    >>> import doce
    >>> import numpy as np
    >>> import pandas as pd
    >>> np.random.seed(0)

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.project.name = 'example'
    >>> experiment.path.output = '/tmp/'+experiment.project.name+'/'
    >>> experiment.factor.f1 = [1, 2]
    >>> experiment.factor.f2 = [1, 2, 3]
    >>> experiment.metric.m1 = ['mean', 'std']
    >>> experiment.metric.m2 = ['min', 'argmin']
    >>> def process(setting, experiment):
    ...   metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...   metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...   np.save(experiment.path.output+setting.id()+'_m1.npy', metric1)
    ...   np.save(experiment.path.output+setting.id()+'_m2.npy', metric2)
    >>> experiment.setPath()
    >>> nbFailed = experiment.do([], process, progress=False)
    >>> (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = experiment.metric.reduce(experiment.factor.mask([1]), experiment.path.output)

    >>> df = pd.DataFrame(settingDescription, columns=columnHeader)
    >>> df[columnHeader[nbColumnFactor:]] = df[columnHeader[nbColumnFactor:]].round(decimals=2)
    >>> print(constantSettingDescription)
    f1: 2
    >>> print(df)
       f2  m1Mean  m1Std  m2Min  m2Argmin
    0   1    2.87   1.00  -4.49        35
    1   2    3.97   0.93  -8.19        13
    2   3    5.00   0.91 -12.07        98

    explanes also supports metrics storage using one .h5 file sink structured with settings as groups et metrics as leaf nodes.

    >>> import doce
    >>> import numpy as np
    >>> import tables as tb
    >>> import pandas as pd
    >>> np.random.seed(0)

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.project.name = 'example'
    >>> experiment.path.output = '/tmp/'+experiment.project.name+'.h5'
    >>> experiment.factor.f1 = [1, 2]
    >>> experiment.factor.f2 = [1, 2, 3]
    >>> experiment.metric.m1 = ['mean', 'std']
    >>> experiment.metric.m2 = ['min', 'argmin']
    >>> def process(setting, experiment):
    ...   h5 = tb.open_file(experiment.path.output, mode='a')
    ...   settingGroup = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'m1':100, 'm2':100})
    ...   settingGroup.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...   settingGroup.m2[:] = setting.f1*setting.f2*np.random.randn(100)
    ...   h5.close()
    >>> experiment.setPath()
    >>> nbFailed = experiment.do([], process, progress=False)
    >>> h5 = tb.open_file(experiment.path.output, mode='r')
    >>> print(h5)
    /tmp/example.h5 (File) ''
    Last modif.: '...'
    Object Tree:
    / (RootGroup) ''
    /f1_1_f2_1 (Group) 'f1 1 f2 1'
    /f1_1_f2_1/m1 (Array(100,)) 'm1'
    /f1_1_f2_1/m2 (EArray(100,)) 'm2'
    /f1_1_f2_2 (Group) 'f1 1 f2 2'
    /f1_1_f2_2/m1 (Array(100,)) 'm1'
    /f1_1_f2_2/m2 (EArray(100,)) 'm2'
    /f1_1_f2_3 (Group) 'f1 1 f2 3'
    /f1_1_f2_3/m1 (Array(100,)) 'm1'
    /f1_1_f2_3/m2 (EArray(100,)) 'm2'
    /f1_2_f2_1 (Group) 'f1 2 f2 1'
    /f1_2_f2_1/m1 (Array(100,)) 'm1'
    /f1_2_f2_1/m2 (EArray(100,)) 'm2'
    /f1_2_f2_2 (Group) 'f1 2 f2 2'
    /f1_2_f2_2/m1 (Array(100,)) 'm1'
    /f1_2_f2_2/m2 (EArray(100,)) 'm2'
    /f1_2_f2_3 (Group) 'f1 2 f2 3'
    /f1_2_f2_3/m1 (Array(100,)) 'm1'
    /f1_2_f2_3/m2 (EArray(100,)) 'm2'
    >>> h5.close()

    >>> (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = experiment.metric.reduce(experiment.factor.mask([0]), experiment.path.output)

    >>> df = pd.DataFrame(settingDescription, columns=columnHeader)
    >>> df[columnHeader[nbColumnFactor:]] = df[columnHeader[nbColumnFactor:]].round(decimals=2)
    >>> print(constantSettingDescription)
    f1: 1
    >>> print(df)
       f2  m1Mean  m1Std  m2Min  m2Argmin
    0   1    2.06   1.01  -2.22        83
    1   2    2.94   0.95  -5.32        34
    2   3    3.99   1.04  -9.14        89
    """


    if dataLocation.endswith('.h5'):
      (settingDescription, metricHasData) = self.reduceFromH5(settings, dataLocation, settingEncoding, verbose, reductionDirectiveModule)
    else:
      (settingDescription, metricHasData) = self.reduceFromNpy(settings, dataLocation, settingEncoding, verbose, reductionDirectiveModule)

    columnHeader = self.getColumnHeader(settings, factorDisplay, factorDisplayLength, metricDisplay, metricDisplayLength, metricHasData, reducedMetricDisplay)
    nbColumnFactor = len(settings.factors())

    (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = eu.pruneSettingDescription(settingDescription, columnHeader, nbColumnFactor, factorDisplay)

    return (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor)

  def get(
    self,
    metric,
    settings,
    dataLocation,
    settingEncoding={},
    verbose=False
    ):
    """ Get the metric vector from an .npy or a group of a .h5 file.

    Get the metric vector as a numpy array from an .npy or a group of a .h5 file.

    Parameters
    ----------

    metric: str
      The name of the metric. Must be a member of the doce.metric.Metric object.

    settings: doce.factor.Factor
      Iterable settings.

    dataLocation: str
      In the case of .npy storage, a valid path to the main directory. In the case of .h5 storage, a valid path to an .h5 file.

    settingEncoding : dict
      Encoding of the setting. See doce.factor.Factor.id for references.

    verbose : bool
      In the case of .npy metric storage, if verbose is set to True, print the fileName seeked for the metric.

      In the case of .h5 metric storage, if verbose is set to True, print the group seeked for the metric.

    Returns
    -------

    settingMetric: list of np.Array
      stores for each valid setting an np.Array with the values of the metric selected.

    settingDescription: list of list of str
      stores for each valid setting, a compact description of the modalities of each factors. The factors with the same modality accross all the set of settings is stored in constantSettingDescription.

    constantSettingDescription: str
      compact description of the factors with the same modality accross all the set of settings.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import pandas as pd

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.project.name = 'example'
    >>> experiment.path.output = '/tmp/'+experiment.project.name+'/'
    >>> experiment.factor.f1 = [1, 2]
    >>> experiment.factor.f2 = [1, 2, 3]
    >>> experiment.metric.m1 = ['mean', 'std']
    >>> experiment.metric.m2 = ['min', 'argmin']

    >>> def process(setting, experiment):
    ...  metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...  metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...  np.save(experiment.path.output+setting.id()+'_m1.npy', metric1)
    ...  np.save(experiment.path.output+setting.id()+'_m2.npy', metric2)
    >>> experiment.setPath()
    >>> nbFailed = experiment.do([], process, progress=False)

    >>> (settingMetric, settingDescription, constantSettingDescription) = experiment.metric.get('m1', experiment.factor.mask([1]), experiment.path.output)
    >>> print(constantSettingDescription)
    f1 2
    >>> print(settingDescription)
    [['f2', '1'], ['f2', '2'], ['f2', '3']]
    >>> print(len(settingMetric))
    3
    >>> print(settingMetric[0].shape)
    (100,)
    """

    settingMetric = []
    settingDescription = []
    settingDescriptionFormat = copy.deepcopy(settingEncoding)
    settingDescriptionFormat['format'] = 'list'
    settingDescriptionFormat['default'] = True

    if isinstance(dataLocation, str):
      if dataLocation.endswith('.h5'):
        h5 = tb.open_file(dataLocation, mode='r')
        for setting in settings:
          if h5.root.__contains__(setting.id(**settingEncoding)):
            if verbose:
              print('Found group '+setting.id(**settingEncoding))
            settingGroup = h5.root._f_get_child(setting.id(**settingEncoding))
            if settingGroup.__contains__(metric):
              settingMetric.append(np.array(settingGroup._f_get_child(metric)))
              settingDescription.append(setting.id(**settingDescriptionFormat))
          elif verbose:
            print('** Unable to find group '+setting.id(**settingEncoding))
        h5.close()
      else:
        for setting in settings:
          fileName = dataLocation+setting.id(**settingEncoding)+'_'+metric+'.npy'
          if os.path.exists(fileName):
            if verbose:
              print('Found '+fileName)
            settingMetric.append(np.load(fileName))
            settingDescription.append(setting.id(**settingDescriptionFormat))
          elif verbose:
            print('** Unable to find '+fileName)

    (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = eu.pruneSettingDescription(settingDescription)

    return (settingMetric, settingDescription, constantSettingDescription)

  def addSettingGroup(
    self,
    fileId,
    setting,
    metricDimension={},
    settingEncoding={}
    ):
    """adds a group to the root of a valid PyTables Object in order to store the metrics corresponding to the specified setting.

    adds a group to the root of a valid PyTables Object in order to store the metrics corresponding to the specified setting. The encoding of the setting is used to set the name of the group. For each metric, a Floating point Pytable Array is created. For any metric, ff no dimension is provided in the metricDimension dict, an expandable array is instantiated. If a dimension is available, a static size array is instantiated.

    Parameters
    ----------

    fileId: PyTables file Object
    a valid PyTables file Object, leading to an .h5 file opened with writing permission.

    setting: :class:`doce.factor.Factor`
    an instantiated Factor object describing a setting.

    metricDimension: dict
    for metrics for which the dimensionality of the storage vector is known, each key of the dict is a valid metric name and each conresponding value is the size of the storage vector.

    settingEncoding : dict
    Encoding of the setting. See doce.factor.Factor.id for references.

    Returns
    -------

    settingGroup: a Pytables Group
    a Pytables Group where to store metrics corresponding to the specified setting.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import tables as tb

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.project.name = 'example'
    >>> experiment.path.output = '/tmp/'+experiment.project.name+'.h5'
    >>> experiment.factor.f1 = [1, 2]
    >>> experiment.factor.f2 = [1, 2, 3]
    >>> experiment.metric.m1 = ['mean', 'std']
    >>> experiment.metric.m2 = ['min', 'argmin']

    >>> def process(setting, experiment):
    ...  h5 = tb.open_file(experiment.path.output, mode='a')
    ...  sg = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'m1':100})
    ...  sg.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...  sg.m2.append(setting.f1*setting.f2*np.random.randn(100))
    ...  h5.close()

    >>> experiment.setPath()
    >>> nbFailed = experiment.do([], process, progress=False)

    >>> h5 = tb.open_file(experiment.path.output, mode='r')
    >>> print(h5)
    /tmp/example.h5 (File) ''
    Last modif.: '...'
    Object Tree:
    / (RootGroup) ''
    /f1_1_f2_1 (Group) 'f1 1 f2 1'
    /f1_1_f2_1/m1 (Array(100,)) 'm1'
    /f1_1_f2_1/m2 (EArray(100,)) 'm2'
    /f1_1_f2_2 (Group) 'f1 1 f2 2'
    /f1_1_f2_2/m1 (Array(100,)) 'm1'
    /f1_1_f2_2/m2 (EArray(100,)) 'm2'
    /f1_1_f2_3 (Group) 'f1 1 f2 3'
    /f1_1_f2_3/m1 (Array(100,)) 'm1'
    /f1_1_f2_3/m2 (EArray(100,)) 'm2'
    /f1_2_f2_1 (Group) 'f1 2 f2 1'
    /f1_2_f2_1/m1 (Array(100,)) 'm1'
    /f1_2_f2_1/m2 (EArray(100,)) 'm2'
    /f1_2_f2_2 (Group) 'f1 2 f2 2'
    /f1_2_f2_2/m1 (Array(100,)) 'm1'
    /f1_2_f2_2/m2 (EArray(100,)) 'm2'
    /f1_2_f2_3 (Group) 'f1 2 f2 3'
    /f1_2_f2_3/m1 (Array(100,)) 'm1'
    /f1_2_f2_3/m2 (EArray(100,)) 'm2'

    >>> h5.close()
    """
    groupName = setting.id(**settingEncoding)
    # print(groupName)
    if not fileId.__contains__('/'+groupName):
      settingGroup = fileId.create_group('/', groupName, str(setting))
    else:
      settingGroup = fileId.root._f_get_child(groupName)
    for metric in self.name():
      if hasattr(self._description, metric):
        description = getattr(self._description, metric)
      else:
        description = metric

      if hasattr(self._unit, metric):
        description += ' in ' + getattr(self._unit, metric)

      if metric in metricDimension:
        if not settingGroup.__contains__(metric):
          fileId.create_array(settingGroup, metric, np.zeros((metricDimension[metric])), description)
      else:
        if settingGroup.__contains__(metric):
          settingGroup._f_get_child(metric)._f_remove()
        fileId.create_earray(settingGroup, metric, tb.Float64Atom(), (0,), description)

    return settingGroup

  def getColumnHeader(
    self,
    factor,
    factorDisplay='long',
    factorDisplayLength=2,
    metricDisplay='long',
    metricDisplayLength=2,
    metricHasData=[],
    reducedMetricDisplay = 'capitalize',
    ):
    """Builds the column header of the reduction settingDescription.

    This method builds the column header of the reduction settingDescription by formating the Factor names from the doce.factor.Factor class and by describing the reduced metrics.

    Parameters
    ----------

    factor : doce.factor.Factor
      The doce.factor.Factor describing the factors of the experiment.

    factorDisplay : str (optional)
      The expected format of the display of factors. 'long' (default) do not lead to any reduction. If factorDisplay contains 'short', a reduction of each word is performed. 'shortUnderscore' assumes pythonCase delimitation. 'shortCapital' assumes camelCase delimitation. 'short' attempts to perform reduction by guessing the type of delimitation.

    factorDisplayLength : int (optional)
      If factorDisplay has 'short', factorDisplayLength specifies the maximal length of each word of the description of the factor.

    metricHasData : list of bool
      Specify for each metric described in the doce.metric.Metric object, whether data has been loaded or not.

    reducedMetricDisplay : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric is done in a Camel case fashion: metricReduction.

      If set to 'underscore', the description of the reduced metric is done in a Python case fashion: metric_reduction.

    See Also
    --------

    doce.util.compressDescription
    """
    # print(factorDisplay)
    columnHeader = []
    for factorName in factor.factors():
      columnHeader.append(eu.compressDescription(factorName, factorDisplay, factorDisplayLength))
    for mIndex, metric in enumerate(self.name()):
      if metricHasData[mIndex]:
        for reductionType in self.__getattribute__(metric):
          if reducedMetricDisplay == 'capitalize':
            name = metric+str(reductionType).capitalize()
          elif reducedMetricDisplay == 'underscore':
            name = metric+'_'+reductionType
          else:
            print('Unrecognized reducedMetricDisplay value. Should be \'capitalize\' or \'underscore\'. Got:'+reducedMetricDisplay)
            raise ValueError
          columnHeader.append(eu.compressDescription(name, metricDisplay, metricDisplayLength))
    return columnHeader

  def name(
    self
    ):
    """Returns a list of str with the names of the metrics.

    Returns a list of str with the names of the metricsdefined as members of the doce.metric.Metric object.

    Examples
    --------

    >>> import doce
    >>> m = doce.metric.Metric()
    >>> m.duration = ['mean']
    >>> m.mse = ['mean']
    >>> m.name()
    ['duration', 'mse']
    """
    return self._metrics

  def __len__(
    self
    ):
    """Returns the number of metrics.

    Returns the number of metrics defined as members of the doce.metric.Metric object.

    Examples
    --------

    >>> import doce
    >>> m = doce.metric.Metric()
    >>> m.duration = ['mean']
    >>> m.mse = ['mean']
    >>> len(m)
    2
    """
    return len(self.name())

  def __str__(
    self
    ):
    """Returns a str describing the doce.metric.Metric.

    Returns a str describing the doce.metric.Metric by listing each member of the object.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> m = doce.metric.Metric()
    >>> m.duration = ['mean']
    >>> m._unit.duration = 'seconds'
    >>> m._description.duration = 'duration of the trial'
    >>> m.mse = ['mean']
    >>> m._unit.mse = ''
    >>> m._description.mse = 'Mean Square Error'
    >>> print(m)
    duration: ['mean'], the duration of the trial in seconds.
    mse: ['mean'], the Mean Square Error.
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
    return cString.rstrip()

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    # doctest.run_docstring_examples(Metric.addSettingGroup, globals(), optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
