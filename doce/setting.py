import doce
import hashlib
import copy
import logging
import traceback
import numpy as np

class Setting():
  """stores a :term:`setting`, where each member is a factor and the value of the member is a modality.

  Stores a :term:`setting`, where each member is a factor and the value of the member is a modality.

  Examples
  --------

  >>> import doce

  >>> p = doce.Plan()
  >>> p.f1=['a', 'b']
  >>> p.f2=[1, 2]

  >>> for setting in p:
  ...   print(setting)
  f1=a+f2=1
  f1=a+f2=2
  f1=b+f2=1
  f1=b+f2=2

  """

  def __init__(self, plan, settingArray=None):
    self._plan = plan
    # underscore = ['_nonSingleton', '_default', '_plans', '_setting']
    # for f in underscore:
    #   self.__setattr__(f, getattr(plan, f))

    if settingArray:
      self._setting = copy.deepcopy(settingArray)
    else:
      self._setting = copy.deepcopy(plan._setting)

    for fi, f in enumerate(plan.factors()):
      # print(self._setting[fi])
      # print(f)
      self.__setattr__(f, getattr(plan, f)[self._setting[fi]])

  def __str__(self):
    """returns a one-liner str with a readable description of the Factor object or the current setting.

  	returns a one-liner str with a readable description of the Factor object or the current setting if in an iterable.

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan()
    >>> p.one = ['a', 'b']
    >>> p.two = [1, 2]

    >>> print(p)
      0  one: ['a' 'b']
      1  two: [1 2]

    >>> for setting in p:
    ...   print(setting)
    one=a+two=1
    one=a+two=2
    one=b+two=1
    one=b+two=2
    """
    return self.id(sort=False, singleton=True, default=True)


  def id(self, format='long', sort=True, separator='+', identifier='=', singleton=True, default=False, hide=[], toInt=True):
    """return a one-liner str or a list of str that describes a setting or a :class:`~doce.Plan` object.

  	Return a one-liner str or a list of str that describes a setting or a :class:`~doce.Plan` object with a high degree of flexibility.

  	Parameters
  	----------

    format: str (optional)
      'long': (default)
      'list': a list of string alternating factor and the corresponding modality
      'hash': a hashed version

    sort: bool (optional)
     if True, sorts the factors by name  (default).

     If False, use the order of definition.

    singleton: bool (optional)
      if True, consider factors with only one modality.

      if False, consider factors with only one modality (default).

    default: bool (optional)
      if True, also consider couple of factor/modality where the modality is explicitly set to be a default value for this factor using :meth:`doce.Plan.default`.

      if False, do not show them (default).

    hide: list of str
      list the factors that should not be considered. The list is empty by default.

    separator: str
      separator used to concatenate the factors, default is '|'.

    separator: str
      separator used to concatenate the factor and modality value, default is '='.

  	See Also
  	--------

    doce.Plan.default

    doce.util.compressName

  	Examples
  	--------

    >>> import doce

    >>> p = doce.Plan()
    >>> p.one = ['a', 'b']
    >>> p.two = [0,1]
    >>> p.three = ['none', 'c']
    >>> p.four = 'd'

    >>> print(p)
      0  one: ['a' 'b']
      1  two: [0 1]
      2  three: ['none' 'c']
      3  four: ['d']

    >>> for setting in p.select([0, 1, 1]):
    ...   # default display
    ...   print(setting.id())
    four=d+one=a+three=c+two=1
    >>> # list format
    >>> print(setting.id('list'))
    ['four=d', 'one=a', 'three=c', 'two=1']
    >>> # hashed version of the default display
    >>> print(setting.id('hash'))
    4474b298d3b23000e739e888042dab2b
    >>> # do not apply sorting of the factor
    >>> print(setting.id(sort=False))
    one=a+two=1+three=c+four=d
    >>> # specify a separator
    >>> print(setting.id(separator=' '))
    four=d one=a three=c two=1
    >>> # do not show some factors
    >>> print(setting.id(hide=['one', 'three']))
    four=d+two=1
    >>> # do not show factors with only one modality
    >>> print(setting.id(singleton=False))
    one=a+three=c+two=1
    >>> delattr(p, 'four')
    >>> for setting in p.select([0, 0, 0]):
    ...   print(setting.id())
    one=a+three=none+two=0

    >>> # set the default value of factor one to a
    >>> p.default('one', 'a')
    >>> for setting in p.select([0, 1, 1]):
    ...   print(setting.id())
    three=c+two=1
    >>> # do not hide the default value in the description
    >>> print(setting.id(default=True))
    one=a+three=c+two=1

    >>> p.optional_parameter = ['value_one', 'value_two']
    >>> for setting in p.select([0, 1, 1, 0]):
    ...   print(setting.id())
    optional_parameter=valueunderscoreone+three=c+two=1
    >>> delattr(p, 'optional_parameter')

    >>> p.optionalParameter = ['valueOne', 'valueTwo']
    >>> for setting in p.select([0, 1, 1, 0]):
    ...   print(setting.id())
    optionalParameter=valueOne+three=c+two=1

    """
    id = []
    fNames = self._plan._factors
    if isinstance(hide, str):
      hide=[hide]
    elif isinstance(hide, int) :
      hide=[fNames[hide]]
    elif isinstance(hide, list) and len(hide) and isinstance(hide[0], int) :
      for oi, o in enumerate(hide):
        hide[oi]=fNames[o]
    if sort:
      fNames = sorted(fNames)
    for fIndex, f in enumerate(fNames):
      if f[0] != '_' and getattr(self, f) is not None and f not in hide:
        if (singleton or f in self._plan._nonSingleton) and (default or not hasattr(self._plan._default, f) or (not default and hasattr(self._plan._default, f) and getattr(self._plan._default, f) != getattr(self, f))):
          # id.append(f)
          # print(str(getattr(self, f)))
          modality = doce.util.specialCaracterNaturalNaming(str(getattr(self, f)))
          id.append(f+identifier+modality)
    if 'list' not in format:
      id = separator.join(id)
      if format == 'hash':
        id  = hashlib.md5(id.encode("utf-8")).hexdigest()
    return id

  def replace(self, factor, value=None, positional=0, relative=0):
    """returns a new doce.Plan object with one factor with modified modality.

    Returns a new doce.Plan object with with one factor with modified modality. The value of the requested new modality can requested by 3 exclusive means: its value, its position in the modality array, or its relative position in the array with respect to the position of the current modality.

    Parameters
    ----------

    factor: int or str
      if int, considered as the index inside an array of the factors sorted by order of definition.

      If str, the name of the factor.

    modality: literal or None (optional)
      the value of the modality.

    positional: int (optional)
      if 0, this parameter is not considered (default).

      If >0, interpreted as the index in the modality array (default).

    relative: int (optional)
      if 0, this parameter is not considered (default).

      Otherwise, interpreted as an index, relative to the current modality.

    Examples
    --------

    >>> import doce

    >>> p = doce.Plan()
    >>> p.one = ['a', 'b', 'c']
    >>> p.two = [1, 2, 3]

    >>> for setting in p.select([1, 1]):
    ...   # the inital setting
    ...   print(setting)
    one=b+two=2
    >>> # the same setting but with the factor 'two' set to modality 1
    >>> print(setting.replace('two', value=1))
    one=b+two=1
    >>> # the same setting but with the first factor set to modality
    >>> print(setting.replace(1, value=1))
    one=b+two=1
    >>> # the same setting but with the factor 'two' set to modality index 0
    one=b+two=1
    >>> print(setting.replace('two', positional=0))
    one=b+two=1
    >>> # the same setting but with the factor 'two' set to modality of relative index -1 with respect to the modality index of the current setting
    >>> print(setting.replace('two', relative=-1))
    one=b+two=1
    """

    # get factor index
    if isinstance(factor, str):
      factor = self._plan._factors.index(factor)
    # get modality index
    if value is not None:
      factorName = self._plan._factors[factor]
      modalities = self._plan.__getattribute__(factorName)
      positional, = np.where(modalities == value)
      positional = positional[0] # assumes no repetion

    sDesc = copy.deepcopy(self._setting)
    if relative:
      sDesc[factor] += relative
    else:
      sDesc[factor] = positional
    if sDesc[factor]< 0 or sDesc[factor] >= self._plan.nbModalities(factor):
      print('Unable to find the requested modality.')
      return None
    else:
      s = Setting(self._plan, sDesc)
      return s

  def do(
    self,
    function,
    experiment,
    logFileName,
    *parameters
    ):
    """run the function given as parameter for the setting.

  	Helper function for the method :meth:`~doce.Plan.do`.

  	See Also
  	--------

    doce.Plan.do

    """
    failed = 0
    if experiment.skipSetting(self) :
      message = 'Metrics for setting '+self.id()+' already available. Skipping...'
      print(message)
      if logFileName:
        logging.info(message)
    else:
      try:
        function(self, experiment, *parameters)
      except Exception as e:
        if logFileName:
          failed = 1
          #print('setting '+setting.id()+' failed')
          logging.info(traceback.format_exc())
        else:
          raise e
    return failed

  def removeFactor(self, factor):
    """returns a copy of the setting where the specified factor is removed.

    Parameters
    ----------

    factor: str
      the name of the factor.

    """
    s = copy.deepcopy(self)
    delattr(s, factor)
    return s


if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    # doctest.run_docstring_examples(Setting.id, globals())
