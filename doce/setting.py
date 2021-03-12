import doce.util as eu
import hashlib
import copy
import logging
import traceback

class Setting():
  """stores a :term:`setting`, where each member is a factor and the value of the member is a modality.

  Stores a :term:`setting`, where each member is a factor and the value of the member is a modality.

  Examples
  --------

  >>> import doce

  >>> f = doce.factor.Factor()
  >>> f.f1=['a', 'b']
  >>> f.f2=[1, 2]

  >>> for setting in f:
  ...   print(setting)
  f1 a f2 1
  f1 a f2 2
  f1 b f2 1
  f1 b f2 2

  """

  def __init__(self, factor, settingArray=None):
    self._factor = factor
    # underscore = ['_nonSingleton', '_default', '_factors', '_setting']
    # for f in underscore:
    #   self.__setattr__(f, getattr(factor, f))

    if settingArray:
      self._setting = copy.deepcopy(settingArray)
    else:
      self._setting = copy.deepcopy(factor._setting)

    for fi, f in enumerate(factor.factors()):
      # print(self._setting[fi])
      # print(f)
      self.__setattr__(f, getattr(factor, f)[self._setting[fi]])

  def __str__(self):
    """returns a one-liner str with a readable description of the Factor object or the current setting.

  	returns a one-liner str with a readable description of the Factor object or the current setting if in an iterable.

  	Examples
  	--------

    >>> import doce

    >>> f = doce.factor.Factor()
    >>> f.one = ['a', 'b']
    >>> f.two = [1, 2]

    >>> print(f)
      0  one: ['a', 'b']
      1  two: [1, 2]

    >>> for setting in f:
    ...   print(setting)
    one a two 1
    one a two 2
    one b two 1
    one b two 2
    """
    return self.id(sort=False, separator=' ', singleton=True, default=False)


  def id(self, format='long', sort=True, separator='_', singleton=True, default=False, hide=[]):
    """return a one-liner str or a list of str that describes a setting or a :class:`~doce.factor.Factor` object.

  	Return a one-liner str or a list of str that describes a setting or a :class:`~doce.factor.Factor` object with a high degree of flexibility.

  	Parameters
  	----------

    format: str (optional)
      'long': (default)
      'shortUnderscore': pythonCase delimitation
      'shortCapital': camelCase delimitation
      'short':
      'list': a list of string alternating factor and the corresponding modality
      'hash':

    sort: bool (optional)
     if True, sorts the factors by name  (default).

     If False, use the order of definition.

    singleton: bool (optional)
      if True, consider factors with only one modality.

      if False, consider factors with only one modality (default).

    default: bool (optional)
      also consider couple of factor/modality where the modality is explicitly set to be a default value for this factor using :meth:`doce.factor.Factors.default`.

    hide: list of str
      list the factors that should not be considered. The list is empty by default.

    separator: str
      separator used to concatenate the factor and modality value, default is '_'.

  	See Also
  	--------

    doce.factor.Factor.default

    doce.util.compressName

  	Examples
  	--------

    >>> import doce

    >>> f = doce.factor.Factor()
    >>> f.one = ['a', 'b']
    >>> f.two = [0, 1]
    >>> f.three = ['none', 'c']
    >>> f.four = 'd'

    >>> print(f)
      0  one: ['a', 'b']
      1  two: [0, 1]
      2  three: ['none', 'c']
      3  four: d

    >>> for setting in f.mask([0, 1, 1]):
    ...   # default display
    ...   print(setting.id())
    four_d_one_a_three_c_two_1
    >>> # list format
    >>> print(setting.id('list'))
    ['four', 'd', 'one', 'a', 'three', 'c', 'two', '1']
    >>> # hashed version of the default display
    >>> print(setting.id('hash'))
    5ab88e338f29c2dec99880d3b9dee7e9
    >>> # do not apply sorting of the factor
    >>> print(setting.id(sort=False))
    one_a_two_1_three_c_four_d
    >>> # specify a separator
    >>> print(setting.id(separator=' '))
    four d one a three c two 1
    >>> # do not show some factors
    >>> print(setting.id(hide=['one', 'three']))
    four_d_two_1
    >>> # do not show factors with only one modality
    >>> print(setting.id(singleton=False))
    one_a_three_c_two_1
    >>> delattr(f, 'four')
    >>> for setting in f.mask([0, 0, 0]):
    ...   print(setting.id())
    one_a

    >>> # set the default value of factor one to a
    >>> f.default('one', 'a')
    >>> for setting in f.mask([0, 1, 1]):
    ...   print(setting.id())
    three_c_two_1
    >>> # do not hide the default value in the description
    >>> print(setting.id(default=False))
    one_a_three_c_two_1

    >>> f.optional_parameter = ['value_one', 'value_two']
    >>> for setting in f.mask([0, 1, 1, 0]):
    ...   print(setting.id())
    optional_parameter_value_one_three_c_two_1
    >>> # compress the names as pythonCase
    >>> print(setting.id(format = 'shortUnderscore'))
    oppa_vaon_th_c_tw_1
    >>> delattr(f, 'optional_parameter')

    >>> f.optionalParameter = ['valueOne', 'valueTwo']
    >>> for setting in f.mask([0, 1, 1, 0]):
    ...   print(setting.id())
    optionalParameter_valueOne_three_c_two_1
    >>> # compress the names as camelCase
    >>> print(setting.id(format = 'shortCapital'))
    oppa_vaon_th_c_tw_1

    >>> f.optionalParameter = ['value_one', 'value_two']
    >>> for setting in f.mask([0, 1, 1, 0]):
    ...   print(setting.id())
    optionalParameter_value_one_three_c_two_1
    >>> # compress the names with smart detection of the type of case
    >>> print(setting.id(format = 'short'))
    oppa_vaon_th_c_tw_1
    """
    id = []
    fNames = self._factor._factors
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
        if (singleton or f in self._factor._nonSingleton) and (default or not hasattr(self._factor._default, f) or (not default and hasattr(self._factor._default, f) and getattr(self._factor._default, f) != getattr(self, f))):
          id.append(eu.compressDescription(f, format))
          id.append(eu.compressDescription(str(getattr(self, f)), format))
    if 'list' not in format:
      id = separator.join(id)
      if format == 'hash':
        id  = hashlib.md5(id.encode("utf-8")).hexdigest()
    return id

  def replace(self, factor, value=None, positional=0, relative=0):
    """returns a new doce.factor.Factor object with one factor with modified modality.

    Returns a new doce.factor.Factor object with with one factor with modified modality. The value of the requested new modality can requested by 3 exclusive means: its value, its position in the modality array, or its relative position in the array with respect to the position of the current modality.

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

    >>> f = doce.factor.Factor()
    >>> f.one = ['a', 'b', 'c']
    >>> f.two = [1, 2, 3]

    >>> for setting in f.mask([1, 1]):
    ...   # the inital setting
    ...   print(setting)
    one b two 2
    >>> # the same setting but with the factor 'two' set to modality 1
    >>> print(setting.replace('two', value=1))
    one b two 1
    >>> # the same setting but with the first factor set to modality
    >>> print(setting.replace(1, value=1))
    one b two 1
    >>> # the same setting but with the factor 'two' set to modality index 0
    one b two 1
    >>> print(setting.replace('two', positional=0))
    one b two 1
    >>> # the same setting but with the factor 'two' set to modality of relative index -1 with respect to the modality index of the current setting
    >>> print(setting.replace('two', relative=-1))
    one b two 1
    """

    # get factor index
    if isinstance(factor, str):
      factor = self._factor._factors.index(factor)
    # get modality index
    if value is not None:
      factorName = self._factor._factors[factor]
      modalities = self._factor.__getattribute__(factorName)
      positional = modalities.index(value)

    sDesc = copy.deepcopy(self._setting)
    if relative:
      sDesc[factor] += relative
    else:
      sDesc[factor] = positional

    if sDesc[factor]< 0 or sDesc[factor] >= self._factor.nbModalities(factor):
      print('Unable to find the requested modality.')
      return None
    else:
      s = Setting(self._factor, sDesc)
      return s

  def do(
    self,
    function,
    experiment,
    logFileName,
    *parameters
    ):
    """run the function given as parameter for the setting.

  	Helper function for the method :meth:`~doce.factor.Factor.do`.

  	See Also
  	--------

    doce.factor.Factor.do

    """
    failed = 0
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

  def remove(self, factor):
    delattr(self, factor)
    print(': '+factor)
    # print(self)
    return self


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    # doctest.run_docstring_examples(Setting.id, globals())
