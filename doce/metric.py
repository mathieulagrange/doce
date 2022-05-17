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

  Stores information about the way evaluation metrics are stored and manipulated. Each member of this class describes an evaluation metric and the way it may be abstracted. Two name_spaces (doce.metric.Metric._unit, doce.metric.Metric._description) are available to respectively provide information about the unit of the metric and its semantic.

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

  def reduce_from_npy(
    self,
    settings,
    path,
    setting_encoding={},
    verbose = False,
    reduction_directive_module = None,
    metric_selector = None
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering numpy storage. For each metric, a .npy file is assumed to be available which the following naming convention: <id_of_setting>_<metric_name>.npy.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """

    table = []
    stat = []
    modification_time_stamp = []
    metric_has_data = [False] * len(self.name())

    (reduced_metrics, rDir, rDo) = self.significance_status()

    for sIndex, setting in enumerate(settings):
      row = []
      rStat = []
      nb_reduced_metrics = 0
      nb_metrics = 0
      for mIndex, metric in enumerate(self.name()):
        file_name = path+setting.id(**setting_encoding)+'_'+metric+'.npy'
        if os.path.exists(file_name):
          mod = os.path.getmtime(file_name)
          modification_time_stamp.append(mod)
          if verbose:
            print('Found '+file_name+', last modified '+time.ctime(mod))
          metric_has_data[mIndex] = True
          data = np.load(file_name)
          for reduction_type in self.__getattribute__(metric):
            reduced_metrics[nb_reduced_metrics] = True
            nb_reduced_metrics+=1
            row.append(self.reduce_metric(data, reduction_type, reduction_directive_module))
            if isinstance(reduction_type, str) and '*' in reduction_type:
              rStat.append(data)
        else:
          if verbose:
            print('** Unable to find '+file_name)
          for reduction_type in self.__getattribute__(metric):
            row.append(np.nan)
            if isinstance(reduction_type, str) and '*' in reduction_type:
              rStat.append(np.nan)
            nb_reduced_metrics+=1

      if len(row) and not all(np.isnan(c) for c in row):
        for factor_name in reversed(settings.factors()):
          row.insert(0, setting.__getattribute__(factor_name))
        table.append(row)
        stat.append(rStat)

    significance = self.significance(settings, table, stat, reduced_metrics, rDir, rDo)

    return (table, metric_has_data, reduced_metrics, modification_time_stamp, significance)

  def significance_status(self):
    nb_reduced_metrics = 0
    rDir = []
    rDo = []
    for mIndex, metric in enumerate(self.name()):
      for reduction_type in self.__getattribute__(metric):
        nb_reduced_metrics += 1
        if isinstance(reduction_type, str) and '*' in reduction_type:
          rDo.append(1)
        else:
          rDo.append(0)
        if isinstance(reduction_type, str) and len(reduction_type):
           if '-' in reduction_type:
             rDir.append(-1)
           elif '+' in reduction_type:
             rDir.append(1)
           elif '*' in reduction_type:
             rDir.append(1)
             print('statistical testing will assume a higher the better metric. You can remove this warning by adding a + to the metric reduction directive.')
           else:
             rDir.append(0)
        else:
          rDir.append(0)

    reduced_metrics = [False] * nb_reduced_metrics
    return reduced_metrics, rDir, rDo

  def significance(self, settings, table, stat, reduced_metrics, rDir, rDo):

    from scipy import stats

    significance = np.zeros((len(table),len(reduced_metrics)))
    mii = 0
    for mi in range(len(rDir)):
      mv = []
      for si in range(len(table)):
        mv.append(table[si][len(settings.factors())+mi])
      if not np.isnan(mv).all() and rDir[mi]!=0:
        if rDir[mi]<0:
          im = np.argwhere(mv==np.nanmin(mv)).flatten()
        else:
          im = np.argwhere(mv==np.nanmax(mv)).flatten()
        significance[im, mi] = -1
        sRow = []
        if rDo[mi] != 0:
          for si in range(len(stat)):
            if si!=im[0] and mv[mii] != mv[si]:
              if not np.isnan(stat[si][mii]).all():
                (s, p) = stats.ttest_rel(stat[si][mii], stat[im[0]][mii])
                significance[si, mi] = p
          mii += 1
    significance = np.delete(significance, np.invert(reduced_metrics), axis=1)

    return significance

  def reduce_from_h5(
    self,
    settings,
    path,
    setting_encoding={},
    verbose = False,
    reduction_directive_module = None,
    metric_selector = None # TODO
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
    h5 = tb.open_file(path, mode='r')
    metric_has_data = [False] * len(self.name())

    (reduced_metrics, rDir, rDo) = self.significance_status()

    for sIndex, setting in enumerate(settings):
      row = []
      rStat = []
      nb_reduced_metrics = 0
      nb_metrics = 0
      if verbose:
        print('Seeking Group '+setting.id(**setting_encoding))
      if h5.root.__contains__(setting.id(**setting_encoding)):
        setting_group = h5.root._f_get_child(setting.id(**setting_encoding))
        # print(setting_group._v_name)
        # print(setting.id(**setting_encoding))
        for mIndex, metric in enumerate(self.name()):
          for reduction_type in self.__getattribute__(metric):
            # value = np.nan
            no_data = True
            if setting_group.__contains__(metric):
              data = setting_group._f_get_child(metric)
              if data.shape[0] > 0:
                metric_has_data[mIndex] = True
                reduced_metrics[nb_reduced_metrics] = True
                nb_reduced_metrics+=1
                no_data = False
              if isinstance(reduction_type, str) and '*' in reduction_type:
                rStat.append(np.array(data))
            if no_data:
              row.append(np.nan)
              if isinstance(reduction_type, str) and '*' in reduction_type:
                rStat.append(np.nan)
              nb_reduced_metrics+=1
            else:
              row.append(self.reduce_metric(np.array(data), reduction_type, reduction_directive_module))
        if len(row) and not all(np.isnan(c) for c in row):
          for factor_name in reversed(settings.factors()):
            row.insert(0, setting.__getattribute__(factor_name))
        table.append(row)
        stat.append(rStat)
    h5.close()
    significance = self.significance(settings, table, stat, reduced_metrics, rDir, rDo)
    return (table, metric_has_data, reduced_metrics, significance)

  def apply_reduction(
    self,
    reduction_directive_module,
    reduction_typeDirective,
    data):

      if '|' in reduction_typeDirective:
        for r in reversed(reduction_typeDirective.split('|')):
          data = self.apply_reduction(reduction_directive_module,
          r,
          data)
        return data
      else:
        if reduction_typeDirective and not hasattr(reduction_directive_module, reduction_typeDirective):
          return np.nan
        # print(reduction_typeDirective)
        return getattr(reduction_directive_module, reduction_typeDirective)(data)

  def reduce_metric(
    self,
    data,
    reduction_type,
    reduction_directive_module=None
    ):
    """Apply reduction directive to a metric vector after potentially remove non wanted items from the vector.

    The data vector is reduced by considering the reduction directive after potentially remove non wanted items from the vector.

    Parameters
    ----------

    data : numpy array
      1-D vector to be reduced.

    reduction_type : str
      type of reduction to be applied to the data vector. Can be any method supplied by the reduction_directive_module. If unavailable, a numpy method with this name that can applied to a vector and returns a value is searched for. Selectors and layout can also be specified.

    reduction_directive_module : str (optional)
      Python module to perform the reduction. If None, numpy is considered.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> data = np.linspace(1, 10, num=10)
    >>> print(data)
    [ 1.  2.  3.  4.  5.  6.  7.  8.  9. 10.]
    >>> m  =doce.metric.Metric()
    >>> m.reduce_metric(data, 0)
    1.0
    >>> m.reduce_metric(data, 8)
    9.0
    >>> m.reduce_metric(data, 'sum%')
    5500.0
    >>> m.reduce_metric(data, 'sum-0')
    54.0
    >>> m.reduce_metric(data, 'sum-1')
    25.0
    >>> m.reduce_metric(data, 'sum-2')
    30.0

    """

    if reduction_directive_module == 'None':
      reduction_directive_module = np
    reduction_typeDirective = reduction_type
    index_percent = -1
    if isinstance(reduction_type, str):
      split = reduction_type.replace('%', '').replace('*', '').replace('+', '').split('-')
      reduction_typeDirective = split[0]
      ignore = ''
      if len(split)>1:
        ignore = split[1]
      index_percent = reduction_type.find('%')

    if isinstance(reduction_typeDirective, int) or not reduction_directive_module or not hasattr(reduction_directive_module, reduction_typeDirective):
      reduction_directive_module = np
      data = data.flatten()

    # index_percent=-1
    if reduction_typeDirective:
      if isinstance(reduction_typeDirective, int):
        if data.size>1:
          value = float(data[reduction_typeDirective])
        else:
          value = float(data)
      elif ignore:
        if ignore == '0':
          value = self.apply_reduction(reduction_directive_module,reduction_typeDirective,data[1:])
        elif ignore == '1':
          value = self.apply_reduction(reduction_directive_module,reduction_typeDirective,data[::2])
        elif ignore == '2':
          value = self.apply_reduction(reduction_directive_module,reduction_typeDirective,data[1::2])
        else:
          print('Unrecognized pruning directive')
          raise value_error
      else :
          value = self.apply_reduction(reduction_directive_module,reduction_typeDirective,data)
    else:
      if not isinstance(data, np.ndarray):
        data = np.array(data)
      if data.size>1:
        value = float(data[0])
      else:
        value = float(data)
    if index_percent>-1:
      value *= 100
    return value

  def reduce(
    self,
    settings,
    path,
    setting_encoding= {},
    factor_display = 'long',
    factor_display_length = 2,
    metric_display = 'long',
    metric_display_length = 2,
    reduced_metric_display = 'capitalize',
    verbose = False,
    reduction_directive_module = None,
    expand_factor = None,
    metric_selector = None
    ):
    """Apply the reduction directives described in each members of doce.metric.Metric objects for the settings given as parameters.

    For each setting in the iterable settings, available data corresponding to the metrics specified as members of the doce.metric.Metric object are reduced using specified reduction methods.

    Parameters
    ----------

    settings: doce.Plan
      iterable settings.

    path: str
      In the case of .npy storage, a valid path to the main directory. In the case of .h5 storage, a valid path to an .h5 file.

    setting_encoding : dict
      Encoding of the setting. See doce.Plan.id for references.

    reduced_metric_display : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric is done in a Camel case fashion: metric_reduction.

      If set to 'underscore', the description of the reduced metric is done in a Python case fashion: metric_reduction.

    factor : doce.Plan
      The doce.Plan describing the factors of the experiment.

    factor_display : str (optional)
      The expected format of the display of factors. 'long' (default) do not lead to any reduction. If factor_display contains 'short', a reduction of each word is performed. 'short_underscore' assumes python_case delimitation. 'short_capital' assumes camel_case delimitation. 'short' attempts to perform reduction by guessing the type of delimitation.

    factor_display_length : int (optional)
      If factor_display has 'short', factor_display_length specifies the maximal length of each word of the description of the factor.

    verbose : bool
      In the case of .npy metric storage, if verbose is set to True, print the file_name seeked for each metric as well as its time of last modification.

      In the case of .h5 metric storage, if verbose is set to True, print the group seeked for each metric.

    Returns
    -------

    setting_description : list of lists of literals
      A setting_description, stored as a list of list of literals of the same size. The main list stores the rows of the setting_description.

    column_header : list of str
      The column header of the setting_description as a list of str, describing the factors (left side), and the reduced metrics (right side).

    constant_setting_description : str
      When a factor is equally valued for all the settings, the factor column is removed from the setting_description and stored in constant_setting_description along its value.

    nb_column_factor : int
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
    >>> experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)
    >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.set_metrics(m1 = ['mean', 'std'], m2 = ['min', 'argmin'])
    >>> def process(setting, experiment):
    ...   metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...   metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...   np.save(experiment.path.output+setting.id()+'_m1.npy', metric1)
    ...   np.save(experiment.path.output+setting.id()+'_m2.npy', metric2)
    >>> nb_failed = experiment.do([], process, progress='')
    >>> (setting_description, column_header, constant_setting_description, nb_column_factor, modification_time_stamp, significance) = experiment.metric.reduce(experiment._plan.select([1]), experiment.path.output)

    >>> df = pd.DataFrame(setting_description, columns=column_header)
    >>> df[column_header[nb_column_factor:]] = df[column_header[nb_column_factor:]].round(decimals=2)
    >>> print(constant_setting_description)
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
    >>> experiment.set_path('output', '/tmp/'+experiment.name+'.h5', force=True)
    >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.set_metrics(m1 = ['mean', 'std'], m2 = ['min', 'argmin'])
    >>> def process(setting, experiment):
    ...   h5 = tb.open_file(experiment.path.output, mode='a')
    ...   setting_group = experiment.metric.add_setting_group(h5, setting, metric_dimension = {'m1':100, 'm2':100})
    ...   setting_group.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...   setting_group.m2[:] = setting.f1*setting.f2*np.random.randn(100)
    ...   h5.close()
    >>> nb_failed = experiment.do([], process, progress='')
    >>> h5 = tb.open_file(experiment.path.output, mode='r')
    >>> print(h5)
    /tmp/example.h5 (File) ''
    Last modif.: '...'
        Object Tree:
    / (RootGroup) ''
    /f1_1_f2_1 (Group) 'f1=1+f2=1'
    /f1_1_f2_1/m1 (Array(100,)) 'm1'
    /f1_1_f2_1/m2 (EArray(100,)) 'm2'
    /f1_1_f2_2 (Group) 'f1=1+f2=2'
    /f1_1_f2_2/m1 (Array(100,)) 'm1'
    /f1_1_f2_2/m2 (EArray(100,)) 'm2'
    /f1_1_f2_3 (Group) 'f1=1+f2=3'
    /f1_1_f2_3/m1 (Array(100,)) 'm1'
    /f1_1_f2_3/m2 (EArray(100,)) 'm2'
    /f1_2_f2_1 (Group) 'f1=2+f2=1'
    /f1_2_f2_1/m1 (Array(100,)) 'm1'
    /f1_2_f2_1/m2 (EArray(100,)) 'm2'
    /f1_2_f2_2 (Group) 'f1=2+f2=2'
    /f1_2_f2_2/m1 (Array(100,)) 'm1'
    /f1_2_f2_2/m2 (EArray(100,)) 'm2'
    /f1_2_f2_3 (Group) 'f1=2+f2=3'
    /f1_2_f2_3/m1 (Array(100,)) 'm1'
    /f1_2_f2_3/m2 (EArray(100,)) 'm2'
    >>> h5.close()

    >>> (setting_description, column_header, constant_setting_description, nb_column_factor, modification_time_stamp, significance) = experiment.metric.reduce(experiment.plan.select([0]), experiment.path.output)

    >>> df = pd.DataFrame(setting_description, columns=column_header)
    >>> df[column_header[nb_column_factor:]] = df[column_header[nb_column_factor:]].round(decimals=2)
    >>> print(constant_setting_description)
    f1: 1
    >>> print(df)
      f2  m1Mean  m1Std  m2Min  m2Argmin
    0   1    2.06   1.01  -2.22        83
    1   2    2.94   0.95  -5.32        34
    2   3    3.99   1.04  -9.14        89
    """

    if len(self.name()):
      if path.endswith('.h5'):
        setting_encoding = {'separator':'_', 'identifier':'_'}
        modification_time_stamp = []
        (setting_description, metric_has_data, reduced_metrics, significance) = self.reduce_from_h5(settings, path, setting_encoding, verbose, reduction_directive_module, metric_selector)
      else:
        (setting_description, metric_has_data, reduced_metrics, modification_time_stamp, significance) = self.reduce_from_npy(settings, path, setting_encoding, verbose, reduction_directive_module, metric_selector)

      nb_factors = len(settings.factors())
      for ir, row in enumerate(setting_description):
        setting_description[ir] = row[:nb_factors]+list(compress(row[nb_factors:], reduced_metrics))

      column_header = self.get_column_header(settings, factor_display, factor_display_length, metric_display, metric_display_length, metric_has_data, reduced_metric_display)
      nb_column_factor = len(settings.factors())

      (setting_description, column_header, constant_setting_description, nb_column_factor) = eu.prune_setting_description(setting_description, column_header, nb_column_factor, factor_display)

      return (setting_description, column_header, constant_setting_description, nb_column_factor, modification_time_stamp, significance)
    else:
      return ([], [], '', 0, [], [])


  def get(
    self,
    metric,
    settings = None,
    path = '',
    setting_encoding={},
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

    path: str
      In the case of .npy storage, a valid path to the main directory. In the case of .h5 storage, a valid path to an .h5 file.

    setting_encoding : dict
      Encoding of the setting. See doce.Plan.id for references.

    verbose : bool
      In the case of .npy metric storage, if verbose is set to True, print the file_name seeked for the metric.

      In the case of .h5 metric storage, if verbose is set to True, print the group seeked for the metric.

    Returns
    -------

    setting_metric: list of np.Array
      stores for each valid setting an np.Array with the values of the metric selected.

    setting_description: list of list of str
      stores for each valid setting, a compact description of the modalities of each factors. The factors with the same modality accross all the set of settings is stored in constant_setting_description.

    constant_setting_description: str
      compact description of the factors with the same modality accross all the set of settings.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import pandas as pd

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)
    >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.set_metrics(m1 = ['mean', 'std'], m2 = ['min', 'argmin'])

    >>> def process(setting, experiment):
    ...  metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...  metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...  np.save(experiment.path.output+setting.id()+'_m1.npy', metric1)
    ...  np.save(experiment.path.output+setting.id()+'_m2.npy', metric2)
    >>> nb_failed = experiment.do([], process, progress='')

    >>> (setting_metric, setting_description, constant_setting_description) = experiment.metric.get('m1', experiment._plan.select([1]), experiment.path.output)
    >>> print(constant_setting_description)
    f1=2
    >>> print(setting_description)
    ['f2=1', 'f2=2', 'f2=3']
    >>> print(len(setting_metric))
    3
    >>> print(setting_metric[0].shape)
    (100,)
    """

    setting_metric = []
    setting_description = []
    setting_descriptionFormat = copy.deepcopy(setting_encoding)
    setting_descriptionFormat['format'] = 'list'
    setting_descriptionFormat['default'] = True
    setting_descriptionFormat['sort'] = False

    if isinstance(path, str):
      if path.endswith('.h5'):
        h5 = tb.open_file(path, mode='r')
        for setting in settings:
          if h5.root.__contains__(setting.id(**setting_encoding)):
            if verbose:
              print('Found group '+setting.id(**setting_encoding))
            setting_group = h5.root._f_get_child(setting.id(**setting_encoding))
            if setting_group.__contains__(metric):
              setting_metric.append(np.array(setting_group._f_get_child(metric)))
              setting_description.append(setting.id(**setting_descriptionFormat))
          elif verbose:
            print('** Unable to find group '+setting.id(**setting_encoding))
        h5.close()
      else:
        for setting in settings:
          file_name = path+setting.id(**setting_encoding)+'_'+metric+'.npy'
          if os.path.exists(file_name):
            if verbose:
              print('Found '+file_name)
            setting_metric.append(np.load(file_name))
            setting_description.append(setting.id(**setting_descriptionFormat))
          elif verbose:
            print('** Unable to find '+file_name)

    (setting_description, column_header, constant_setting_description, nb_column_factor) = eu.prune_setting_description(setting_description, show_unique_setting = True)

    for ri, r in enumerate(setting_description):
      setting_description[ri] = ', '.join(r)

    return (setting_metric, setting_description, constant_setting_description)

  def add_setting_group(
    self,
    file_id,
    setting,
    metric_dimension={},
    setting_encoding={'separator':'_', 'identifier':'_'}
    ):
    """adds a group to the root of a valid py_tables Object in order to store the metrics corresponding to the specified setting.

    adds a group to the root of a valid py_tables Object in order to store the metrics corresponding to the specified setting. The encoding of the setting is used to set the name of the group. For each metric, a Floating point Pytable Array is created. For any metric, if no dimension is provided in the metric_dimension dict, an expandable array is instantiated. If a dimension is available, a static size array is instantiated.

    Parameters
    ----------

    file_id: py_tables file Object
    a valid py_tables file Object, leading to an .h5 file opened with writing permission.

    setting: :class:`doce.Plan`
    an instantiated Factor object describing a setting.

    metric_dimension: dict
    for metrics for which the dimensionality of the storage vector is known, each key of the dict is a valid metric name and each conresponding value is the size of the storage vector.

    setting_encoding : dict
    Encoding of the setting. See doce.Plan.id for references.

    Returns
    -------

    setting_group: a Pytables Group
      where metrics corresponding to the specified setting are stored.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import tables as tb

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.set_path('output', '/tmp/'+experiment.name+'.h5')
    >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.set_metrics (m1 = ['mean', 'std'], m2 = ['min', 'argmin'])

    >>> def process(setting, experiment):
    ...  h5 = tb.open_file(experiment.path.output, mode='a')
    ...  sg = experiment.metric.add_setting_group(h5, setting, metric_dimension = {'m1':100})
    ...  sg.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...  sg.m2.append(setting.f1*setting.f2*np.random.randn(100))
    ...  h5.close()
    >>> nb_failed = experiment.do([], process, progress='')

    >>> h5 = tb.open_file(experiment.path.output, mode='r')
    >>> print(h5)
    /tmp/example.h5 (File) ''
    Last modif.: '...'
    Object Tree:
    / (RootGroup) ''
    /f1_1_f2_1 (Group) 'f1=1+f2=1'
    /f1_1_f2_1/m1 (Array(100,)) 'm1'
    /f1_1_f2_1/m2 (EArray(100,)) 'm2'
    /f1_1_f2_2 (Group) 'f1=1+f2=2'
    /f1_1_f2_2/m1 (Array(100,)) 'm1'
    /f1_1_f2_2/m2 (EArray(100,)) 'm2'
    /f1_1_f2_3 (Group) 'f1=1+f2=3'
    /f1_1_f2_3/m1 (Array(100,)) 'm1'
    /f1_1_f2_3/m2 (EArray(100,)) 'm2'
    /f1_2_f2_1 (Group) 'f1=2+f2=1'
    /f1_2_f2_1/m1 (Array(100,)) 'm1'
    /f1_2_f2_1/m2 (EArray(100,)) 'm2'
    /f1_2_f2_2 (Group) 'f1=2+f2=2'
    /f1_2_f2_2/m1 (Array(100,)) 'm1'
    /f1_2_f2_2/m2 (EArray(100,)) 'm2'
    /f1_2_f2_3 (Group) 'f1=2+f2=3'
    /f1_2_f2_3/m1 (Array(100,)) 'm1'
    /f1_2_f2_3/m2 (EArray(100,)) 'm2'

    >>> h5.close()
    """
    import tables as tb

    group_name = setting.id(**setting_encoding)
    # print(group_name)
    if not file_id.__contains__('/'+group_name):
      setting_group = file_id.create_group('/', group_name, str(setting))
    else:
      setting_group = file_id.root._f_get_child(group_name)
    for metric in self.name():
      if hasattr(self._description, metric):
        description = getattr(self._description, metric)
      else:
        description = metric

      if hasattr(self._unit, metric):
        description += ' in ' + getattr(self._unit, metric)

      if metric in metric_dimension:
        if not setting_group.__contains__(metric):
          file_id.create_array(setting_group, metric, np.zeros((metric_dimension[metric]))*np.nan, description)
      else:
        if setting_group.__contains__(metric):
          setting_group._f_get_child(metric)._f_remove()
        file_id.create_earray(setting_group, metric, tb.Float64Atom(), (0,), description)

    return setting_group

  def get_column_header(
    self,
    plan,
    factor_display='long',
    factor_display_length=2,
    metric_display='long',
    metric_display_length=2,
    metric_has_data=[],
    reduced_metric_display = 'capitalize',
    ):
    """Builds the column header of the reduction setting_description.

    This method builds the column header of the reduction setting_description by formating the Factor names from the doce.Plan class and by describing the reduced metrics.

    Parameters
    ----------

    plan : doce.Plan
      The doce.Plan describing the factors of the experiment.

    factor_display : str (optional)
      The expected format of the display of factors. 'long' (default) do not lead to any reduction. If factor_display contains 'short', a reduction of each word is performed. 'short_underscore' assumes python_case delimitation. 'short_capital' assumes camel_case delimitation. 'short' attempts to perform reduction by guessing the type of delimitation.

    factor_display_length : int (optional)
      If factor_display has 'short', factor_display_length specifies the maximal length of each word of the description of the factor.

    metric_has_data : list of bool
      Specify for each metric described in the doce.metric.Metric object, whether data has been loaded or not.

    reduced_metric_display : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric is done in a Camel case fashion: metric_reduction.

      If set to 'underscore', the description of the reduced metric is done in a Python case fashion: metric_reduction.

    See Also
    --------

    doce.util.compress_description
    """

    column_header = []
    for factor_name in plan.factors():
      column_header.append(eu.compress_description(factor_name, factor_display, factor_display_length))
    for mIndex, metric in enumerate(self.name()):
      if metric_has_data[mIndex]:
        for reduction_type in self.__getattribute__(metric):
          if reduced_metric_display == 'capitalize':
            name = metric+str(reduction_type).capitalize()
          elif reduced_metric_display == 'underscore':
            name = metric+'_'+reduction_type
          else:
            print('Unrecognized reduced_metric_display value. Should be \'capitalize\' or \'underscore\'. Got:'+reduced_metric_display)
            raise value_error
          column_header.append(eu.compress_description(name, metric_display, metric_display_length))
    return column_header

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

    # doctest.run_docstring_examples(_metric.add_setting_group, globals(), optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
