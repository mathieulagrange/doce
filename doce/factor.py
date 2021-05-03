import os
import shutil as sh
import inspect
import types
import numpy as np
import tables as tb
import pandas as pd
import copy
import glob
import doce.util as eu
import doce.setting as es
import logging
from joblib import Parallel, delayed
from subprocess import call
import time
from itertools import groupby

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

  >>> import doce

  >>> f = doce.factor.Factor()
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
      self._expandedMask = None
      self._nonSingleton = []
      self._factors = []
      self._default = types.SimpleNamespace()
      self._maskVolatile = True
      self._pruneMask = True

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

    doce.factor.Factor.id

  	Examples
  	--------

    >>> import doce

    f = doce.Factor()

    f.f1 = ['a', 'b']
    f.f2 = [1, 2, 3]

    print(f)
    for setting in f.mask():
      print(setting.id())

    f.default('f2', 2)

    for setting in f:
      print(setting.id())

    f.f2 = [0, 1, 2, 3]
    print(f)

    f.default('f2', 2)

    for setting in f:
      print(setting.id())


    """
    if hasattr(self, factor):
      # if genericDefaultModalityWarning and len([item for item in getattr(self, factor) if item in [0, 'none']]):
      #   print('Setting an explicit default modality to factor '+factor+' should be handled with care as the factor already as an implicit default modality (O or none). This may lead to loss of data. Ensure that you have the flag <hideNoneAndZero> set to False when using method id() if (O or none). You can remove this warning by setting the flag <force> to True.')
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
    progress='d',
    logFileName='',
    mailInterval=0):
    """iterate over the setting set and run the function given as parameter.

    This function is wrapped by :meth:`doce.experiment.Experiment.do`, which should be more convenient to use. Please refer to this method for usage.

    Parameters
    ----------

    function : function(:class:`~doce.factor.Factor`, :class:`~doce.experiment.Experiment`, \*parameters)
      operates on a given setting within the experiment environnment with optional parameters.

    experiment:
      an :class:`~doce.experiment.Experiment` object

    *parameters : any type (optional)
      parameters to be given to the function.

    nbJobs : int > 0 (optional)
      number of jobs.

      If nbJobs = 1, the setting set is browsed sequentially in a depth first traversal of the settings tree (default).

      If nbJobs > 1, the settings set is browsed randomly, and settings are distributed over the different processes.

    progress : str (optional)
      display progress of scheduling the setting set.

      If str has an m, show the mask of the current setting.
      If str has an d, show a textual description of the current setting (default).

    logFileName : str (optional)
      path to a file where potential errors will be logged.

      If empty, the execution is stopped on the first faulty setting (default).

      If not empty, the execution is not stopped on a faulty setting, and the error is logged in the logFileName file.

    See Also
    --------

    doce.experiment.Experiment.do

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
      with tqdm(total=len(self), disable = progress == '') as t:
        for iSetting, setting in enumerate(self):
            description = ''
            if nbFailed:
                description = '[failed: '+str(nbFailed)+']'
            if 'm' in progress:
              description += str(self._settings[iSetting])+' '
            if 'd' in progress:
              description += setting.id()
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
    volatile=False,
    prune=True
    ):
    """set the mask.

  	This method sets the internal mask to the mask given as parameter. Once set, iteration over the setting set is limited to the settings that can be reached according to the definition of the mask.

  	Parameters
  	----------

    mask: list of list of int or list of int or list of dict
     a :term:`mask

    volatile: bool
      if True, the mask is disabled after a complete iteration over the setting set.

      If False, the mask is saved for further iterations.

  	Examples
  	--------

    >>> import doce

    >>> f = doce.factor.Factor()
    >>> f.f1=['a', 'b', 'c']
    >>> f.f2=[1, 2, 3]

    >>> # doce allows two ways of defining the mask. The first one is dict based:
    >>> for setting in f.mask([{'f1':'b', 'f2':[1, 2]}, {'f1':'c', 'f2':[3]}]):
    ...  print(setting)
    f1 b f2 1
    f1 b f2 2
    f1 c f2 3

    >>> # The second one is list based. In this exmaple, we select the settings with the second modality of the first factor, and with the first modality of the second factor
    >>> for setting in f.mask([1, 0]):
    ...  print(setting)
    f1 b f2 1
    >>> # select the settings with all the modalities of the first factor, and the second modality of the second factor
    >>> for setting in f.mask([-1, 1]):
    ...  print(setting)
    f1 a f2 2
    f1 b f2 2
    f1 c f2 2
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
    if mask and (isinstance(mask, str) or isinstance(mask, dict)):
      mask = [mask]
    if mask and any(isinstance(val, str) for val in mask):
      mask = self._str2list(mask)
    elif mask and any(isinstance(val, dict) for val in mask):
      mask = self._dict2list(mask)

    self._mask = mask
    self._maskVolatile = volatile
    self._pruneMask = prune
    return self

  def factors(
    self
    ):
    """returns the names of the factors.

  	Returns the names of the factors as a list of strings.

  	Examples
  	--------

    >>> import doce

    >>> f = doce.factor.Factor()
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

    >>> import doce

    >>> f = doce.factor.Factor()
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

  def cleanH5(
    self,
    path,
    reverse=False,
    force=False,
    keep=False,
    settingEncoding={},
    archivePath='',
    verbose=0):
    """clean a h5 data sink by considering the settings set.

  	This method is more conveniently used by considering the method :meth:`doce.experiment.Experiment.cleanDataSink, please see its documentation for usage.
    """
    if archivePath:
      print(path)
      print(archivePath)
      sh.copyfile(path, archivePath)
      self.cleanH5(
        path=archivePath,
        reverse = not reverse,
        force=True,
        keep=False,
        settingEncoding=settingEncoding,
        archivePath='',
        verbose=verbose)
    if not keep:
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
      print('repack')
      # repack
      outfilename = path+'Tmp'
      command = ["ptrepack", "-o", "--chunkshape=auto", "--propindexes", path, outfilename]
      if verbose:
        print('Original size is %.2fMiB' % (float(os.stat(path).st_size)/1024**2))
      if call(command) != 0:
        print('Unable to repack. Is ptrepack installed ?')
      else:
        if verbose:
          print('Repacked size is %.2fMiB' % (float(os.stat(outfilename).st_size)/1024**2))
        os.rename(outfilename, path)


  def cleanDataSink(
    self,
    path,
    reverse=False,
    force=False,
    keep=False,
    selector='*',
    settingEncoding={},
    archivePath='',
    verbose=0
    ):
    """clean a data sink by considering the settings set.

  	This method is more conveniently used by considering the method :meth:`doce.experiment.Experiment.cleanDataSink, please see its documentation for usage.
    """

    path = os.path.expanduser(path)
    if path.endswith('.h5'):
      self.cleanH5(path, reverse, force, keep, settingEncoding, archivePath, verbose)
    else:
      fileNames = []
      for setting in self:
        if verbose:
          print('search path: '+path+'/'+setting.id(**settingEncoding)+selector)
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
      if verbose:
        print('Selected files')
        print(fileNames)
      # print(len(fileNames))
      if archivePath:
        if keep:
          action = 'copy '
        else:
          action = 'move '
        destination = ' to '+archivePath+' '
      elif not force:
        print('INFORMATION: setting path.archive allows you to move the unwanted files to the archive path and not delete them.')
        destination = ''
        action = 'remove '
      if len(fileNames):
        if not force and eu.query_yes_no('List the '+str(len(fileNames))+' files ?'):
          print("\n".join(fileNames))
        if force or eu.query_yes_no('About to '+action+str(len(fileNames))+' files from '+path+destination+' \n Proceed ?'):
          for f in fileNames:
            if archivePath:
              if keep:
                sh.copyfile(f, archivePath+'/'+os.path.basename(f))
              else:
                os.rename(f, archivePath+'/'+os.path.basename(f))
            else:
              os.remove(f)
      else:
        print('no files found.')
  def merge(self):
    # build temporary factor
    tmp = Factor()
    for x in self.factors():
      for f in getattr(self, x).factors():
        setattr(tmp, f, np.empty([0]))
        if hasattr(getattr(self, x)._default, f):
          if hasattr(tmp._default, f) and getattr(getattr(self, x)._default, f) != getattr(tmp._default, f):
            print(getattr(tmp._default, f))
            print('While merging factors of the different experiment, a conflict of default modalities for the factor '+f+' is detected. This may lead to an inconsistent behavior.')
            raise ValueError
          else:
            setattr(tmp._default, f, getattr(getattr(self, x)._default, f))
            # print(tmp._default)
    for x in self.factors():
      for f in getattr(self, x).factors():
        for m in getattr(getattr(self, x), f):
          if len(getattr(tmp, f))==0 or m not in getattr(tmp, f):
            setattr(tmp, f, np.append(getattr(tmp, f), m))
    # check if factors are available in every experiment
    have = [True]*len(tmp.factors())
    for fi, f in enumerate(tmp.factors()):
      for x in self.factors():
        if not f in getattr(self, x).factors():
          have[fi] = False
    # print(have)
    factor = Factor()
    factor._default = tmp._default
    for fi, f in enumerate(tmp.factors()):
      m = getattr(tmp, f)
      # print(m)
      # print(type(m[0]))
      if not isinstance(m[0], str) and all(np.array([val.is_integer() for val in m])):
        m = np.array(m, dtype=np.intc)
      setattr(factor, f, m)
      if not have[fi] and not hasattr(tmp._default, f):
        if isinstance(m[0], str):
          if 'none' not in m:
            m = np.insert(m, 0, 'none')
            setattr(factor, f, m)
          factor.default(f, 'none')
        if not isinstance(m[0], str):
          if 0 not in m:
            m = np.insert(m, 0, 0)
            setattr(factor, f, m)
          factor.default(f, 0)
    return factor

  def asPandaFrame(self):
    """returns a panda frame that describes the Factor object.

  	Returns a panda frame describing the Factor object. For ease of definition of a mask to select some settings, the columns and the rows of the panda frame are numbered.

  	Examples
  	--------

    >>> import doce

    >>> f = doce.factor.Factor()
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
    columns.append('Factor')
    for il in range(l):
      columns.append(il)
    return pd.DataFrame(table, columns=columns)

  def constantFactors(self, mask):
    self.mask(mask)
    message = str(len(self))+' settings'
    # print(self._mask)
    # print(self._expandedMask)
    cf = [ [] for _ in range(len(self._factors)) ]
    for m in self._expandedMask:
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

  def _dict2list(self, dictMask):
    """convert dict based mask to list based mask

    """
    mask = []
    for dm in dictMask:
      m = [-1]*len(self._factors)
      for dmk in dm.keys():
        if dmk in self._factors:
          if isinstance(dm[dmk], list):
            mm = []
            for dmkl in dm[dmk]:
              if dmkl in getattr(self, dmk):
                 mm.append(list(getattr(self, dmk)).index(dmkl))
              else:
                print('Warning: '+str(dmkl)+' is not a modality of factor '+dmk+'.')
            m[self._factors.index(dmk)] = mm
          else:
            if dm[dmk] in getattr(self, dmk):
              m[self._factors.index(dmk)] = list(getattr(self, dmk)).index(dm[dmk])
        else:
          print('Warning: '+dmk+' is not a factor.')
      mask.append(m)
    return mask

  def _str2list(self, strMask):
    """convert string based mask to list based mask

    """
    mask = []
    for dm in strMask:
      m = [-1]*len(self._factors)
      sp = dm.split('_')
      factors = sp[0::2]
      modalities = sp[1::2]
      for dmki, dmk in enumerate(factors):
        if dmk in self._factors:
            mod = modalities[dmki]
            refMod = []
            for am in list(getattr(self, dmk)):
              refMod.append(eu.specialCaracterNaturalNaming(str(am)))
            if mod in refMod:
              m[self._factors.index(dmk)] = refMod.index(mod)
            else:
              print('Warning: '+modalities[dmki]+' is not a modality of factor '+dmk+'.')
        else:
          print('Warning: '+dmk+' is not a factor.')
      mask.append(m)
    return mask

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
    if name == '_mask' or name[0] != '_':
      self._changed = True
    if name[0] != '_' and type(value) in {list, np.ndarray} and len(value)>1 and name not in self._nonSingleton:
      self._nonSingleton.append(name)
    if name[0] != '_' and type(value) not in {np.ndarray, Factor}:
      if len(value) and not all(isinstance(x, type(value[0])) for x in value):
        raise Exception('All the modalities of the factor '+name+' must be of the same type (str, int, or float)')
      print(type(value))
      print(type(value[0]))
      if len(value) and all(isinstance(x, str) for x in value):
        value = np.array(value)
      elif len(value) and all(isinstance(x, int) for x in value):
        value = np.array(value, dtype=np.intc)
      else:
        value = np.array(value, dtype=np.float)

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
      # prune repeated entries
      for im, m in enumerate(mask):
        if isinstance(m, list):
          for il, l in enumerate(m):
            if isinstance(l, list):
              m[il] = list(dict.fromkeys(l))
      self._expandedMask = mask

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
      prunedSettings = [k for k,v in groupby(sorted(settings))]
      if self._pruneMask and len(prunedSettings) < len(settings):
        settings = prunedSettings
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
    # print(settings)
    return settings

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
