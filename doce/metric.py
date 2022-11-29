"""Handle processing of the stored outputs to produce the metrics of the doce module."""

import os
import inspect
import types
from itertools import compress
import time
import numpy as np
import doce.util as eu

class Metric():
  """Stores information about the way evaluation metrics are stored and manipulated.

  Stores information about the way evaluation metrics are stored and manipulated.
  Each member of this class describes an evaluation metric and the way it may be abstracted.
  Two name_spaces (doce.metric.Metric._unit, doce.metric.Metric._description) are available
  to respectively provide information about the unit of the metric and its semantic.

  Each metric may be reduced by any mathematical operation that operate on a vector
  made available by the numpy library with default parameters.

  Two pruning strategies can be complemented to this description in order to remove
  some items of the metric vector before being abstracted.

  One can select one value of the vector by providing its index.

  Examples
  --------

  >>> import doce
  >>> m = doce.metric.Metric()
  >>> m.duration = ['mean', 'std']
  >>> m._unit.duration = 'second'
  >>> m._description = 'duration of the processing'

  It is sometimes useful to store complementary data useful for plotting
  that must not be considered during the reduction.

  >>> m.metric1 = ['median-0', 'min-0', 'max-0']

  In this case, the first value will be removed before reduction.

  >>> m.metric2 = ['median-2', 'min-2', 'max-2', '0%']

  In this case, the odd values will be removed before reduction and the last reduction
  will select the first value of the metric vector, expressed in percents by multiplying it by 100.

  """
  def __init__(self):
    self._unit = types.SimpleNamespace()
    self._description = types.SimpleNamespace()
    self._metrics = []

    # for metric, reduction in metrics.items():
    #   self.__setattr__(metric, reduction)


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
    setting_encoding=None,
    verbose = False,
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering numpy storage.
    For each metric, a .npy file is assumed to be available which the following
    naming convention: <id_of_setting>_<metric_name>.npy.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and
    should be considered as the main user interface, please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """

    table = []
    raw_data = []
    modification_time_stamp = []
    metric_has_data = [False] * len(self.name())

    if not setting_encoding:
      setting_encoding = {}

    (reduced_metrics, metric_direction, do_testing) = self.significance_status()
    
    for setting in settings:
      row = []
      raw_data_row = []
      nb_reduced_metrics = 0
      for metric_index, metric in enumerate(self.name()):
        output = getattr(self, metric)['output']
        output_path = getattr(path, getattr(self, metric)['path'])
        file_name = output_path+setting.identifier(**setting_encoding)+'_'+output+'.npy'
        if os.path.exists(file_name):
          mod = os.path.getmtime(file_name)
          modification_time_stamp.append(mod)
          if verbose:
            print('Found '+file_name+', last modified '+time.ctime(mod))
          metric_has_data[metric_index] = True
          data = np.load(file_name)
          reduction_type=self.__getattribute__(metric)
          reduced_metrics[nb_reduced_metrics] = True
          nb_reduced_metrics+=1
          value = reduction_type['func'](data)
          if reduction_type['percent']:
            value *= 100
          row.append(value)
          if reduction_type['significance']:
            raw_data_row.append(data.flatten())
        else:
          if verbose:
            print('** Unable to find '+file_name)
          reduction_type=self.__getattribute__(metric)
          row.append(np.nan)
          if reduction_type['significance']:
            raw_data_row.append(np.nan)
          nb_reduced_metrics+=1

      if row and not all(np.isnan(c) for c in row):
        for factor_name in reversed(settings.factors()):
          row.insert(0, setting.__getattribute__(factor_name))
        table.append(row)
        
        raw_data.append(raw_data_row)

    p_values = significance(
      settings,
      table,
      raw_data,
      reduced_metrics,
      metric_direction,
      do_testing
      )

    return (table, metric_has_data, reduced_metrics, modification_time_stamp, p_values)

  def significance_status(self):
    nb_reduced_metrics = 0
    metric_direction = []
    do_testing = []
    for metric in self.name():
      reduction_type=self.__getattribute__(metric)
      nb_reduced_metrics += 1
      if reduction_type['significance']:
        do_testing.append(1)
      else:
        do_testing.append(0)
    
      if reduction_type['higher_the_better']:
        metric_direction.append(-1)
      elif reduction_type['lower_the_better']:
        metric_direction.append(1)

    reduced_metrics = [False] * nb_reduced_metrics
    return reduced_metrics, metric_direction, do_testing

  def reduce_from_h5(
    self,
    settings,
    path,
    setting_encoding=None,
    verbose = False,
    ):
    """Handle reduction of the metrics when considering numpy storage.

    The method handles the reduction of the metrics when considering h5 storage.

    The method :meth:`doce.metric.Metric.reduce` wraps this method and
    should be considered as the main user interface,
    please see its documentation for usage.

    See Also
    --------

    doce.metric.Metric.reduce

    """
    import tables as tb
    import warnings
    from tables import NaturalNameWarning
    warnings.filterwarnings('ignore', category=NaturalNameWarning)

    table = []
    raw_data = []
    h5_fid = tb.open_file(path.output, mode='r')
    metric_has_data = [False] * len(self.name())

    if not setting_encoding:
      setting_encoding = {}

    (reduced_metrics, metric_direction, do_testing) = self.significance_status()

    for setting in settings:
      row = []
      raw_data_row = []
      nb_reduced_metrics = 0
      
      if not h5_fid.root.__contains__(setting.identifier(**setting_encoding)):
        if verbose:
          print('** Not found Group '+setting.identifier(**setting_encoding))
      else:
        if verbose:
          print('Found Group '+setting.identifier(**setting_encoding))
        setting_group = h5_fid.root._f_get_child(setting.identifier(**setting_encoding))
        for metric_index, metric in enumerate(self.name()):
          reduction_type=self.__getattribute__(metric)
          no_data = True
          if setting_group.__contains__(reduction_type['output']):
            data = setting_group._f_get_child(reduction_type['output'])
            if data.shape[0] > 0:
              metric_has_data[metric_index] = True
              reduced_metrics[nb_reduced_metrics] = True
              nb_reduced_metrics+=1
              no_data = False
            if reduction_type['significance']:
              raw_data_row.append(np.array(data))
          if no_data:
            row.append(np.nan)
            if reduction_type['significance']:
              raw_data_row.append(np.nan)
            nb_reduced_metrics+=1
          else:
            value = reduction_type['func'](np.array(data))
            if reduction_type['percent']:
              value *= 100
            row.append(value)
        if row and not all(np.isnan(c) for c in row):
          for factor_name in reversed(settings.factors()):
            row.insert(0, setting.__getattribute__(factor_name))
        table.append(row)
        raw_data.append(raw_data_row)
 
    h5_fid.close()
    p_values = significance(
      settings,
      table,
      raw_data,
      reduced_metrics,
      metric_direction,
      do_testing
      )
    return (table, metric_has_data, reduced_metrics, p_values)

  def reduce(
    self,
    settings,
    path,
    setting_encoding= None,
    factor_display = 'long',
    factor_display_length = 2,
    metric_display = 'long',
    metric_display_length = 2,
    reduced_metric_display = 'capitalize',
    verbose = False
    ):
    """Apply the reduction directives described in each members of doce.metric.
    Metric objects for the settings given as parameters.

    For each setting in the iterable settings, available data corresponding
    to the metrics specified as members of the doce.metric.Metric object
    are reduced using specified reduction methods.

    Parameters
    ----------

    settings: doce.Plan
      iterable settings.

    path: str
      In the case of .npy storage, a valid path to the main directory.
      In the case of .h5 storage, a valid path to an .h5 file.

    setting_encoding : dict
      Encoding of the setting. See doce.Plan.id for references.

    reduced_metric_display : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric
      is done in a Camel case fashion: metric_reduction.

      If set to 'underscore', the description of the reduced metric is done
      in a Python case fashion: metric_reduction.

    factor : doce.Plan
      The doce.Plan describing the factors of the experiment.

    factor_display : str (optional)
      The expected format of the display of factors. 'long' (default) do not lead to any reduction.
      If factor_display contains 'short', a reduction of each word is performed.
       - 'short_underscore' assumes python_case delimitation.
       - 'short_capital' assumes camel_case delimitation.
       - 'short' attempts to perform reduction by guessing the type of delimitation.

    factor_display_length : int (optional)
      If factor_display has 'short', factor_display_length specifies the maximal
      length of each word of the description of the factor.

    verbose : bool
      In the case of .npy metric storage, if verbose is set to True,
      print the file_name seeked for each metric as well as its time of last modification.

      In the case of .h5 metric storage, if verbose is set to True,
      print the group seeked for each metric.

    Returns
    -------

    setting_description : list of lists of literals
      A setting_description, stored as a list of list of literals of the same size.
      The main list stores the rows of the setting_description.

    column_header : list of str
      The column header of the setting_description as a list of str,
      describing the factors (left side), and the reduced metrics (right side).

    constant_setting_description : str
      When a factor is equally valued for all the settings, the factor column is removed
      from the setting_description and stored in constant_setting_description along its value.

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
    >>> experiment.set_metric(name = 'm1_mean', output = 'm1', func = np.mean)
    >>> experiment.set_metric(name = 'm1_std', output = 'm1', func = np.std)
    >>> experiment.set_metric(name = 'm2_min', output = 'm2', func = np.min)
    >>> experiment.set_metric(name = 'm2_argmin', output = 'm2', func = np.argmin)
    >>> def process(setting, experiment):
    ...   metric1 = setting.f1+setting.f2+np.random.randn(100)
    ...   metric2 = setting.f1*setting.f2*np.random.randn(100)
    ...   np.save(experiment.path.output+setting.identifier()+'_m1.npy', metric1)
    ...   np.save(experiment.path.output+setting.identifier()+'_m2.npy', metric2)
    >>> nb_failed = experiment.perform([], process, progress='')
    >>> (setting_description,
    ... column_header,
    ... constant_setting_description,
    ... nb_column_factor,
    ... modification_time_stamp,
    ... p_values
    ... ) = experiment.metric.reduce(experiment._plan.select([1]), experiment.path)

    >>> df = pd.DataFrame(setting_description, columns=column_header)
    >>> df[column_header[nb_column_factor:]] = df[column_header[nb_column_factor:]].round(decimals=2)
    >>> print(constant_setting_description)
    f1: 2
    >>> print(df)
      f2  m1_mean  m1_std  m2_min  m2_argmin
    0   1    2.87   1.00  -4.49        35
    1   2    3.97   0.93  -8.19        13
    2   3    5.00   0.91 -12.07        98

    doce also supports metrics storage using one .h5 file sink structured
    with settings as groups et metrics as leaf nodes.

    >>> import doce
    >>> import numpy as np
    >>> import tables as tb
    >>> import pandas as pd
    >>> np.random.seed(0)

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.set_path('output', '/tmp/'+experiment.name+'.h5', force=True)
    >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.set_metric(name = 'm1_mean', output = 'm1', func = np.mean)
    >>> experiment.set_metric(name = 'm1_std', output = 'm1', func = np.std)
    >>> experiment.set_metric(name = 'm2_min', output = 'm2', func = np.min)
    >>> experiment.set_metric(name = 'm2_argmin', output = 'm2', func = np.argmin)
    >>> def process(setting, experiment):
    ...   h5 = tb.open_file(experiment.path.output, mode='a')
    ...   setting_group = experiment.add_setting_group(
    ...     h5,
    ...     setting,
    ...     output_dimension = {'m1':100, 'm2':100}
    ...   )
    ...   setting_group.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...   setting_group.m2[:] = setting.f1*setting.f2*np.random.randn(100)
    ...   h5.close()
    >>> nb_failed = experiment.perform([], process, progress='')
    >>> h5 = tb.open_file(experiment.path.output, mode='r')
    >>> print(h5)
    /tmp/example.h5 (File) ''
    Last modif.: '...'
        Object Tree:
    / (RootGroup) ''
    /f1=1+f2=1 (Group) 'f1=1+f2=1'
    /f1=1+f2=1/m1 (Array(100,)) 'm1'
    /f1=1+f2=1/m2 (EArray(100,)) 'm2'
    /f1=1+f2=2 (Group) 'f1=1+f2=2'
    /f1=1+f2=2/m1 (Array(100,)) 'm1'
    /f1=1+f2=2/m2 (EArray(100,)) 'm2'
    /f1=1+f2=3 (Group) 'f1=1+f2=3'
    /f1=1+f2=3/m1 (Array(100,)) 'm1'
    /f1=1+f2=3/m2 (EArray(100,)) 'm2'
    /f1=2+f2=1 (Group) 'f1=2+f2=1'
    /f1=2+f2=1/m1 (Array(100,)) 'm1'
    /f1=2+f2=1/m2 (EArray(100,)) 'm2'
    /f1=2+f2=2 (Group) 'f1=2+f2=2'
    /f1=2+f2=2/m1 (Array(100,)) 'm1'
    /f1=2+f2=2/m2 (EArray(100,)) 'm2'
    /f1=2+f2=3 (Group) 'f1=2+f2=3'
    /f1=2+f2=3/m1 (Array(100,)) 'm1'
    /f1=2+f2=3/m2 (EArray(100,)) 'm2'
    >>> h5.close()

    >>> (setting_description,
    ... column_header,
    ... constant_setting_description,
    ... nb_column_factor,
    ... modification_time_stamp,
    ... p_values) = experiment.metric.reduce(experiment.plan.select([0]), experiment.path)

    >>> df = pd.DataFrame(setting_description, columns=column_header)
    >>> df[column_header[nb_column_factor:]] = df[column_header[nb_column_factor:]].round(decimals=2)
    >>> print(constant_setting_description)
    f1: 1
    >>> print(df)
      f2  m1_mean  m1_std  m2_min  m2_argmin
    0   1    2.06   1.01  -2.22        83
    1   2    2.94   0.95  -5.32        34
    2   3    3.99   1.04  -9.14        89
    """

    if self.name():
      if path.output.endswith('.h5'):
        # setting_encoding = {'factor_separator':'_', 'modality_separator':'_'}
        setting_encoding = {}
        modification_time_stamp = []
        (setting_description,
        metric_has_data,
        reduced_metrics,
        p_values) = self.reduce_from_h5(
          settings,
          path,
          setting_encoding,
          verbose)
      else:
        (setting_description,
        metric_has_data,
        reduced_metrics,
        modification_time_stamp,
        p_values) = self.reduce_from_npy(
          settings,
          path,
          setting_encoding,
          verbose)

      nb_factors = len(settings.factors())
      for row_index, row in enumerate(setting_description):
        setting_description[row_index] = row[:nb_factors]+list(compress(row[nb_factors:], reduced_metrics))

      column_header = self.get_column_header(
        settings,
        factor_display,
        factor_display_length,
        metric_display,
        metric_display_length,
        metric_has_data,
        reduced_metric_display)
      nb_column_factor = len(settings.factors())

      (setting_description,
      column_header,
      constant_setting_description,
      nb_column_factor) = eu.prune_setting_description(
        setting_description,
        column_header,
        nb_column_factor,
        factor_display)

      return (setting_description,
        column_header,
        constant_setting_description,
        nb_column_factor,
        modification_time_stamp,
        p_values)
    return ([], [], '', 0, [], [])

  

  def get_column_header(
    self,
    plan,
    factor_display='long',
    factor_display_length=2,
    metric_display='long',
    metric_display_length=2,
    metric_has_data=None,
    reduced_metric_display = 'capitalize',
    ):
    """Builds the column header of the reduction setting_description.

    This method builds the column header of the reduction setting_description
    by formating the Factor names from the doce.Plan class and by describing the reduced metrics.

    Parameters
    ----------

    plan : doce.Plan
      The doce.Plan describing the factors of the experiment.

    factor_display : str (optional)
      The expected format of the display of factors. 'long' (default) do not lead to any reduction.
      If factor_display contains 'short', a reduction of each word is performed.
       - 'short_underscore' assumes python_case delimitation.
       - 'short_capital' assumes camel_case delimitation.
       - 'short' attempts to perform reduction by guessing the type of delimitation.

    factor_display_length : int (optional)
      If factor_display has 'short', factor_display_length specifies the maximal length
      of each word of the description of the factor.

    metric_has_data : list of bool
      Specify for each metric described in the doce.metric.Metric object,
      whether data has been loaded or not.

    reduced_metric_display : str (optional)
      If set to 'capitalize' (default), the description of the reduced metric is done
      in a Camel case fashion: metricReduction.

      If set to 'underscore', the description of the reduced metric is done
      in a snake case fashion: metric_reduction.

    See Also
    --------

    doce.util.compress_description
    """

    column_header = []
    for factor_name in plan.factors():
      column_header.append(eu.compress_description(
        factor_name,
        factor_display,
        factor_display_length
        ))
    for metric_index, metric in enumerate(self.name()):
      if self.__getattribute__(metric)['percent']:
        metric+=(' %')
      if metric_has_data[metric_index]:
        column_header.append(eu.compress_description(metric, metric_display, metric_display_length))
    return column_header

  def name(
    self
    ):
    """Returns a list of str with the names of the metrics.

    Returns a list of str with the names of the metrics defined as members
    of the doce.metric.Metric object.

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
    metric_descriptor = ''
    atrs = dict(vars(type(self)))
    atrs.update(vars(self))
    atrs = [a for a in atrs if a[0] !=  '_']

    for atr in atrs:
      if not isinstance(inspect.getattr_static(self, atr), types.FunctionType):
        metric_descriptor+='  '+atr+': '+str(self.__getattribute__(atr))
        if hasattr(self._description, atr):
          metric_descriptor+=', the '+str(self._description.__getattribute__(atr))+''
        if hasattr(self._unit, atr) and self._unit.__getattribute__(atr):
          metric_descriptor+=' in '+str(self._unit.__getattribute__(atr))
        metric_descriptor += '\r\n'
    return metric_descriptor.rstrip()

