import os
import inspect
import types
import numpy as np
import tables as tb
import pandas as pd
import copy
import glob
import explanes.util as eu
import explanes.setting as es
import traceback
import logging
from joblib import Parallel, delayed
from subprocess import call
import time

if eu.inNotebook():
    from tqdm.notebook import tqdm as tqdm
else:
    from tqdm import tqdm as tqdm

class Factor():
  """stores the different factors of the explanes experiment.

  This class stores the different factors of the explanes experiments. For each factor, the set of different modalities can be expressed as a list or a numpy array.

  To browse the setting set defined by the Factor object, one must iterate over the Factor object.

  Examples
  --------

  >>> import explanes as el

  >>> f = el.factor.Factor()
  >>> f.factor1=[1, 3]
  >>> f.factor2=[2, 4]

  >>> print(f)
    0  factor1: [1, 3]
    1  factor2: [2, 4]

  >>> for setting in f:
  ...   print(setting)
  factor1 1 factor2 2
  factor1 1 factor2 4
  factor1 3 factor2 2
  factor1 3 factor2 4
  """
  def __init__(self):
    self._setting = None
    self._changed = False
    self._currentSetting = 0
    self._settings = []
    self._mask = None
    self._nonSingleton = []
    self._factors = []
    self._default = types.SimpleNamespace()
    self._maskVolatile = True

  def default(
    self,
    factor,
    modality,
    genericDefaultModalityWarning=True
    ):
    """set the default modality for the specified factor.

  	Set the default modality for the specified factor.

  	Parameters
  	----------

    factor: str

    modality: str

    genericDefaultModalityWarning: bool (optional)

      if True,  print a warning if a default value is a generic default value is already in the set of modalities for this factor (default).

      If False, do not print the warning.

  	See Also
  	--------

    explanes.factor.Factor.id

  	Examples
  	--------

    """
    if hasattr(self, factor):
      if not genericDefaultModalityWarning and any(item == getattr(self, factor) for item in [0, 'none']):
        print('Setting an explicit default modality to factor '+name+' should be handled with care as the factor already as an implicit default modality (O or none). This may lead to loss of data. Ensure that you have the flag <hideNoneAndZero> set to False when using method id() if (O or none). You can remove this warning by setting the flag <force> to True.')
      if modality not in getattr(self, factor):
        print('The default modality of factor '+factor+' should be available in the set of modalities.')
        raise ValueError
      self._default.__setattr__(factor, modality)
    else:
      print('Please set the factor '+factor+' before choosing its default modality.')
      raise ValueError

  def do(
    self,
    function,
    experiment,
    *parameters,
    nbJobs=1,
    progress=True,
    logFileName='',
    mailInterval=0):
    """iterate over the setting set and run the function given as parameter.

    This function is wrapped by :meth:`explanes.experiment.Experiment.do`, which should be more convenient to use. Please refer to this method for usage.

    Parameters
    ----------

    function : function(:class:`~explanes.factor.Factor`, :class:`~explanes.experiment.Experiment`, \*parameters)
      operates on a given setting within the experiment environnment with optional parameters.

    experiment:
      an :class:`~explanes.experiment.Experiment` object

    *parameters : any type (optional)
      parameters to be given to the function.

    nbJobs : int > 0 (optional)
      number of jobs.

      If nbJobs = 1, the setting set is browsed sequentially in a depth first traversal of the settings tree (default).

      If nbJobs > 1, the settings set is browsed randomly, and settings are distributed over the different processes.

    progress : bool (optional)
      display progress of scheduling the setting set.

      If True, use tqdm to display progress (default).

      If False, do not display progress.

    logFileName : str (optional)
      path to a file where potential errors will be logged.

      If empty, the execution is stopped on the first faulty setting (default).

      If not empty, the execution is not stopped on a faulty setting, and the error is logged in the logFileName file.

    See Also
    --------

    explanes.experiment.Experiment.do

    """
    nbFailed = 0
    if logFileName:
      logging.basicConfig(filename=logFileName,
                level=logging.DEBUG,
                format='%(levelname)s: %(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S')
    if progress:
      print('Number of settings: '+str(len(self)))
    if nbJobs>1 or nbJobs<0:
      # print(nbJobs)
      result = Parallel(n_jobs=nbJobs, require='sharedmem')(delayed(setting.do)(function, experiment, logFileName, *parameters) for setting in self)
    else:
      startTime = time.time()
      stepTime = startTime
      with tqdm(total=len(self), disable= not progress) as t:
        for iSetting, setting in enumerate(self):
            description = ''
            if nbFailed:
                description = '[failed: '+str(nbFailed)+']'
            description += str(setting)
            t.set_description(description)
            if function:
              nbFailed += setting.do(function, experiment, logFileName, *parameters)
            else:
                print(setting)
            delay = (time.time()-stepTime)
            if mailInterval>0 and iSetting<len(self)-1  and delay/(60**2) > mailInterval :
              stepTime = time.time()
              percentage = int((iSetting+1)/len(self)*100)
              message = '{}% of settings done: {} over {} <br>Time elapsed: {}'.format(percentage, iSetting+1, len(self), time.strftime('%dd %Hh %Mm %Ss', time.gmtime(stepTime-startTime)))
              experiment.sendMail('progress {}% '.format(percentage), message)
            t.update(1)
    return nbFailed

  def mask(
    self,
    mask=None,
    volatile=False
    ):
    """set the mask.

  	This method sets the internal mask to the mask given as parameter. Once set, iteration over the setting set is limited to the settings that can be reached according to the definition of the mask.

  	Parameters
  	----------

    mask: list of list of int or list of int
     a :term:`mask

    volatile: bool
      if True, the mask is disabled after a complete iteration over the setting set.

      If False, the mask is saved for further iterations.

  	Examples
  	--------

    >>> import explanes as el

    >>> f = el.factor.Factor()
    >>> f.f1=['a', 'b', 'c']
    >>> f.f2=[1, 2, 3]

    >>> # select the settings with the second modality of the first factor, and with the first modality of the second factor
    >>> for setting in f.mask([1, 0]):
    ...  print(setting)
    f1 b f2 1
    >>> # select the settings with the second modality of the first factor, and all the modalities of the second factor
    >>> for setting in f.mask([1, -1]):
    ...  print(setting)
    f1 b f2 1
    f1 b f2 2
    f1 b f2 3
    >>> # the selection of all the modalities of the remaining factors can be conveniently expressed
    >>> for setting in f.mask([1]):
    ...  print(setting)
    f1 b f2 1
    f1 b f2 2
    f1 b f2 3
    >>> # select the settings using 2 mask, where the first selects the settings with the first modality of the first factor and with the second modality of the second factor, and the second mask selects the settings with the second modality of the first factor, and with the third modality of the second factor
    >>> for setting in f.mask([[0, 1], [1, 2]]):
    ...  print(setting)
    f1 a f2 2
    f1 b f2 3
    >>> # the latter expression may be interpreted as the selection of the settings with the first and second modalities of the first factor and with second and third modalities of the second factor. In that case, one needs to add a -1 at the end the mask (even if by doing so the length of the mask is larger than the number of factors)
    >>> for setting in f.mask([[0, 1], [1, 2], -1]):
    ...  print(setting)
    f1 a f2 2
    f1 a f2 3
    f1 b f2 2
    f1 b f2 3
    >>> # if volatile is set to False (default) when the mask is set and the setting set iterated, the setting set stays ready for another iteration.
    >>> for setting in f.mask([0, 1]):
    ...  pass
    >>> for setting in f:
    ...  print(setting)
    f1 a f2 2
    >>> # if volatile is set to False (default) when the mask is set and the setting set iterated, the setting set stays ready for another iteration.
    >>> for setting in f.mask([0, 1], volatile=True):
    ...  pass
    >>> for setting in f:
    ...  print(setting)
    f1 a f2 1
    f1 a f2 2
    f1 a f2 3
    f1 b f2 1
    f1 b f2 2
    f1 b f2 3
    f1 c f2 1
    f1 c f2 2
    f1 c f2 3
    >>> # if volatile was set to False (default) when the mask was first set and the setting set iterated, the complete set of settings can be reached by calling mask with no parameters.
    >>> for setting in f.mask([0, 1]):
    ...  pass
    >>> for setting in f.mask():
    ...  print(setting)
    f1 a f2 1
    f1 a f2 2
    f1 a f2 3
    f1 b f2 1
    f1 b f2 2
    f1 b f2 3
    f1 c f2 1
    f1 c f2 2
    f1 c f2 3
    """

    self._mask = mask
    self._maskVolatile = volatile
    return self

  def factors(
    self
    ):
    """returns the names of the factors.

  	Returns the names of the factors as a list of strings.

  	Examples
  	--------

    >>> import explanes as el

    >>> f = el.factor.Factor()
    >>> f.f1=['a', 'b']
    >>> f.f2=[1, 2]
    >>> f.f3=[0, 1]

    >>> print(f.factors())
    ['f1', 'f2', 'f3']
    """
    return self._factors

  def nbModalities(
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

    >>> import explanes as el

    >>> f = el.factor.Factor()
    >>> f.one = ['a', 'b']
    >>> f.two = list(range(10))

    >>> print(f.nbModalities('one'))
    2
    >>> print(f.nbModalities(1))
    10
    """
    if isinstance(factor, int):
      factor = self.factors()[factor]
    return len(object.__getattribute__(self, factor))

  def cleanH5(self, path, reverse=False, force=False, settingEncoding={}):
    """clean a h5 data sink by considering the settings set.

  	This method is more conveniently used by considering the method :meth:`explanes.experiment.Experiment.cleanDataSink, please see its documentation for usage.
    """
    h5 = tb.open_file(path, mode='a')
    if reverse:
      ids = [setting.id(**settingEncoding) for setting in self]
      for g in h5.iter_nodes('/'):
        if g._v_name not in ids:
          h5.remove_node(h5.root, g._v_name, recursive=True)
    else:
      for setting in self:
        groupName = setting.id(**settingEncoding)
        if h5.root.__contains__(groupName):
          h5.remove_node(h5.root, groupName, recursive=True)
    h5.close()

    # repack
    outfilename = path+'Tmp'
    command = ["ptrepack", "-o", "--chunkshape=auto", "--propindexes", path, outfilename]
    # print('Original size is %.2fMiB' % (float(os.stat(path).st_size)/1024**2))
    if call(command) != 0:
      print('Unable to repack. Is ptrepack installed ?')
    else:
      # print('Repacked size is %.2fMiB' % (float(os.stat(outfilename).st_size)/1024**2))
      os.rename(outfilename, path)


  def cleanDataSink(
    self,
    path,
    reverse=False,
    force=False,
    selector='*',
    settingEncoding={},
    archivePath=''
    ):
    """clean a data sink by considering the settings set.

  	This method is more conveniently used by considering the method :meth:`explanes.experiment.Experiment.cleanDataSink, please see its documentation for usage.
    """

    path = os.path.expanduser(path)
    if path.endswith('.h5'):
      self.cleanH5(path, reverse, force, settingEncoding)
    else:
      fileNames = []
      for setting in self:
        print(path+'/'+setting.id(**settingEncoding)+selector)
        for f in glob.glob(path+'/'+setting.id(**settingEncoding)+selector):
            fileNames.append(f)
      if reverse:
        complete = []
        for f in glob.glob(path+'/'+selector):
          complete.append(f)
        # print(fileNames)
        fileNames = [i for i in complete if i not in fileNames]
      #   print(complete)
      fileNames = set(fileNames)
      print(fileNames)
      # print(len(fileNames))
      if archivePath:
        destination = 'move to '+archivePath+' '
      else:
        destination = 'remove '
      if len(fileNames) and (force or eu.query_yes_no('About to '+destination+str(len(fileNames))+' files from '+path+' \n Proceed ?')):
        for f in fileNames:
          if archivePath:
            os.rename(f, archivePath+'/'+os.path.basename(f))
          else:
            os.remove(f)

  def merge(self):
    # build temporary factor
    tmp = Factor()
    for x in self.factors():
      for f in getattr(self, x).factors():
        setattr(tmp, f, [])
    for x in self.factors():
      for f in getattr(self, x).factors():
        for m in getattr(getattr(self, x), f):
          getattr(tmp, f).append(m)
    # check if factors are available in every experiment
    have = [True]*len(tmp.factors())
    for fi, f in enumerate(tmp.factors()):
      for x in self.factors():
        if not f in getattr(self, x).factors():
          have[fi] = False
    # print(have)
    factor = Factor()
    for fi, f in enumerate(tmp.factors()):
      m = getattr(tmp, f)
      if not have[fi]:
        if isinstance(m[0], str) and 'none' not in m:
          m.insert(0, 'none')
        elif 0 not in m:
          m.insert(0, 0)
      setattr(factor, f, m)
    return factor

  def asPandaFrame(self):
    """returns a panda frame that describes the Factor object.

  	Returns a panda frame describing the Factor object. For ease of definition of a mask to select some settings, the columns and the rows of the panda frame are numbered.

  	Examples
  	--------

    >>> import explanes as el

    >>> f = el.factor.Factor()
    >>> f.one = ['a', 'b']
    >>> f.two = list(range(10))

    >>> print(f)
      0  one: ['a', 'b']
      1  two: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> print(f.asPandaFrame())
      Factor  0  1  2  3  4  5  6  7  8  9
    0    one  a  b
    1    two  0  1  2  3  4  5  6  7  8  9
    """
    l = 1
    for ai, atr in enumerate(self._factors):
      if isinstance(self.__getattribute__(atr), list):
        l = max(l, len(self.__getattribute__(atr)))
      elif isinstance(self.__getattribute__(atr), np.ndarray):
        l = max(l, len(self.__getattribute__(atr)))

    table = []
    for atr in self._factors:
      line = []
      line.append(atr)
      for il in range(l):
        if isinstance(self.__getattribute__(atr), list) and len(self.__getattribute__(atr)) > il :
          line.append(self.__getattribute__(atr)[il])
        elif isinstance(self.__getattribute__(atr), np.ndarray) and len(self.__getattribute__(atr)) > il :
          line.append(self.__getattribute__(atr)[il])
        elif il<1:
          line.append(self.__getattribute__(atr))
        else:
          line.append('')
      table.append(line)
    columns = []
    columns.append('Factor')
    for il in range(l):
      columns.append(il)
    return pd.DataFrame(table, columns=columns)

  def __str__(self):
    cString = ''
    l = 1
    for ai, atr in enumerate(self._factors):
      cString+='  '+str(ai)+'  '+atr+': '+str(self.__getattribute__(atr))+'\n'
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
    if name == '_mask' or name[0] != '_':
      self._changed = True
    if name[0] != '_' and type(value) in {list, np.ndarray} and len(value)>1 and name not in self._nonSingleton:
      self._nonSingleton.append(name)
    return object.__setattr__(self, name, value)

  def __delattr__(
    self,
    name):

    self._changed = True
    if hasattr(self, name) and name[0] != '_':
      self._factors.remove(name)
      if name in self._nonSingleton:
        self._nonSingleton.remove(name)
    return object.__delattr__(self, name)

  # def __getattribute__(
  #   self,
  #   name
  #   ):
  #
  #   value = object.__getattribute__(self, name)
  #   if name[0] != '_' and self._setting and type(inspect.getattr_static(self, name)) != types.FunctionType:
  #     idx = self.factors().index(name)
  #     if self._setting[idx] == -2:
  #       value = None
  #     else:
  #       if  type(inspect.getattr_static(self, name)) in {list, np.ndarray} :
  #         try:
  #           value = value[self._setting[idx]]
  #         except IndexError:
  #           value = 'null'
  #           print('Error: factor '+name+' have modalities 0 to '+str(len(value)-1)+'. Requested '+str(self._setting[idx]))
  #           raise
  #   return value

  def __iter__(
    self
    ):

    self.__setSettings__()
    self._currentSetting = 0
    return self

  def __next__(
    self
    ):

    if self._currentSetting == len(self._settings):
      if self._maskVolatile:
        self._mask = None
      raise StopIteration
    else:
      self._setting = self._settings[self._currentSetting]
      # print(self._setting)
      self._currentSetting += 1
      return es.Setting(self)
      # if self._parallel:
      #   return copy.deepcopy(self)
      # else:
      #   return self #  copy.deepcopy(self)

  def __getitem__(self, index):
    # print('get item')
    self.__setSettings__()
    # print(self._mask)
    return  self


  def __len__(
    self
    ):
    self.__setSettings__()
    return len(self._settings)

  def __setSettings__(
    self
    ):
    if self._changed:
      settings = []
      mask = copy.deepcopy(self._mask)
      self._setting = None

      mask = copy.deepcopy(mask)
      nbFactors = len(self.factors())
      if mask is None or len(mask)==0 or (len(mask)==1 and len(mask)==0) :
         mask = [[-1]*nbFactors]
      if isinstance(mask, list) and not all(isinstance(x, list) for x in mask):
          mask = [mask]

      for im, m in enumerate(mask):
        if len(m) < nbFactors:
          mask[im] = m+[-1]*(nbFactors-len(m))
        for il, l in enumerate(m):
            if not isinstance(l, list) and l > -1:
                mask[im][il] = [l]

      for m in mask:
        # handle -1 in mask
        for mfi, mf in enumerate(m):
          if isinstance(mf, int) and mf == -1 and mfi<len(self.factors()):
            attr = self.__getattribute__(self.factors()
            [mfi])
            # print(attr)
            # print(isinstance(attr, int))
            if isinstance(attr, list) or isinstance(attr, np.ndarray):
              m[mfi] = list(range(len(attr)))
            else:
              m[mfi] = [0]

        s = self.__setSettingsMask__(m, 0)
        if all(isinstance(ss, list) for ss in s):
          for ss in s:
            settings.append(ss)
        else:
          settings.append(s)
      self._changed = False
      self._settings = settings

  def __setSettingsMask__(self, mask, done):
    if done == len(mask):
      return []

    s = self.__setSettingsMask__(mask, done+1)
    if isinstance(mask[done], list):
      settings = []
      for mod in mask[done]:
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
          ss.insert(0, mask[done])
      else:
        settings.insert(0, mask[done])
    return settings

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
