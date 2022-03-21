import os
import inspect
import types
import numpy as np
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
  def __init__(self, **metrics):
    self._unit = types.SimpleNamespace()
    self._description = types.SimpleNamespace()
    self._metrics = []

    for metric, reduction in metrics.items():
      self.__setattr__(metric, reduction)


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
    reductionDirectiveModule = None,
    metricSelector = None
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering numpy storage. For each metric, a .npy file is assumed to be available which the following naming convention: <id_of_setting>_<metricName>.npy.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """

    table = []
    stat = []
    modificationTimeStamp = []
    metricHasData = [False] * len(self.name())

    (reducedMetrics, rDir, rDo) = self.significanceStatus()

    for sIndex, setting in enumerate(settings):
      row = []
      rStat = []
      nbReducedMetrics = 0
      nbMetrics = 0
      for mIndex, metric in enumerate(self.name()):
        fileName = dataLocation+setting.id(**settingEncoding)+'_'+metric+'.npy'
        if os.path.exists(fileName):
          mod = os.path.getmtime(fileName)
          modificationTimeStamp.append(mod)
          if verbose:
            print('Found '+fileName+', last modified '+time.ctime(mod))
          metricHasData[mIndex] = True
          data = np.load(fileName)
          for reductionType in self.__getattribute__(metric):
            reducedMetrics[nbReducedMetrics] = True
            nbReducedMetrics+=1
            row.append(self.reduceMetric(data, reductionType, reductionDirectiveModule))
            if isinstance(reductionType, str) and '*' in reductionType:
              rStat.append(data)
        else:
          if verbose:
            print('** Unable to find '+fileName)
          for reductionType in self.__getattribute__(metric):
            row.append(np.nan)
            if isinstance(reductionType, str) and '*' in reductionType:
              rStat.append(np.nan)
            nbReducedMetrics+=1

      if len(row) and not all(np.isnan(c) for c in row):
        for factorName in reversed(settings.factors()):
          row.insert(0, setting.__getattribute__(factorName))
        table.append(row)
        stat.append(rStat)

    significance = self.significance(settings, table, stat, reducedMetrics, rDir, rDo)

    return (table, metricHasData, reducedMetrics, modificationTimeStamp, significance)

  def significanceStatus(self):
    nbReducedMetrics = 0
    rDir = []
    rDo = []
    for mIndex, metric in enumerate(self.name()):
      for reductionType in self.__getattribute__(metric):
        nbReducedMetrics += 1
        if isinstance(reductionType, str) and '*' in reductionType:
          rDo.append(1)
        else:
          rDo.append(0)
        if isinstance(reductionType, str) and len(reductionType):
           if reductionType[-1]=='-':
             rDir.append(-1)
           elif reductionType[-1]=='+':
             rDir.append(1)
           else:
             rDir.append(0)
        else:
          rDir.append(0)

    reducedMetrics = [False] * nbReducedMetrics
    return reducedMetrics, rDir, rDo

  def significance(self, settings, table, stat, reducedMetrics, rDir, rDo):

    from scipy import stats

    significance = np.zeros((len(table),len(reducedMetrics)))
    mii = 0
    for mi in range(len(rDir)):
      mv = []
      for si in range(len(table)):
        mv.append(table[si][len(settings.factors())+mi])
      if not np.isnan(mv).all() and rDir[mi]!=0:
        if rDir[mi]<0:
          im = np.nanargmin(mv)
        else:
          im = np.nanargmax(mv)
        significance[im, mi] = -1
        sRow = []
        if rDo[mi] != 0:
          for si in range(len(stat)):
            if si!=im:
              if not np.isnan(stat[si][mii]).all():
                (s, p) = stats.ttest_rel(stat[si][mii], stat[im][mii])
                significance[si, mi] = p
          mii += 1
    significance = np.delete(significance, np.invert(reducedMetrics), axis=1)

    return significance

  def reduceFromH5(
    self,
    settings,
    dataLocation,
    settingEncoding={},
    verbose = False,
    reductionDirectiveModule = None,
    metricSelector = None # TODO
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering h5 storage.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """
    import tables as tb

    table = []
    stat = []
    h5 = tb.open_file(dataLocation, mode='r')
    metricHasData = [False] * len(self.name())

    (reducedMetrics, rDir, rDo) = self.significanceStatus()

    for sIndex, setting in enumerate(settings):
      row = []
      rStat = []
      nbReducedMetrics = 0
      nbMetrics = 0
      if verbose:
        print('Seeking Group '+setting.id(**settingEncoding))
      if h5.root.__contains__(setting.id(**settingEncoding)):
        settingGroup = h5.root._f_get_child(setting.id(**settingEncoding))
        # print(settingGroup._v_name)
        # print(setting.id(**settingEncoding))
        for mIndex, metric in enumerate(self.name()):
          for reductionType in self.__getattribute__(metric):
            # value = np.nan
            noData = True
            if settingGroup.__contains__(metric):
              data = settingGroup._f_get_child(metric)
              if data.shape[0] > 0:
                metricHasData[mIndex] = True
                reducedMetrics[nbReducedMetrics] = True
                nbReducedMetrics+=1
                noData = False
              if isinstance(reductionType, str) and '*' in reductionType:
                rStat.append(np.array(data))
            if noData:
              row.append(np.nan)
              if isinstance(reductionType, str) and '*' in reductionType:
                rStat.append(np.nan)
              nbReducedMetrics+=1
            else:
              row.append(self.reduceMetric(np.array(data), reductionType, reductionDirectiveModule))
        if len(row) and not all(np.isnan(c) for c in row):
          for factorName in reversed(settings.factors()):
            row.insert(0, setting.__getattribute__(factorName))
        table.append(row)
        stat.append(rStat)
    h5.close()
    significance = self.significance(settings, table, stat, reducedMetrics, rDir, rDo)
    return (table, metricHasData, reducedMetrics, significance)

  def applyReduction(
    self,
    reductionDirectiveModule,
    reductionTypeDirective,
    data):

      if '|' in reductionTypeDirective:
        for r in reversed(reductionTypeDirective.split('|')):
          data = self.applyReduction(reductionDirectiveModule,
          r,
          data)
        return data
      else:
        if reductionTypeDirective and not hasattr(reductionDirectiveModule, reductionTypeDirective):
          return np.nan
        # print(reductionTypeDirective)
        return getattr(reductionDirectiveModule, reductionTypeDirective)(data)

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
      split = reductionType.replace('%', '').replace('*', '').replace('+', '').split('-')
      reductionTypeDirective = split[0]
      ignore = ''
      if len(split)>1:
        ignore = split[1]
      indexPercent = reductionType.find('%')

    if isinstance(reductionTypeDirective, int) or not reductionDirectiveModule or not hasattr(reductionDirectiveModule, reductionTypeDirective):
      reductionDirectiveModule = np
      data = data.flatten()

    # indexPercent=-1
    if reductionTypeDirective:
      if isinstance(reductionTypeDirective, int):
        if data.size>1:
          value = float(data[reductionTypeDirective])
        else:
          value = float(data)
      elif ignore:
        if ignore == '0':
          value = self.applyReduction(reductionDirectiveModule,reductionTypeDirective,data[1:])
        elif ignore == '1':
          value = self.applyReduction(reductionDirectiveModule,reductionTypeDirective,data[::2])
        elif ignore == '2':
          value = self.applyReduction(reductionDirectiveModule,reductionTypeDirective,data[1::2])
        else:
          print('Unrecognized pruning directive')
          raise ValueError
      else :
          value = self.applyReduction(reductionDirectiveModule,reductionTypeDirective,data)
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

    settings: doce.Plan
      iterable settings.

    dataLocation: str
      In the case of .npy storage, a valid path to the main directory. In the case of .h5 storage, a valid path to an .h5 file.

    settingEncoding : dict
      Encoding of the setting. See doce.Plan.id for references.

    reducedMetricDisplay : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric is done in a Camel case fashion: metricReduction.

      If set to 'underscore', the description of the reduced metric is done in a Python case fashion: metric_reduction.

    factor : doce.Plan
      The doce.Plan describing the factors of the experiment.

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

    doce supports metrics storage using an .npy file per metric per setting.

    >>> import doce
    >>> import numpy as np
    >>> import pandas as pd
    >>> np.random.seed(0)

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.setPath('output', '/tmp/'+experiment.name+'/', force=True)
    >>> experiment.addPlan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.setMetrics(m1 = ['mean', 'std'], m2 = ['min', 'argmin'])
    >>> def process(setting, experiment):
    ...   metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...   metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...   np.save(experiment.path.output+setting.id()+'_m1.npy', metric1)
    ...   np.save(experiment.path.output+setting.id()+'_m2.npy', metric2)
    >>> nbFailed = experiment.do([], process, progress='')
    >>> (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor, modificationTimeStamp, significance) = experiment.metric.reduce(experiment._plan.select([1]), experiment.path.output)

    >>> df = pd.DataFrame(settingDescription, columns=columnHeader)
    >>> df[columnHeader[nbColumnFactor:]] = df[columnHeader[nbColumnFactor:]].round(decimals=2)
    >>> print(constantSettingDescription)
    f1: 2
    >>> print(df)
       f2  m1Mean  m1Std  m2Min  m2Argmin
    0   1    2.87   1.00  -4.49        35
    1   2    3.97   0.93  -8.19        13
    2   3    5.00   0.91 -12.07        98

    doce also supports metrics storage using one .h5 file sink structured with settings as groups et metrics as leaf nodes.

    >>> import doce
    >>> import numpy as np
    >>> import tables as tb
    >>> import pandas as pd
    >>> np.random.seed(0)

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.setPath('output', '/tmp/'+experiment.name+'.h5', force=True)
    >>> experiment.addPlan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.setMetrics(m1 = ['mean', 'std'], m2 = ['min', 'argmin'])
    >>> def process(setting, experiment):
    ...   h5 = tb.open_file(experiment.path.output, mode='a')
    ...   settingGroup = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'m1':100, 'm2':100})
    ...   settingGroup.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...   settingGroup.m2[:] = setting.f1*setting.f2*np.random.randn(100)
    ...   h5.close()
    >>> nbFailed = experiment.do([], process, progress='')
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

    >>> (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor, modificationTimeStamp, significance) = experiment.metric.reduce(experiment.plan.select([0]), experiment.path.output)

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
      modificationTimeStamp = []
      (settingDescription, metricHasData, reducedMetrics, significance) = self.reduceFromH5(settings, dataLocation, settingEncoding, verbose, reductionDirectiveModule, metricSelector)
    else:
      (settingDescription, metricHasData, reducedMetrics, modificationTimeStamp, significance) = self.reduceFromNpy(settings, dataLocation, settingEncoding, verbose, reductionDirectiveModule, metricSelector)

    nbFactors = len(settings.factors())
    for ir, row in enumerate(settingDescription):
      settingDescription[ir] = row[:nbFactors]+list(compress(row[nbFactors:], reducedMetrics))

    columnHeader = self.getColumnHeader(settings, factorDisplay, factorDisplayLength, metricDisplay, metricDisplayLength, metricHasData, reducedMetricDisplay)
    nbColumnFactor = len(settings.factors())

    (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = eu.pruneSettingDescription(settingDescription, columnHeader, nbColumnFactor, factorDisplay)

    return (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor, modificationTimeStamp, significance)

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

    settings: doce.Plan
      Iterable settings.

    dataLocation: str
      In the case of .npy storage, a valid path to the main directory. In the case of .h5 storage, a valid path to an .h5 file.

    settingEncoding : dict
      Encoding of the setting. See doce.Plan.id for references.

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
    >>> experiment.name = 'example'
    >>> experiment.setPath('output', '/tmp/'+experiment.name+'/')
    >>> experiment.addPlan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.setMetrics(m1 = ['mean', 'std'], m2 = ['min', 'argmin'])

    >>> def process(setting, experiment):
    ...  metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...  metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...  np.save(experiment.path.output+setting.id()+'_m1.npy', metric1)
    ...  np.save(experiment.path.output+setting.id()+'_m2.npy', metric2)
    >>> nbFailed = experiment.do([], process, progress='')

    >>> (settingMetric, settingDescription, constantSettingDescription) = experiment.metric.get('m1', experiment._plan.select([1]), experiment.path.output)
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
    settingDescriptionFormat['sort'] = False

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

    (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = eu.pruneSettingDescription(settingDescription, showUniqueSetting=True)

    return (settingMetric, settingDescription, constantSettingDescription)

  def addSettingGroup(
    self,
    fileId,
    setting,
    metricDimension={},
    settingEncoding={}
    ):
    """adds a group to the root of a valid PyTables Object in order to store the metrics corresponding to the specified setting.

    adds a group to the root of a valid PyTables Object in order to store the metrics corresponding to the specified setting. The encoding of the setting is used to set the name of the group. For each metric, a Floating point Pytable Array is created. For any metric, if no dimension is provided in the metricDimension dict, an expandable array is instantiated. If a dimension is available, a static size array is instantiated.

    Parameters
    ----------

    fileId: PyTables file Object
    a valid PyTables file Object, leading to an .h5 file opened with writing permission.

    setting: :class:`doce.Plan`
    an instantiated Factor object describing a setting.

    metricDimension: dict
    for metrics for which the dimensionality of the storage vector is known, each key of the dict is a valid metric name and each conresponding value is the size of the storage vector.

    settingEncoding : dict
    Encoding of the setting. See doce.Plan.id for references.

    Returns
    -------

    settingGroup: a Pytables Group
      where metrics corresponding to the specified setting are stored.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import tables as tb

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.setPath('output', '/tmp/'+experiment.name+'.h5')
    >>> experiment.addPlan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.setMetrics (m1 = ['mean', 'std'], m2 = ['min', 'argmin'])

    >>> def process(setting, experiment):
    ...  h5 = tb.open_file(experiment.path.output, mode='a')
    ...  sg = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'m1':100})
    ...  sg.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...  sg.m2.append(setting.f1*setting.f2*np.random.randn(100))
    ...  h5.close()
    >>> nbFailed = experiment.do([], process, progress='')

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
          fileId.create_array(settingGroup, metric, np.zeros((metricDimension[metric]))*np.nan, description)
      else:
        if settingGroup.__contains__(metric):
          settingGroup._f_get_child(metric)._f_remove()
        fileId.create_earray(settingGroup, metric, tb.Float64Atom(), (0,), description)

    return settingGroup

  def getColumnHeader(
    self,
    plan,
    factorDisplay='long',
    factorDisplayLength=2,
    metricDisplay='long',
    metricDisplayLength=2,
    metricHasData=[],
    reducedMetricDisplay = 'capitalize',
    ):
    """Builds the column header of the reduction settingDescription.

    This method builds the column header of the reduction settingDescription by formating the Factor names from the doce.Plan class and by describing the reduced metrics.

    Parameters
    ----------

    plan : doce.Plan
      The doce.Plan describing the factors of the experiment.

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

    columnHeader = []
    for factorName in plan.factors():
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
    duration: ['mean'], the duration of the trial in seconds
    mse: ['mean'], the Mean Square Error
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
        cString += '\r\n'
    return cString.rstrip()

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    # doctest.run_docstring_examples(Metric.addSettingGroup, globals(), optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
