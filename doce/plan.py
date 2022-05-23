import os
import shutil as sh
import inspect
import types
import numpy as np

import copy
import glob
import doce.util as eu
import doce.setting as es
import logging
import time
from itertools import groupby
from subprocess import call

if eu.in_notebook():
    from tqdm.notebook import tqdm as tqdm
else:
    from tqdm import tqdm as tqdm

class Plan():
  """stores the different factors of the doce experiment.

  This class stores the different factors of the doce experiments. For each factor, the set of different modalities can be expressed as a list or a numpy array.

  To browse the setting set defined by the Plan object, one must iterate over the Plan object.

  Examples
  --------

  >>> import doce

  >>> p = doce.Plan()
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
  def __init__(self, **factors):
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

    p = doce.Plan()

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
      # if generic_default_modality_warning and len([item for item in getattr(self, factor) if item in [0, 'none']]):
      #   print('Setting an explicit default modality to factor '+factor+' should be handled with care as the factor already as an implicit default modality (O or none). This may lead to loss of data. Ensure that you have the flag <hide_none_and_zero> set to False when using method identifier() if (O or none). You can remove this warning by setting the flag <force> to True.')
      if modality not in getattr(self, factor):
        print('The default modality of factor '+factor+' should be available in the set of modalities.')
        raise ValueError
      self._default.__setattr__(factor, modality)
    else:
      print('Please set the factor '+factor+' before choosing its default modality.')
      raise ValueError

  def perform(
    self,
    function,
    experiment,
    *parameters,
    nb_jobs=1,
    progress='d',
    log_file_name='',
    mail_interval=0):
    """iterate over the setting set and run the function given as parameter.

    This function is wrapped by :meth:`doce.experiment.Experiment.do`, which should be more convenient to use. Please refer to this method for usage.

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

      If nb_jobs = 1, the setting set is browsed sequentially in a depth first traversal of the settings tree (default).

      If nb_jobs > 1, the settings set is browsed randomly, and settings are distributed over the different processes.

    progress : str (optional)
      display progress of scheduling the setting set.

      If str has an m, show the selector of the current setting.
      If str has an d, show a textual description of the current setting (default).

    log_file_name : str (optional)
      path to a file where potential errors will be logged.

      If empty, the execution is stopped on the first faulty setting (default).

      If not empty, the execution is not stopped on a faulty setting, and the error is logged in the log_file_name file.

    See Also
    --------

    doce.experiment.Experiment.do

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
      result = Parallel(n_jobs=nb_jobs, require='sharedmem')(delayed(setting.perform)(function, experiment, log_file_name, *parameters) for setting in self)
    else:
      start_time = time.time()
      step_time = start_time
      with tqdm(total=len(self), disable = progress == '') as t:
        for iSetting, setting in enumerate(self):
            description = ''
            if nb_failed:
                description = '[failed: '+str(nb_failed)+']'
            if 'm' in progress:
              description += str(self._settings[iSetting])+' '
            if 'd' in progress:
              description += setting.identifier()
            t.set_description(description)
            if function:
              nb_failed += setting.perform(function, experiment, log_file_name, *parameters)
            else:
                print(setting)
            delay = (time.time()-step_time)
            if mail_interval>0 and iSetting<len(self)-1  and delay/(60**2) > mail_interval :
              step_time = time.time()
              percentage = int((iSetting+1)/len(self)*100)
              message = '{}% of settings done: {} over {} <br>Time elapsed: {}'.format(percentage, iSetting+1, len(self), time.strftime('%dd %Hh %Mm %Ss', time.gmtime(step_time-start_time)))
              experiment.send_mail('progress {}% '.format(percentage), message)
            t.update(1)
    return nb_failed

  def check(self):
   for factor in self._factors:
     if '=' in factor or '+' in factor:
       print('Error: = and + are not allowed for naming factors')
       raise ValueError
     # modalities = str(getattr(self, factor))
     # if '=' in factor or '+' in modalities:
     #   print('Error: = and + are not allowed for naming modalities')
     #   raise ValueError

  def select(
    self,
    selector=None,
    volatile=False,
    prune=True
    ):
    """set the selector.

  	This method sets the internal selector to the selector given as parameter. Once set, iteration over the setting set is limited to the settings that can be reached according to the definition of the selector.

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

    >>> # The second one is list based. In this example, we select the settings with the second modality of the first factor, and with the first modality of the second factor
    >>> for setting in p.select([1, 0]):
    ...  print(setting)
    f1=b+f2=1
    >>> # select the settings with all the modalities of the first factor, and the second modality of the second factor
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
    >>> # select the settings using 2 selector, where the first selects the settings with the first modality of the first factor and with the second modality of the second factor, and the second selector selects the settings with the second modality of the first factor, and with the third modality of the second factor
    >>> for setting in p.select([[0, 1], [1, 2]]):
    ...  print(setting)
    f1=a+f2=2
    f1=b+f2=3
    >>> # the latter expression may be interpreted as the selection of the settings with the first and second modalities of the first factor and with second and third modalities of the second factor. In that case, one needs to add a -1 at the end the selector (even if by doing so the length of the selector is larger than the number of factors)
    >>> for setting in p.select([[0, 1], [1, 2], -1]):
    ...  print(setting)
    f1=a+f2=2
    f1=a+f2=3
    f1=b+f2=2
    f1=b+f2=3
    >>> # if volatile is set to False (default) when the selector is set and the setting set iterated, the setting set stays ready for another iteration.
    >>> for setting in p.select([0, 1]):
    ...  pass
    >>> for setting in p:
    ...  print(setting)
    f1=a+f2=2
    >>> # if volatile is set to True when the selector is set and the setting set iterated, the setting set is reinitialized at the second iteration.
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
    >>> # if volatile was set to False (default) when the selector was first set and the setting set iterated, the complete set of settings can be reached by calling selector with no parameters.
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

    >>> p = doce.Plan()
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

  	Returns the number of :term:`modalities<modality>` for a given :term:`factor` as an integer value.

  	Parameters
  	----------

    factor: int or str
      if int, considered as the index inside an array of the factors sorted by order of definition.

      If str, the name of the factor.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan()
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
    force=False,
    keep=False,
    setting_encoding={'factor_separator':'_', 'modality_separator':'_'},
    archive_path='',
    verbose=0):
    """clean a h5 data sink by considering the settings set.

  	This method is more conveniently used by considering the method :meth:`doce.experiment._experiment.clean_data_sink, please see its documentation for usage.
    """
    import tables as tb

    if archive_path:
      print(path)
      print(archive_path)
      sh.copyfile(path, archive_path)
      self.clean_h5(
        path=archive_path,
        reverse = not reverse,
        force=True,
        keep=False,
        setting_encoding=setting_encoding,
        archive_path='',
        verbose=verbose)
    if not keep:
      h5 = tb.open_file(path, mode='a')
      if reverse:
        ids = [setting.identifier(**setting_encoding) for setting in self]
        for g in h5.iter_nodes('/'):
          if g._v_name not in ids:
            h5.remove_node(h5.root, g._v_name, recursive=True)
      else:
        for setting in self:
          group_name = setting.identifier(**setting_encoding)
          if h5.root.__contains__(group_name):
            h5.remove_node(h5.root, group_name, recursive=True)
      h5.close()
      if verbose:
        print('repacking')
      # repack
      outfilename = path+'Tmp'
      command = ["ptrepack", "-o", "--chunkshape=auto", "--propindexes", path, outfilename]
      if verbose:
        print('Original size is %.2f_mi_b' % (float(os.stat(path).st_size)/1024**2))
      if call(command) != 0:
        print('Unable to repack. Is ptrepack installed ?')
      else:
        if verbose:
          print('Repacked size is %.2f_mi_b' % (float(os.stat(outfilename).st_size)/1024**2))
        os.rename(outfilename, path)


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

  	This method is more conveniently used by considering the method :meth:`doce.experiment._experiment.clean_data_sink, please see its documentation for usage.
    """
    if not setting_encoding:
      setting_encoding = {}
    path = os.path.expanduser(path)
    if path.endswith('.h5'):
      setting_encoding={'factor_separator':'_', 'modality_separator':'_'}
      self.clean_h5(path, reverse, force, keep, setting_encoding, archive_path, verbose)
    else:
      file_names = []
      for setting in self:
        if verbose:
          print('search path: '+path+'/'+setting.identifier(**setting_encoding)+wildcard)
        for f in glob.glob(path+'/'+setting.identifier(**setting_encoding)+wildcard):
            file_names.append(f)
      if reverse:
        complete = []
        for f in glob.glob(path+'/'+wildcard):
          complete.append(f)
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
        print('INFORMATION: setting path.archive allows you to move the unwanted files to the archive path and not delete them.')
        destination = ''
        action = 'remove '
      if len(file_names):
        if not force and eu.query_yes_no('List the '+str(len(file_names))+' files ?'):
          print("\n".join(file_names))
        if force or eu.query_yes_no('About to '+action+str(len(file_names))+' files from '+path+destination+' \n Proceed ?'):
          for f in file_names:
            if archive_path:
              if keep:
                sh.copyfile(f, archive_path+'/'+os.path.basename(f))
              else:
                os.rename(f, archive_path+'/'+os.path.basename(f))
            else:
              os.remove(f)
      else:
        print('no files found.')

  def merge(self, plans):
    # build temporary plan
    tmp = Plan()
    for x in plans:
      for f in x.factors():
        setattr(tmp, f, np.empty([0]))
        if hasattr(x._default, f):
          if hasattr(tmp._default, f) and getattr(x._default, f) != getattr(tmp._default, f):
            print(getattr(tmp._default, f))
            print('While merging factors of the different experiment, a conflict of default modalities for the factor '+f+' is detected. This may lead to an inconsistent behavior.')
            raise ValueError
          setattr(tmp._default, f, getattr(x._default, f))
            # print(tmp._default)
    for x in plans:
      for f in x.factors():
        for m in getattr(x, f):
          if len(getattr(tmp, f))==0 or m not in getattr(tmp, f):
            setattr(tmp, f, np.append(getattr(tmp, f), m))
    # check if factors are available in every experiment
    have = [True]*len(tmp.factors())
    for fi, f in enumerate(tmp.factors()):
      for x in plans:
        if not f in x.factors():
          have[fi] = False
    plan = Plan()
    plan._default = tmp._default
    for fi, f in enumerate(tmp.factors()):
      m = getattr(tmp, f)
      if not isinstance(m[0], str) and all(np.array([val.is_integer() for val in m])):
        m = np.array(m, dtype=np.intc)
      setattr(plan, f, m)
      if not have[fi] and not hasattr(tmp._default, f):
        if isinstance(m[0], str):
          if 'none' not in m:
            m = np.insert(m, 0, 'none')
            setattr(plan, f, m)
          plan.default(f, 'none')
        if not isinstance(m[0], str):
          if 0 not in m:
            m = np.insert(m, 0, 0)
            setattr(plan, f, m)
          plan.default(f, 0)
    return plan

  def as_panda_frame(self):
    """returns a panda frame that describes the Plan object.

  	Returns a panda frame describing the Plan object. For ease of definition of a selector to select some settings, the columns and the rows of the panda frame are numbered.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan()
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

    l = 1
    for ai, f in enumerate(self._factors):
      if isinstance(getattr(self, f), list):
        l = max(l, len(getattr(self, f)))
      elif isinstance(getattr(self, f), np.ndarray):
        l = max(l, len(getattr(self, f)))

    table = []
    for f in self._factors:
      line = []
      line.append(f)
      for il in range(l):
        if ((isinstance(getattr(self, f), list)) or isinstance(getattr(self, f), np.ndarray)) and len(getattr(self, f)) > il :
          m = str(getattr(self, f)[il])
          if hasattr(self._default, f) and getattr(self._default, f) == getattr(self, f)[il]:
            m = '*'+m+'*'
          line.append(m)
        elif il<1:
          line.append(getattr(self, f))
        else:
          line.append('')
      table.append(line)
    columns = []
    columns.append('Factors')
    for il in range(l):
      columns.append(il)
    return pd.DataFrame(table, columns = columns)

  def constant_factors(self, selector):
    self.select(selector)
    message = str(len(self))+' settings'
    cf = [ [] for _ in range(len(self._factors)) ]
    for m in self._expanded_selector:
      for fi, f in enumerate(self._factors):
        if m[fi]:
          cf[fi] = list(set(cf[fi]) | set(m[fi]))

    cst = ''
    for fi, f in enumerate(self._factors):
      if len(cf[fi]) == 1:
        cst+=f+', '
    if cst:
      message += ' with constant factors : '
      message += cst[:-2]
    return message

  def expand_selector(self, selector, factor):

    selector = self.__format__(selector)
    fi = self.factors().index(factor)

    if len(selector)<=fi:
      for m in range(1+fi-len(selector)):
        selector.append(-1)

    nm = []
    for mi, m in enumerate(selector):
      if m==-1:
        nm.append(list(range(len(getattr(self, self.factors()[mi])))))
      else:
        nm.append(m)
    nm.append(-1)

    return nm

  def _dict2list(self, dict_selector):
    """convert dict based selector to list based selector

    """
    integer_selector_array = []
    for dm in dict_selector:
      m = [-1]*len(self._factors)
      for dmk in dm.keys():
        if dmk in self._factors:
          if isinstance(dm[dmk], list):
            mm = []
            for dmkl in dm[dmk]:
              if dmkl in getattr(self, dmk):
                 mm.append(list(getattr(self, dmk)).index(dmkl))
              else:
                print('Error: '+str(dmkl)+' is not a modality of factor '+dmk+'.')
            m[self._factors.index(dmk)] = mm
          else:
            if dm[dmk] in getattr(self, dmk):
              m[self._factors.index(dmk)] = list(getattr(self, dmk)).index(dm[dmk])
        else:
          print('Error: '+dmk+' is not a factor.')
      integer_selector_array.append(m)

    return integer_selector_array

  def _str2list(self, str_selector, factor_separator = '+', modality_identifier = '='):
    """convert string based selector to list based selector

    """
    selector = []
    # print(str_selector)
    if ',' in str_selector[0]:
      for ss in str_selector[0].split(','):
        s = self._str2list([ss])
        selector.append(s[0])
    else:
      for dm in str_selector:
        m = [-1]*len(self._factors)
        factors = dm.split(factor_separator)
        # factors = sp[0::2]
        # modalities = sp[1::2]
        for dmki, dmk in enumerate(factors):
          dmks = dmk.split(modality_identifier)
          dmk = dmks[0]
          modality = dmks[1]
          if dmk in self._factors:
              # mod = modalities[dmki]
              ref_mod = []
              for am in list(getattr(self, dmk)):
                ref_mod.append(str(am))
              if modality in ref_mod:
                m[self._factors.index(dmk)] = ref_mod.index(modality)
              else:
                print('Error: '+modality+' is not a modality of factor '+dmk+'.')
                return [0]
          else:
            print('Error: '+dmk+' is not a factor.')
            return [0]
        selector = m
    return selector

  def _check_selector(self, selector):
    check=True
    for s in selector:
      for fi, f in enumerate(s):
        if fi<len(self._factors):
          # print(type(getattr(self, self._factors[fi])))
          nm = len(np.atleast_1d(getattr(self, self._factors[fi])))
          if f != -1:
            for fm in f:
              if fm+1 > nm:
                print('Error: factor '+str(self._factors[fi])+' only has '+str(nm)+' modalities. Requested modality '+str(fm))
                check = False
        elif f != -1:
          print('Warning: the selector is longer than the number of factors. Doce takes this last element into account only if it is equal to -1 (see the documentation of the Plan.select() method).')

    return check

  def __str__(self):
    cString = ''
    l = 1
    for ai, f in enumerate(self._factors):
      cString+='  '+str(ai)+'  '+f+': '+str(self.__getattribute__(f))+'\n'
    return cString[:-1]

  def __setattr__(
    self,
    name,
    value
    ):
    if not hasattr(self, name) and name[0] != '_':
      self._factors.append(name)
    if hasattr(self, name) and type(inspect.getattr_static(self, name)) == types.FunctionType:
      raise Exception('the attribute '+name+' is shadowing a builtin function')
    if name == '_selector' or name[0] != '_':
      self._changed = True
    if name[0] != '_' and type(value) in {list, np.ndarray} and len(value)>1 and name not in self._non_singleton:
      self._non_singleton.append(name)
    if name[0] != '_' and type(value) not in {list, np.ndarray} :
      value = [value]
    if name[0] != '_' and type(value) not in {np.ndarray, Plan}:
      if len(value) and not all(isinstance(x, type(value[0])) for x in value):
        raise Exception('All the modalities of the factor '+name+' must be of the same type (str, int, or float)')
      if len(value) and all(isinstance(x, str) for x in value):
        value = np.array(value)
      elif len(value) and all(isinstance(x, int) for x in value):
        value = np.array(value, dtype=np.intc)
      elif len(value) and all(isinstance(x, float) for x in value):
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

  # def __getattribute__(
  #   self,
  #   name
  #   ):
  #
  #   value = object.__getattribute__(self, name)
  #   if name[0] != '_' and self._setting and type(inspect.getattr_static(self, name)) != types._function_type:
  #     idx = self.factors().index(name)
  #     if self._setting[idx] == -2:
  #       value = None
  #     else:
  #       if  type(inspect.getattr_static(self, name)) in {list, np.ndarray} :
  #         try:
  #           value = value[self._setting[idx]]
  #         except index_error:
  #           value = 'null'
  #           print('Error: factor '+name+' have modalities 0 to '+str(len(value)-1)+'. Requested '+str(self._setting[idx]))
  #           raise
  #   return value

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
      selector = copy.deepcopy(self._selector)
      self._setting = None

      selector = copy.deepcopy(selector)
      nb_plans = len(self.factors())
      if selector is None or len(selector)==0 or (len(selector)==1 and len(selector)==0) :
         selector = [[-1]*nb_plans]
      if isinstance(selector, list) and not all(isinstance(x, list) for x in selector):
          selector = [selector]

      for im, m in enumerate(selector):
        if len(m) < nb_plans:
          selector[im] = m+[-1]*(nb_plans-len(m))
        for il, l in enumerate(m):
            if not isinstance(l, list) and l > -1:
                selector[im][il] = [l]
      # prune repeated entries
      for im, m in enumerate(selector):
        if isinstance(m, list):
          for il, l in enumerate(m):
            if isinstance(l, list):
              m[il] = list(dict.fromkeys(l))
      self._expanded_selector = selector

      if self._check_selector(selector):
        for m in selector:
          # handle -1 in selector
          for mfi, mf in enumerate(m):
            if isinstance(mf, int) and mf == -1 and mfi<len(self.factors()):
              attr = self.__getattribute__(self.factors()
              [mfi])
              if isinstance(attr, list) or isinstance(attr, np.ndarray):
                m[mfi] = list(range(len(np.atleast_1d(attr))))
              else:
                m[mfi] = [0]

          s = self.__set_settings_selector__(m, 0)
          if all(isinstance(ss, list) for ss in s):
            for ss in s:
              settings.append(ss)
          else:
            settings.append(s)
        pruned_settings = [k for k,v in groupby(sorted(settings))]
        if self._prune_selector and len(pruned_settings) < len(settings):
          settings = pruned_settings
        self._changed = False
        self._settings = settings

  def __set_settings_selector__(self, selector, done):
    if done == len(selector):
      return []

    s = self.__set_settings_selector__(selector, done+1)
    if isinstance(selector[done], list):
      settings = []
      for mod in selector[done]:
        if len(s) > 0:
          for ss in s:
            if isinstance(ss, list):
                mList = list(ss)
            else:
                mList = [ss]
            mList.insert(0, mod)
            settings.append(mList)
        else:
          mList = list(s)
          mList.insert(0, mod)
          settings.append(mList)
    else:
      settings = s
      if len(settings) > 0 and all(isinstance(ss, list) for ss in settings):
        for ss in settings:
          ss.insert(0, selector[done])
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
