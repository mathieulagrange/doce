import sys
import re

# def special_caracter_natural_naming(modality):
#   modifier = {' ': 'space',
#               '!': 'exclamationmark',
#               '"': 'doublequote',
#               '#': 'sharp',
#               '$': 'dollar',
#               '%': 'percent',
#               '&': 'ampersand',
#               '\'': 'simplequote',
#               '(': 'leftparenthesis',
#               ')': 'rightparenthesis',
#               '*': 'asterisk',
#               '+': 'plus',
#               ',': 'comma',
#               '-': 'dash',
#               '.': 'dot',
#               '/': 'slash',
#               ':': 'colon',
#               ';': 'semicolon',
#               '<': 'less',
#               '=': 'equal',
#               '>': 'greater',
#               '?': 'questionmark',
#               '@': 'arobace',
#               '[': 'leftbracket',
#               '\\': 'backslash',
#               ']': 'rightbracket',
#               '^': 'caret',
#               '_': 'underscore',
#               '`': 'acute',
#               '{': 'leftbrace',
#               '|': 'pipe',
#               '}': 'rightbrace',
#               '~': 'tilde'
#               }
#   for key, value in modifier.items():
#     modality = modality.replace(key, value)
#   if modality[-4:]=='dot0':
#     modality = modality[:-4]
#   return modality

def constant_column(
  table=None
):
  """detect which column(s) have the same value for all lines.

	Parameters
	----------

  table : list of equal size lists or None
    table of literals.

	Returns
	-------

  values : list of literals
    values of the constant valued columns, None if the column is not constant.

	Examples
	--------
  >>> import doce
  >>> table = [['a', 'b', 1, 2], ['a', 'c', 2, 2], ['a', 'b', 2, 2]]
  >>> doce.util.constant_column(table)
  ['a', None, None, 2]
  """

  indexes = [True] * len(table[0])
  values = [None] * len(table[0])

  for r in table:
      for cIndex, c in enumerate(r):
          if values[cIndex] is None and indexes[cIndex]:
              values[cIndex] = c
          elif values[cIndex] != c:
              indexes[cIndex] = False
              values[cIndex] = None
  return values

def prune_setting_description(setting_description, column_header = None, nb_column_factor=0, factor_display = 'long', show_unique_setting = False):
  """remove the columns corresponding to factors with only one modality from the setting_description and the column_header.

  Remove the columns corresponding to factors with only one modality from the setting_description and the column_header and describes the factors with only one modality in a separate string.

	Parameters
	----------

  setting_description: list of list of literals
    the body of the table.

  column_header: list of string (optional)
    the column header of the table.

  nb_column_factor: int (optional)
    the number of columns corresponding to factors (default 0).

  factor_display:
    type of description of the factors (default 'long'), see :meth:`doce.util.compress_description` for reference.

  show_unique_setting: bool
    If True, show the description of the unique setting in constant_setting_description.

	Returns
	-------

  setting_description: list of list of literals
    setting_description where the columns corresponding to factors with only one modality are removed.

  column_header: list of str
    column_header where the columns corresponding to factors with only one modality are removed.

  constant_setting_description: str
    description of the settings with constant modality.

  nb_column_factor: int
    number of factors in the new setting_description.

	Examples
	--------
  >>> import doce

  >>> header = ['factor_1', 'factor_2', 'metric_1', 'metric_2']
  >>> table = [['a', 'b', 1, 2], ['a', 'c', 2, 2], ['a', 'b', 2, 2]]
  >>> (setting_description, column_header, constant_setting_description, nb_column_factor) = doce.util.prune_setting_description(table, header, 2)
  >>> print(nb_column_factor)
  1
  >>> print(constant_setting_description)
  factor_1: a
  >>> print(column_header)
  ['factor_2', 'metric_1', 'metric_2']
  >>> print(setting_description)
  [['b', 1, 2], ['c', 2, 2], ['b', 2, 2]]
  """
  constant_setting_description = ''
  if setting_description:
    if nb_column_factor == 0:
      nb_column_factor = len(setting_description[0])
    if len(setting_description)>1:
      constant_value = constant_column(setting_description)
      # for si, s in enumerate(constant_value):
      #   if not column_header and si>0 and s is None:
      #     constant_value[si-1] = None
      cc_index = [i for i, x in enumerate(constant_value) if x is not None and i<nb_column_factor] # there is an issue here possibly with get
      nb_column_factor -= len(cc_index)
      for s in cc_index:
        if column_header:
          constant_setting_description += compress_description(column_header[s], factor_display)+': '+str(constant_value[s])+' '
        else:
          constant_setting_description += setting_description[0][s]+' '
      for s in sorted(cc_index, reverse=True):
        if column_header:
          column_header.pop(s)
        for r in setting_description:
          r.pop(s)
    else:
      constant_setting_description = ''
      if show_unique_setting:
        constant_setting_description = ' '.join(str(x) for x in setting_description[0]).strip()

  return (setting_description, column_header, constant_setting_description, nb_column_factor)


