"""Handle the display of settings, the unique description of a parametrization 
   of the system probed by the experiment of the dcode module."""

import hashlib
import copy
import logging
import traceback
import numpy as np

class Setting():
  """stores a :term:`setting`, where each member is a factor
  and the value of the member is a modality.

  Stores a :term:`setting`, where each member is a factor
  and the value of the member is a modality.

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

  def __init__(self, plan, setting_array = None, positional=True):
    self._plan = plan
    # underscore = ['_non_singleton', '_default', '_plans', '_setting']
    # for f in underscore:
    #   self.__setattr__(f, getattr(plan, f))

    if setting_array is not None and positional == False:
      setting_array_string = setting_array
      for factor_index, factor in enumerate(plan.factors()):
        modality_indexes = np.where(getattr(plan, factor)==setting_array_string[factor_index])
        if len(modality_indexes[0])>0:
          setting_array[factor_index] = modality_indexes[0][0]
        else:
          print(f'Unable to identify {setting_array_string[factor_index]} as a modality of factor {factor}')
          raise SystemExit
         

    if setting_array:
      self._setting = copy.deepcopy(setting_array)
    else:
      self._setting = copy.deepcopy(plan._setting)

    for factor_index, factor in enumerate(plan.factors()):
      # print(self._setting[fi])
      # print(f)
      self.__setattr__(factor, getattr(plan, factor)[self._setting[factor_index]])

  def __str__(self):
    """returns a one-liner str with a readable description
    of the Factor object or the current setting.

  	returns a one-liner str with a readable description
    of the Factor object or the current setting if in an iterable.

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
    return self.identifier(sort=False, singleton=True, default=True)

  def identifier(
    self,
    style = 'long',
    sort = True,
    factor_separator = '+',
    modality_separator = '=',
    singleton = True,
    default = False,
    hide = None
    ):

    """return a one-liner str or a list of str
    that describes a setting or a :class:`~doce.Plan` object.

  	Return a one-liner str or a list of str that describes
    a setting or a :class:`~doce.Plan` object with a high degree of flexibility.

  	Parameters
  	----------

    style: str (optional)
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
      if True, also consider couple of factor/modality
      where the modality is explicitly set to be
      a default value for this factor using :meth:`doce.Plan.default`.

      if False, do not show them (default).

    hide: list of str
      list the factors that should not be considered.

    factor_separator: str
      factor_separator used to concatenate the factors, default is '|'.

    factor_separator: str
      factor_separator used to concatenate
      the factor and modality value, default is '='.

  	See Also
  	--------

    doce.Plan.default

    doce.util.compress_name

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
    ...   print(setting.identifier())
    four=d+one=a+three=c+two=1
    >>> # list style
    >>> print(setting.identifier('list'))
    ['four=d', 'one=a', 'three=c', 'two=1']
    >>> # hashed version of the default display
    >>> print(setting.identifier('hash'))
    4474b298d3b23000e739e888042dab2b
    >>> # do not apply sorting of the factor
    >>> print(setting.identifier(sort=False))
    one=a+two=1+three=c+four=d
    >>> # specify a factor_separator
    >>> print(setting.identifier(factor_separator=' '))
    four=d one=a three=c two=1
    >>> # do not show some factors
    >>> print(setting.identifier(hide=['one', 'three']))
    four=d+two=1
    >>> # do not show factors with only one modality
    >>> print(setting.identifier(singleton=False))
    one=a+three=c+two=1
    >>> delattr(p, 'four')
    >>> for setting in p.select([0, 0, 0]):
    ...   print(setting.identifier())
    one=a+three=none+two=0

    >>> # set the default value of factor one to a
    >>> p.default('one', 'a')
    >>> for setting in p.select([0, 1, 1]):
    ...   print(setting.identifier())
    three=c+two=1
    >>> # do not hide the default value in the description
    >>> print(setting.identifier(default=True))
    one=a+three=c+two=1

    >>> p.optional_parameter = ['value_one', 'value_two']
    >>> for setting in p.select([0, 1, 1, 0]):
    ...   print(setting.identifier())
    optional_parameter=value_one+three=c+two=1
    >>> delattr(p, 'optional_parameter')

    >>> p.optional_parameter = ['value_one', 'value_two']
    >>> for setting in p.select([0, 1, 1, 0]):
    ...   print(setting.identifier())
    optional_parameter=value_one+three=c+two=1

    """
    if not hide:
      hide = []
    identifier = []
    factors = self._plan.factors()
    # if isinstance(hide, str):
    #   hide=[hide]
    # elif isinstance(hide, int) :
    #   hide=[factors[hide]]
    # elif hide and isinstance(hide, list) and isinstance(hide[0], int) :
    #   for oi, o in enumerate(hide):
    #     hide[oi]=factors[o]
    if sort:
      factors = sorted(factors)
    for factor in factors:
      if factor[0] != '_' and \
         getattr(self, factor) is not None and \
         factor not in hide:
        if (singleton or factor in self._plan._non_singleton) and \
           (default or not hasattr(self._plan._default, factor) or \
           (not default and hasattr(self._plan._default, factor) and \
           getattr(self._plan._default, factor) != getattr(self, factor))):
          # identifier.append(f)
          # print(str(getattr(self, f)))
          if isinstance(getattr(self, factor), float):
            modality = np.format_float_positional(getattr(self, factor))
          else:
            modality = str(getattr(self, factor))
          identifier.append(factor+modality_separator+modality)
    if 'list' not in style:
      identifier = factor_separator.join(identifier)
      if style == 'hash':
        identifier  = hashlib.md5(identifier.encode("utf-8")).hexdigest()
    return identifier

  def replace(self, factor, value=None, positional=0, relative=0):
    """returns a new doce.Plan object with one factor with modified modality.

    Returns a new doce.Plan object with one factor with modified modality.
    The value of the requested new modality can requested by 3 exclusive means:
    its value, its position in the modality array, or its relative position
    in the array with respect to the position of the current modality.

    Parameters
    ----------

    factor: int or str
      if int, considered as the index inside an array of the factors
      sorted by order of definition.

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
    >>> # the same setting but with the factor 'two' set to
    >>> # modality of relative index -1 with respect to
    >>> # the modality index of the current setting
    >>> print(setting.replace('two', relative=-1))
    one=b+two=1
    """

    # get factor index
    if isinstance(factor, str):
      factor = self._plan.factors().index(factor)
    # get modality index
    if value is not None:
      factor_name = self._plan.factors()[factor]
      modalities = self._plan.__getattribute__(factor_name)
      positional, = np.where(modalities == value)
      positional = positional[0] # assumes no repetion

    setting = copy.deepcopy(self._setting)
    if relative:
      setting[factor] += relative
    else:
      setting[factor] = positional
    if setting[factor]< 0 or setting[factor] >= self._plan.nb_modalities(factor):
      print('Unable to find the requested modality.')
      return None
    return Setting(self._plan, setting)

  def perform(
    self,
    function,
    experiment,
    log_file_name,
    *parameters
    ):
    """run the function given as parameter for the setting.

  	Helper function for the method :meth:`~doce.Plan.do`.

  	See Also
  	--------

    doce.Plan.do

    """
    failed = 0
    if experiment.skip_setting(self) :
      message = 'Metrics for setting '+self.identifier()+' already available. Skipping...'
      print(message)
      if log_file_name:
        logging.info(message)
    else:
      try:
        function(self, experiment, *parameters)
      except Exception as exception:
        if log_file_name:
          failed = 1
          logging.info('Failed setting: %s', self.identifier())
          logging.info(traceback.format_exc())
        else:
          print('Failed setting: '+self.identifier())
          raise exception
    return failed

  def remove_factor(self, factor):
    """returns a copy of the setting where the specified factor is removed.

    Parameters
    ----------

    factor: str
      the name of the factor.

    """
    setting_copy = copy.deepcopy(self)
    delattr(setting_copy, factor)
    return setting_copy


if __name__ == '__main__':
  import doctest
  doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
  # doctest.run_docstring_examples(Setting.id, globals())