def significance(
  settings,
  table,
  raw_data,
  reduced_metrics,
  metric_direction,
  do_testing):

  from scipy import stats

  p_values = np.zeros((len(table),len(reduced_metrics)))
  metric_stat_index = 0
  for direction_index, direction in enumerate(metric_direction):
    mean_values = []
    for table_row in table:
      mean_values.append(table_row[len(settings.factors())+direction_index])
    if not np.isnan(mean_values).all() and direction!=0:
      if metric_direction[direction_index]<0:
        best_index = np.argwhere(mean_values==np.nanmax(mean_values)).flatten()
      else:
        best_index = np.argwhere(mean_values==np.nanmin(mean_values)).flatten()
      p_values[best_index, direction_index] = -1
      if do_testing[direction_index] != 0:
        for raw_data_row_index, raw_data_row in enumerate(raw_data):
          if p_values[raw_data_row_index, direction_index] != -1: # raw_data_row_index!=best_index[0] and and mean_values[metric_stat_index] != mean_values[raw_data_row_index])
            if not np.isnan(raw_data[raw_data_row_index][metric_stat_index]).all():
              (_, p_value) = stats.ttest_rel(
                raw_data_row[metric_stat_index],
                raw_data[best_index[0]][metric_stat_index]
                )
              p_values[raw_data_row_index, direction_index] = p_value
        metric_stat_index += 1
  # p_values = np.delete(p_values, np.invert(reduced_metrics), axis=1)

  return p_values

if __name__ == '__main__':
  import doctest
  doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

  # doctest.run_docstring_examples(
  #   _metric.add_setting_group,
  #   globals(),
  #   optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
  # )