def compress_description(
  description,
  format='long',
  atom_length=2
  ):
  """ reduces the number of letters for each word in a given description structured with underscores (python_case) or capital letters (camel_case).

	Parameters
	----------
  description : str
    the structured description.

  format : str, optional
    can be 'long' (default), do not lead to any reduction, 'short_underscore' assumes python_case delimitation, 'short_capital' assumes camel_case delimitation, and 'short' attempts to perform reduction by guessing the type of delimitation.

	Returns
	-------

  compressed_description : str
    The compressed description.

	Examples
	--------

  >>> import doce
  >>> doce.util.compress_description('myVeryLongParameter', format='short')
  'myvelopa'
  >>> doce.util.compress_description('that_very_long_parameter', format='short', atom_length=3)
  'thaverlonpar'
  """

  if format == 'short':
    if '_' in description and not description.islower() and not description.isupper():
      print('The description '+description+' has underscores and capital. Explicitely states which delimeter shall be considered for reduction.')
      raise value_error
    elif '_' in description:
      format = 'short_underscore'
    else:
      format = 'short_capital'
  compressed_description = description
  if 'short_underscore' in format:
    compressed_description = ''.join([itf[0:atom_length] for itf in description.split('_')])
  if 'short_capital' in format:
    compressed_description = description[0:atom_length]+''.join([itf[0:atom_length] for itf in re.findall('[A-Z][^A-Z]*', description)]).lower()
  if '%' in description and not '%' in compressed_description :
    compressed_description += '%'
  if description[-1] == '-' and not compressed_description[-1] == '-':
    compressed_description += '-'
  return compressed_description

def query_yes_no(
  question,
  default="yes"
  ):
  """ask a yes/no question via input() and return their answer.

  The 'answer' return value is True for 'yes' or False for 'no'.

	Parameters
	----------

  question : str
    phrase presented to the user.
  default : str or None (optional)
    presumed answer if the user just hits <Enter>. It must be 'yes' (default), 'no' or None. The latter meaning an answer is required of the user.

	Returns
	-------

  answer : bool
    True if prompt is 'yes'.

    False if prompt is 'no'.
  """

  valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
  if default is None:
    prompt = " [y/n] "
  elif default == "yes":
    prompt = " [Y/n] "
  elif default == "no":
    prompt = " [y/N] "
  else:
    raise value_error("invalid default answer: '%s'" % default)

  while True:
    sys.stdout.write(question + prompt)
    choice = input().lower()
    if default is not None and choice == '':
      return valid[default]
    elif choice in valid:
      return valid[choice]
    else:
      sys.stdout.write("Please respond with 'yes' or 'no' "
                           "(or 'y' or 'n').\n")

def in_notebook():
  """detect if the experiment is running from Ipython notebook.
  """
  try:
    __IPYTHON__
    return True
  except NameError:
    return False

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
