"""Handle storage and processing of the plan of the doce module."""

import os
import shutil as sh
import inspect
import types
import copy
import glob
import logging
import time
from itertools import groupby
import subprocess
import numpy as np
import doce.util as eu
import doce.setting as es

if eu.in_notebook():
  from tqdm.notebook import tqdm as tqdm
else:
  from tqdm import tqdm as tqdm

class Plan():
  """stores the different factors of the doce experiment.

  This class stores the different factors of the doce experiments.
  For each factor, the set of different modalities can be expressed as a list or a numpy array.

  To browse the setting set defined by the Plan object, one must iterate over the Plan object.

  Examples
  --------

  >>> import doce

  >>> p = doce.Plan('')
  >>> p.factor1=[1, 3]
  >>> p.factor2=[2, 4]

  >>> print(p)
    0  factor1: [1 3]
    1  factor2: [2 4]

  >>> for setting in p:
  ...   print(setting)
  factor1=1+factor2=2
  factor1=1+factor2=4
  factor1=3+factor2=2
  factor1=3+factor2=4
  """
  def __init__(self, name, **factors):
    self._name = name
    self._setting = None
    self._changed = False
    self._current_setting = 0
    self._settings = []
    self._selector = None
    self._expanded_selector = None
    self._non_singleton = []
    self._factors = []
    self._default = types.SimpleNamespace()
    self._selector_volatile = True
    self._prune_selector = True

    for factor, modalities in factors.items():
      self.__setattr__(factor, modalities)


  def copy(self):
    return copy.deepcopy(self)

  def default(
    self,
    factor,
    modality
    ):
    """set the default modality for the specified factor.

  	Set the default modality for the specified factor.

  	Parameters
  	----------

    factor: str
      the name of the factor

    modality: int or str
      the modality value

  	See Also
  	--------

    doce.Plan.id

  	Examples
  	--------

    >>> import doce

    p = doce.Plan('')

    p.f1 = ['a', 'b']
    p.f2 = [1, 2, 3]

    print(f)
    for setting in p.select():
      print(setting.identifier())

    p.default('f2', 2)

    for setting in p:
      print(setting.identifier())

    p.f2 = [0, 1, 2, 3]
    print(f)

    p.default('f2', 2)

    for setting in p:
      print(setting.identifier())
    """
    if hasattr(self, factor):
      # if (generic_default_modality_warning and
      #     len([item for item in getattr(self, factor) if item in [0, 'none']]):
      #   print(f'''Setting an explicit default modality to factor {factor} should be handled
      #     with care as the factor already as an implicit default modality (O or none).
      #     This may lead to loss of data. Ensure that you have the flag <hide_none_and_zero>
      #     set to False when using method identifier() if (O or none). You can remove this warning
      #     by setting the flag <force> to True.''')
      if modality not in getattr(self, factor):
        print(f'''The default modality of factor {factor}\
           should be available in the set of modalities.''')
        raise ValueError
      self._default.__setattr__(factor, modality)
    else:
      print(f'''Please set the factor {factor}\
         before choosing its default modality.''')
      raise ValueError

  def perform(
    self,
    function,
    experiment,
    *parameters,
    nb_jobs=1,
    progress='d',
    log_file_name='',
    mail_interval=0
    ):
    r"""iterate over the setting set and run the function given as parameter.

    This function is wrapped by :meth:`doce.experiment.Experiment.do`,
    which should be more convenient to use. Please refer to this method for usage.

    Parameters
    ----------

    function : function(:class:`~doce.Plan`, :class:`~doce.experiment.Experiment`, \*parameters)
      operates on a given setting within the experiment environnment with optional parameters.

    experiment:
      an :class:`~doce.experiment.Experiment` object

    *parameters : any type (optional)
      parameters to be given to the function.

    nb_jobs : int > 0 (optional)
      number of jobs.

      If nb_jobs = 1, the setting set is browsed sequentially
      in a depth first traversal of the settings tree (default).

      If nb_jobs > 1, the settings set is browsed randomly,
      and settings are distributed over the different processes.

    progress : str (optional)
      display progress of scheduling the setting set.

      If str has an m, show the selector of the current setting.
      If str has an d, show a textual description of the current setting (default).

    log_file_name : str (optional)
      path to a file where potential errors will be logged.

      If empty, the execution is stopped on the first faulty setting (default).

      If not empty, the execution is not stopped on a faulty setting,
      and the error is logged in the log_file_name file.

    See Also
    --------

    doce.experiment.Experiment.perform

    """
    nb_failed = 0
    if log_file_name:
      logging.basicConfig(filename=log_file_name,
                level=logging.DEBUG,
                format='%(levelname)s: %(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S')
    
      
    if progress:
      print('Number of settings: '+str(len(self)))

    if nb_jobs>1 or nb_jobs<0:
      from joblib import Parallel, delayed
      Parallel(n_jobs=nb_jobs, require='sharedmem')(delayed(setting.perform)(
        function,
        experiment,
        log_file_name,
        *parameters
        ) for setting in self)
    else:
      start_time = time.time()
      step_time = start_time
      with tqdm(total=len(self), disable = progress == '') as progress_bar:
        for setting_index, setting in enumerate(self):
          description = ''
          if nb_failed:
            description = f'[failed: {str(nb_failed)}]'
          if 'm' in progress:
            description += str(self._settings[setting_index])+' '
          if 'd' in progress:
            description += setting.identifier()
          progress_bar.set_description(description)
          if function:
            nb_failed += setting.perform(function, experiment, log_file_name, *parameters)
          else:
            print(setting)
          delay = (time.time()-step_time)
          if mail_interval>0 and setting_index<len(self)-1  and delay/(60**2) > mail_interval :
            step_time = time.time()
            percentage = int((setting_index+1)/len(self)*100)
            duration = time.strftime('%dd %Hh %Mm %Ss', time.gmtime(step_time-start_time))
            message = f'{percentage}% of settings done: {setting_index+1} over {len(self)} <br>Time elapsed: {duration}'
            experiment.send_mail(f'progress {percentage}% ', message)
          progress_bar.update(1)
    return nb_failed

  def check(self):
    for factor in self._factors:
      if '=' in factor or '+' in factor:
        print('Error: = and + are not allowed for naming factors')
        raise ValueError

  def order_factor(self, order):
    p = {}
    factors = [self.factors()[i] for i in order]
    for f in factors:
      p[f] = getattr(self, f)
    return Plan(self.name, **p)
  
  def get_name(self):
    return self._name
  
  def select(
    self,
    selector=None,
    volatile=False,
    prune=True
    ):
    """set the selector.

  	This method sets the internal selector to the selector given as parameter.
    Once set, iteration over the setting set is limited to the settings
    that can be reached according to the definition of the selector.

  	Parameters
  	----------

    selector: list of list of int or list of int or list of dict
     a :term:`selector

    volatile: bool
      if True, the selector is disabled after a complete iteration over the setting set.

      If False, the selector is saved for further iterations.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan()
    >>> p.f1=['a', 'b', 'c']
    >>> p.f2=[1, 2, 3]

    >>> # doce allows two ways of defining the selector. The first one is dict based:
    >>> for setting in p.select([{'f1':'b', 'f2':[1, 2]}, {'f1':'c', 'f2':[3]}]):
    ...  print(setting)
    f1=b+f2=1
    f1=b+f2=2
    f1=c+f2=3

    >>> # The second one is list based. In this example, we select the settings with
    >>> # the second modality of the first factor, and with the first modality of the second factor
    >>> for setting in p.select([1, 0]):
    ...  print(setting)
    f1=b+f2=1
    >>> # select the settings with all the modalities of the first factor,
    >>> # and the second modality of the second factor
    >>> for setting in p.select([-1, 1]):
    ...  print(setting)
    f1=a+f2=2
    f1=b+f2=2
    f1=c+f2=2
    >>> # the selection of all the modalities of the remaining factors can be conveniently expressed
    >>> for setting in p.select([1]):
    ...  print(setting)
    f1=b+f2=1
    f1=b+f2=2
    f1=b+f2=3
    >>> # select the settings using 2 selector, where the first selects the settings
    >>> # with the first modalityof the first factor and with the second modality
    >>> # of the second factor, and the second selector selects the settings
    >>> # with the second modality of the first factor,
    >>> # and with the third modality of the second factor
    >>> for setting in p.select([[0, 1], [1, 2]]):
    ...  print(setting)
    f1=a+f2=2
    f1=b+f2=3
    >>> # the latter expression may be interpreted as the selection of the settings with
    >>> # the first and second modalities of the first factor and with second and
    >>> # third modality of the second factor. In that case, one needs to add a -1
    >>> # at the end of the selector (even if by doing so the length of the selector
    >>> # is larger than the number of factors)
    >>> for setting in p.select([[0, 1], [1, 2], -1]):
    ...  print(setting)
    f1=a+f2=2
    f1=a+f2=3
    f1=b+f2=2
    f1=b+f2=3
    >>> # if volatile is set to False (default) when the selector is set
    >>> # and the setting set iterated, the setting set stays ready for another iteration.
    >>> for setting in p.select([0, 1]):
    ...  pass
    >>> for setting in p:
    ...  print(setting)
    f1=a+f2=2
    >>> # if volatile is set to True when the selector is set and the setting set iterated,
    >>> # the setting set is reinitialized at the second iteration.
    >>> for setting in p.select([0, 1], volatile=True):
    ...  pass
    >>> for setting in p:
    ...  print(setting)
    f1=a+f2=1
    f1=a+f2=2
    f1=a+f2=3
    f1=b+f2=1
    f1=b+f2=2
    f1=b+f2=3
    f1=c+f2=1
    f1=c+f2=2
    f1=c+f2=3
    >>> # if volatile was set to False (default) when the selector was first set
    >>> # and the setting set iterated, the complete set of settings can be reached
    >>> # by calling selector with no parameters.
    >>> for setting in p.select([0, 1]):
    ...  pass
    >>> for setting in p.select():
    ...  print(setting)
    f1=a+f2=1
    f1=a+f2=2
    f1=a+f2=3
    f1=b+f2=1
    f1=b+f2=2
    f1=b+f2=3
    f1=c+f2=1
    f1=c+f2=2
    f1=c+f2=3
    """
    selector = self.__format__(selector)

    self._selector = selector
    self._selector_volatile = volatile
    self._prune_selector = prune
    return self

  def factors(
    self
    ):
    """returns the names of the factors.

  	Returns the names of the factors as a list of strings.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan('')
    >>> p.f1=['a', 'b']
    >>> p.f2=[1, 2]
    >>> p.f3=[0, 1]

    >>> print(p.factors())
    ['f1', 'f2', 'f3']
    """
    return self._factors

  def nb_modalities(
    self,
    factor
    ):
    """returns the number of :term:`modalities<modality>` for a given :term:`factor`.

  	Returns the number of :term:`modalities<modality>`
    for a given :term:`factor` as an integer value.

  	Parameters
  	----------

    factor: int or str
      if int, considered as the index inside an array of the factors
      sorted by order of definition.

      If str, the name of the factor.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan('')
    >>> p.one = ['a', 'b']
    >>> p.two = list(range(10))

    >>> print(p.nb_modalities('one'))
    2
    >>> print(p.nb_modalities(1))
    10
    """
    if isinstance(factor, int):
      factor = self.factors()[factor]
    return len(object.__getattribute__(self, factor))

  def clean_h5(
    self,
    path,
    reverse=False,
    force=True,
    keep=False,
    setting_encoding=None,
    archive_path='',
    verbose=0):
    """clean a h5 data sink by considering the settings set.

  	This method is more conveniently used by considering
    the method :meth:`doce.experiment._experiment.clean_data_sink,
    please see its documentation for usage.
    """
    import tables as tb
    import warnings
    from tables import NaturalNameWarning
    warnings.filterwarnings('ignore', category=NaturalNameWarning)

    if not setting_encoding:
      # setting_encoding = {'factor_separator':'_', 'modality_separator':'_'}
      setting_encoding = {}

    changed = False

    if archive_path:
      sh.copyfile(path, archive_path)
      self.clean_h5(
        path=archive_path,
        reverse = not reverse,
        force=True,
        keep=False,
        setting_encoding=setting_encoding,
        archive_path='',
        verbose=verbose)
      print(f'Archived data should be available at: {archive_path}')
    if not keep:
      h_5 = tb.open_file(path, mode='a')
      groups = []
      if reverse:
        ids = [setting.identifier(**setting_encoding) for setting in self]
        for group in h_5.iter_nodes('/'):
          if group._v_name not in ids:
            groups.append(group._v_name)
      else:
        for setting in self:
          group_name = setting.identifier(**setting_encoding)
          if h_5.root.__contains__(group_name):
            groups.append(group_name)
      if not force:
        print(f'About to remove {len(groups)} settings.')
      if not force and not groups:
        print('No settings to remove.')
        return
      if not force and eu.query_yes_no('List them ?'):
        [print(g) for g in groups]
      if force or eu.query_yes_no('Proceed to removal ?'):
        changed = True
        [h_5.remove_node(h_5.root, g, recursive=True) for g in groups]
      
      h_5.close()
 
      # repack
      if not changed:
        outfilename = path+'Tmp'
        command = f'ptrepack -o {path} {outfilename}'
        if not force:
          print('Original size is %.2f MB' % (float(os.stat(path).st_size)/1024**2))
          print('Repacking ... (requires ptrepack utility)')

        subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if os.path.exists(outfilename):
          if not force:
            print('Repacked size is %.2f MB' % (float(os.stat(outfilename).st_size)/1024**2))
          os.rename(outfilename, path)
        else:
          print('Call to ptrepack failed. Is ptrepack available ?')


  def clean_data_sink(
    self,
    path,
    reverse=False,
    force=False,
    keep=False,
    wildcard='*',
    setting_encoding=None,
    archive_path='',
    verbose=0
    ):
    """clean a data sink by considering the settings set.

  	This method is more conveniently used by
    considering the method :meth:`doce.experiment._experiment.clean_data_sink,
    please see its documentation for usage.
    """
    if not setting_encoding:
      setting_encoding = {}
    path = os.path.expanduser(path)
    if path.endswith('.h5'):
      setting_encoding={} #'factor_separator':'_', 'modality_separator':'_'}
      self.clean_h5(path, reverse, force, keep, setting_encoding, archive_path, verbose)
    else:
      file_names = []
      for setting in self:
        if verbose:
          print('search path: '+path+'/'+setting.identifier(**setting_encoding)+wildcard)
        for output_file in glob.glob(path+'/'+setting.identifier(**setting_encoding)+wildcard):
          file_names.append(output_file)
      if reverse:
        complete = []
        for output_file in glob.glob(path+'/'+wildcard):
          complete.append(output_file)
        # print(file_names)
        file_names = [i for i in complete if i not in file_names]
      #   print(complete)
      file_names = set(file_names)
      if verbose:
        print('Selected files')
        print(file_names)
      # print(len(file_names))
      if archive_path:
        if keep:
          action = 'copy '
        else:
          action = 'move '
        destination = ' to '+archive_path+' '
      elif not force:
        print('''INFORMATION: setting path.archive allows you to move
          the unwanted files to the archive path and not delete them.''')
        destination = ''
        action = 'remove '
      if file_names:
        if not force and eu.query_yes_no(f'List the {str(len(file_names))} files ?'):
          print("\n".join(file_names))
        if force or eu.query_yes_no(
          f'About to {action}{str(len(file_names))} files from {path}{destination} \n Proceed?'
          ):
          for file_name in file_names:
            if archive_path:
              if keep:
                sh.copyfile(file_name, archive_path+'/'+os.path.basename(file_name))
              else:
                os.rename(file_name, archive_path+'/'+os.path.basename(file_name))
            else:
              os.remove(file_name)
      else:
        print('no files found.')

  def merge(self, plans):
    # build temporary plan
    tmp = Plan('merged')
    for plan in plans:
      for factor in plan.factors():
        setattr(tmp, factor, np.empty([0]))
        if hasattr(plan._default, factor):
          if (hasattr(tmp._default, factor) and
            getattr(plan._default, factor) != getattr(tmp._default, factor)
            ):
            print(getattr(tmp._default, factor))
            print(f'''While merging factors of the different experiment,
              a conflict of default modalities for the factor {factor} is detected.
              This may lead to an inconsistent behavior.''')
            raise ValueError
          setattr(tmp._default, factor, getattr(plan._default, factor))
            # print(tmp._default)
    for plan in plans:
      for factor in plan.factors():
        for modalities in getattr(plan, factor):
          if len(getattr(tmp, factor))==0 or modalities not in getattr(tmp, factor):
            setattr(tmp, factor, np.append(getattr(tmp, factor), modalities))
    # check if factors are available in every experiment
    have = [True]*len(tmp.factors())
    for factor_index, factor in enumerate(tmp.factors()):
      for plan in plans:
        if not factor in plan.factors():
          have[factor_index] = False
    plan = Plan('merged')
    plan._default = tmp._default
    for factor_index, factor in enumerate(tmp.factors()):
      modalities = getattr(tmp, factor)
      print(modalities)
      if (not isinstance(modalities[0], str) and
          all(np.array([val.is_integer() for val in modalities]))
          ):
        modalities = np.array(modalities, dtype=np.intc)
      setattr(plan, factor, modalities)
      if not have[factor_index] and not hasattr(tmp._default, factor):
        if isinstance(modalities[0], str):
          if '-99999' not in modalities:
            modalities = np.append(modalities, '-99999')
            setattr(plan, factor, modalities)
          plan.default(factor, '-99999')
        if not isinstance(modalities[0], str):
          if -99999 not in modalities:
            modalities = np.append(modalities, -99999)
            setattr(plan, factor, modalities)
          plan.default(factor, -99999)
    return plan

  def as_panda_frame(self):
    """returns a panda frame that describes the Plan object.

  	Returns a panda frame describing the Plan object.
    For ease of definition of a selector to select some settings,
    the columns and the rows of the panda frame are numbered.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan('')
    >>> p.one = ['a', 'b']
    >>> p.two = list(range(10))

    >>> print(p)
      0  one: ['a' 'b']
      1  two: [0 1 2 3 4 5 6 7 8 9]
    >>> print(p.as_panda_frame())
      Factors  0  1  2  3  4  5  6  7  8  9
    0    one  a  b
    1    two  0  1  2  3  4  5  6  7  8  9
    """
    import pandas as pd

    max_modalities = 1
    for factor in self._factors:
      if isinstance(getattr(self, factor), list):
        max_modalities = max(max_modalities, len(getattr(self, factor)))
      elif isinstance(getattr(self, factor), np.ndarray):
        max_modalities = max(max_modalities, len(getattr(self, factor)))

    table = []
    for factor in self._factors:
      line = []
      line.append(factor)
      for modality_index in range(max_modalities):
        if ((isinstance(getattr(self, factor), list) or
            isinstance(getattr(self, factor), np.ndarray)) and
            len(getattr(self, factor)) > modality_index
            ) :
          modality = str(getattr(self, factor)[modality_index])
          if (hasattr(self._default, factor) and
            getattr(self._default, factor) == getattr(self, factor)[modality_index]
            ):
            if modality == str(-99999) or modality == str(-99999.0):
              modality = '*'
            else: 
              modality = '*'+modality+'*'
          line.append(modality)
        elif modality_index<1:
          line.append(getattr(self, factor))
        else:
          line.append('')
      table.append(line)
    columns = []
    columns.append('Factors')
    for modality_index in range(max_modalities):
      columns.append(modality_index)
    return pd.DataFrame(table, columns = columns)

  def constant_factors(self, selector):
    self.select(selector)
    message = str(len(self))+' settings'
    constant_factor = [ [] for _ in range(len(self._factors)) ]
    for factor_selector in self._expanded_selector:
      for factor_index, _ in enumerate(self._factors):
        if factor_selector[factor_index]:
          constant_factor[factor_index] = list(
              set(constant_factor[factor_index])|
              set(factor_selector[factor_index])
              )

    constant_factors = ''
    for factor_index, factor in enumerate(self._factors):
      if len(constant_factor[factor_index]) == 1:
        constant_factors+=factor+', '
    if constant_factors:
      message += ' with constant factors : '
      message += constant_factors[:-2]
    return message

  def expand_selector(self, selector, factor):

    selector = self.__format__(selector)
    factor_index = self.factors().index(factor)

    if len(selector)<=factor_index:
      for _ in range(1+factor_index-len(selector)):
        selector.append(-1)

    expanded_selector = []
    for factor_index, factor_selector in enumerate(selector):
      if factor_selector==-1:
        expanded_selector.append(list(range(len(getattr(self, self.factors()[factor_index])))))
      else:
        expanded_selector.append(factor_selector)
    expanded_selector.append(-1)

    return expanded_selector

  def _dict2list(self, dict_selector):
    """convert dict based selector to list based selector

    """
    integer_selectors = []
    # print(selectors)
    # if ';' in dict_selector[0]:
    #   new_selector = []
    #   print(dict_selector[0].split(';'))
    #   for selector in dict_selector[0].split(';'):
    #     selector_int = self._str2list([selector])
    #     integer_selectors.append(selector_int[0])
    # else:
    for selector in dict_selector:
      integer_selector = [-1]*len(self._factors)
      for factor in selector.keys():
        if factor in self._factors:
          if isinstance(selector[factor], list):
            factor_selector_integer = []
            for factor_selector in selector[factor]:
              if factor_selector in getattr(self, factor):
                factor_selector_integer.append(list(getattr(self, factor)).index(factor_selector))
              else:
                print('Error: '+str(factor_selector)+' is not a modality of factor '+factor+'.')
            integer_selector[self._factors.index(factor)] = factor_selector_integer
          else:
            if selector[factor] in getattr(self, factor):
              integer_selector[self._factors.index(factor)] = list(getattr(self, factor)).index(selector[factor])
        else:
          print('Error: '+factor+' is not a factor.')
      integer_selectors.append(integer_selector)

    return integer_selectors

  def _str2list(
    self,
    selector_str,
    factor_separator = '+',
    modality_identifier = '='
    ):
    """convert string based selector to list based selector

    """
    selector = []
    # print(selectors)
    if ',' in selector_str[0]:
      new_selector = []
      for selector in selector_str[0].split(','):
        selector_int = self._str2list([selector])
        new_selector.append(selector_int[0])
      selector = new_selector
    else:
      # for factor_selector in selectors:
      selector = [-1]*len(self._factors)
      factor_modality_pairs = selector_str[0].split(factor_separator)
      for factor_modality_pair in factor_modality_pairs:
        factor_modality_pair_split = factor_modality_pair.split(modality_identifier)
        factor = factor_modality_pair_split[0]
        modality = factor_modality_pair_split[1]
        if factor in self._factors:
          reference_modality_string = []
          for reference_modality in list(getattr(self, factor)):
            reference_modality_string.append(str(reference_modality))
          if modality in reference_modality_string:
            selector[self._factors.index(factor)] = reference_modality_string.index(modality)
          else:
            raise Exception(f'Error: {modality} is not a modality of factor {factor}.')
        else:
          raise Exception(f'Error: {factor} is not a factor.')
      selector = [selector]
    return selector

  def _check_selector(self, selectors):
    check=True
    for selector in selectors:
      for factor_index, factor_selector in enumerate(selector):
        if factor_index<len(self._factors):
          # print(type(getattr(self, self._factors[factor_index])))
          nb_modalities = len(np.atleast_1d(getattr(self, self._factors[factor_index])))
          if factor_selector != -1:
            for factor_selector_modality in factor_selector:
              if factor_selector_modality+1 > nb_modalities:
                print(f'Error: factor {str(self._factors[factor_index])} only has {str(nb_modalities)} modalities.')
                print(f'Requested modality is {str(factor_selector_modality)}')
                check = False
        elif factor_selector != -1:
          print('''Warning: the selector is longer than the number of factors.
            Doce takes this last element into account only if it is equal to -1 
            (see the documentation of the Plan.select() method).'''
          )

    return check

  def __str__(self):
    plan_description = ''
    for factor_index, factor in enumerate(self._factors):
      plan_description+= f'  {str(factor_index)}  {factor}: {str(self.__getattribute__(factor))}\n'
    return plan_description[:-1]

  def check_length(self):
    max_length = 0
    for factor in self._factors:
      max_length_factor = 0
      for modality in self.__getattribute__(factor):
        if len(str(modality)) > max_length:
          max_length_factor = len(str(modality))
      max_length += max_length_factor + 2
    if max_length > 220:
      print('Considering this plan, the setting description of maximal length is above 220 caracters.')
      print('This may reach the file naming size limit of your file system.')
      print('This will be an issue if you consider npy storage.')
      print('')
      print('Set _check_setting_length to False of your experiment to discard this warning.')
    


  def __setattr__(
    self,
    name,
    value
    ):
    if not hasattr(self, name) and name[0] != '_':
      self._factors.append(name)
    if hasattr(self, name) and isinstance(inspect.getattr_static(self, name), types.FunctionType):
      raise Exception(f'the attribute {name} is shadowing a builtin function')
    if name == '_selector' or name[0] != '_':
      self._changed = True
    if (name[0] != '_' and
        ((isinstance(value, list) and value) or
        isinstance(value, np.ndarray) and value.size) and
        name not in self._non_singleton
        ):
      self._non_singleton.append(name)
    if name[0] != '_' and type(value) not in {list, np.ndarray} :
      value = [value]
    if name[0] != '_' and type(value) not in {np.ndarray, Plan}:
      if value and not all(isinstance(x, type(value[0])) for x in value):
        raise Exception(
          f'All the modalities of the factor {name} must be of the same type (str, int, bool, or float)')
      if value and isinstance(value[0], str):
        value = np.array(value)
      # elif value and isinstance(value[0], bool):
      #   value = np.array(value, dtype=bool)
      elif value and isinstance(value[0], int) or isinstance(value[0], bool):
        value = np.array(value, dtype=np.intc)
      elif value and isinstance(value[0], float):
        value = np.array(value, dtype=np.float)
    return object.__setattr__(self, name, value)

  def __delattr__(
    self,
    name):

    self._changed = True
    if hasattr(self, name) and name[0] != '_':
      self._factors.remove(name)
      if name in self._non_singleton:
        self._non_singleton.remove(name)
    return object.__delattr__(self, name)

  def __iter__(
    self
    ):

    self.__set_settings__()
    self._current_setting = 0
    return self

  def __next__(
    self
    ):

    if self._current_setting == len(self._settings):
      if self._selector_volatile:
        self._selector = None
      raise StopIteration
    else:
      self._setting = self._settings[self._current_setting]
      self._current_setting += 1
      return es.Setting(self)

  def __getitem__(self, index):
    self.__set_settings__()
    return  self


  def __len__(
    self
    ):
    self.__set_settings__()
    return len(self._settings)

  def __set_settings__(
    self
    ):
    if self._changed:
      settings = []
      selectors = copy.deepcopy(self._selector)
      self._setting = None
      # selector = copy.deepcopy(selector)
      nb_factors = len(self.factors())
      if selectors is None or len(selectors)==0 or (len(selectors)==1 and len(selectors)==0) :
        selectors = [[-1]*nb_factors]
      if isinstance(selectors, list) and not all(isinstance(x, list) for x in selectors):
        selectors = [selectors]

      for selector_index, selector in enumerate(selectors):
        if len(selector) < nb_factors:
          selectors[selector_index] = selector+[-1]*(nb_factors-len(selector))
        for factor_selector_index, factor_selector in enumerate(selector):
          if not isinstance(factor_selector, list) and factor_selector > -1:
            selectors[selector_index][factor_selector_index] = [factor_selector]
      # prune repeated entries
      for selector_index, selector in enumerate(selectors):
        if isinstance(selector, list):
          for factor_selector_index, factor_selector in enumerate(selector):
            if isinstance(factor_selector, list):
              selector[factor_selector_index] = list(dict.fromkeys(factor_selector))
      self._expanded_selector = selectors

      if self._check_selector(selectors):
        for selector in selectors:
          # handle -1 in selectors
          for factor_selector_index, factor_selector in enumerate(selector):
            if (isinstance(factor_selector, int) and
                factor_selector == -1 and
                factor_selector_index<len(self.factors())
                ):
              modalities = self.__getattribute__(self.factors()[factor_selector_index])
              if isinstance(modalities, list) or isinstance(modalities, np.ndarray):
                selector[factor_selector_index] = list(range(len(np.atleast_1d(modalities))))
              else:
                selector[factor_selector_index] = [0]

          settings_from_selector = self.__set_settings_selector__(selector, 0)
          if all(isinstance(setting_from_selector, list) for setting_from_selector in settings_from_selector):
            for setting_from_selector in settings_from_selector:
              settings.append(setting_from_selector)
          else:
            settings.append(settings_from_selector)
        pruned_settings = [k for k,v in groupby(sorted(settings))]
        if self._prune_selector and len(pruned_settings) < len(settings):
          settings = pruned_settings
        self._changed = False
        self._settings = settings

  def __set_settings_selector__(self, selector, done):
    if done == len(selector):
      return []

    last_settings = self.__set_settings_selector__(selector, done+1)
    if isinstance(selector[done], list):
      settings = []
      for modalities in selector[done]:
        if len(last_settings) > 0:
          for last_setting in last_settings:
            if isinstance(last_setting, list):
              last_setting = list(last_setting)
            else:
              last_setting = [last_setting]
            last_setting.insert(0, modalities)
            settings.append(last_setting)
        else:
          setting = list(last_settings)
          setting.insert(0, modalities)
          settings.append(setting)
    else:
      settings = last_settings
      if len(settings) > 0 and all(isinstance(setting, list) for setting in settings):
        for setting in settings:
          setting.insert(0, selector[done])
      else:
        settings.insert(0, selector[done])
    return settings

  def __format__(self, selector):
    if selector and (isinstance(selector, str) or isinstance(selector, dict)):
      selector = [selector]
    if selector and any(isinstance(val, str) for val in selector):
      selector = self._str2list(selector)
    elif selector and any(isinstance(val, dict) for val in selector):
      selector = self._dict2list(selector)
    return selector

if __name__ == '__main__':
  import doctest
  doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
