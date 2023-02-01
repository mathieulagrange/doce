"""Handle information of an experiment of the doce module."""

import types
import inspect
import os
import time
import datetime
import ast
import glob
import copy
import numpy as np
import doce.util as eu
import doce

class Experiment():
  """Stores high level information about the experiment and tools
  to control the processing and storage of data.

  The experiment class displays high level information about the experiment
  such as its name, description, author, author's email address, and run identification.

  Information about storage of data is specified using the experiment.path name_space.
  It also stores one or several Plan objects and a Metric object to respectively specify
  the experimental plans and the metrics considered in the experiment.

  See Also
  --------

  doce.Plan, doce.metric.Metric

  Examples
  --------

  >>> import doce
  >>> e=doce.Experiment()
  >>> e.name='my_experiment'
  >>> e.author='John Doe'
  >>> e.address='john.doe@no-log.org'
  >>> e.path.processing='/tmp'
  >>> print(e)
    name: my_experiment
    description
    author: John Doe
    address: john.doe@no-log.org
    version: 0.1
    status:
      run_id: ...
      verbose: 0
    selector: []
    parameter
    metric
    path:
      code_raw: ...
      code: ...
      archive_raw:
      archive:
      export_raw: export
      export: export
      processing_raw: /tmp
      processing: /tmp
    host: []


  Each level can be complemented with new members to store specific information:

  >>> e.specific_info = 'stuff'
  >>> import types
  >>> e.my_data = types.SimpleNamespace()
  >>> e.my_data.info1= 1
  >>> e.my_data.info2= 2
  >>> print(e)
    name: my_experiment
    description
    author: John Doe
    address: john.doe@no-log.org
    version: 0.1
    status:
      run_id: ...
      verbose: 0
    selector: []
    parameter
    metric
    path:
      code_raw: ...
      code: ...
      archive_raw:
      archive:
      export_raw: export
      export: export
      processing_raw: /tmp
      processing: /tmp
    host: []
    specific_info: stuff
    my_data:
      info1: 1
      info2: 2
  """

  def __init__(
    self, **description
    ):
    # list of attributes
    self._atrs = []
    self._plan = doce.Plan('test')
    self._plans = []
    self.name = ''
    self.description = ''
    self.author = 'no name'
    self.address = 'noname@noorg.org'
    self.version = '0.1'

    self.status = types.SimpleNamespace()
    self.status.run_id = str(
      int((time.time()-datetime.datetime(2020,1,1,0,0).timestamp())/60)
      )
    self.status.verbose = 0
    self.selector = []

    self.parameter = types.SimpleNamespace()
    self.metric = doce.Metric()
    self.path = Path()
    self.path.code = os.getcwd()
    self.path.archive = ''
    self.path.export = 'export'
    self._doce_paths = ['export', 'export_raw', 'archive', 'archive_raw', 'code', 'code_raw']
    self.host = []
    self._archive_path = ''
    self._gmail_id = 'expcode.mailer'
    self._gmail_app_password = 'tagsqtlirkznoxro'
    self._default_server_run_argument =  {}
    self._resume = False
    self._check_setting_length = True

    self._display = types.SimpleNamespace()
    self._display.export_png = 'wkhtmltoimage' # could be 'chrome' or 'matplotlib'
    self._display.export_pdf = 'wkhtmltopdf' # could be 'chrome' or 'latex'
    self._display.factor_format_in_reduce = 'long'
    self._display.metric_format_in_reduce = 'long'
    self._display.metric_precision = 2
    self._display.factor_format_in_reduce_length = 2
    self._display.metric_format_in_reduce_length = 2
    self._display.show_row_index = True
    self._display.highlight = True
    self._display.bar = False
    self._display.pValue = 0.05

    for field, value in description.items():
      self.__setattr__(field, value)

    self.__setattr__('metric', doce.Metric())

  def __setattr__(
    self,
    name,
    value
    ):
    if not hasattr(self, name) and name[0] != '_':
      self._atrs.append(name)
    return object.__setattr__(self, name, value)

  def set_path(
    self,
    name,
    path,
    force=False
    ):
    """Create directories whose path described in experiment.path are not reachable.

    For each path set in experiment.path, create the directory if not reachable.
    The user may be prompted before creation.

  	Parameters
  	----------

    force : bool
      If True, do not prompt the user before creating the missing directories.

      If False, prompt the user before creation of each missing directory (default).

    Examples
    --------

    >>> import doce
    >>> import os
    >>> e=doce.Experiment()
    >>> e.name = 'experiment'
    >>> e.set_path('processing', f'/tmp/{e.name}/processing', force=True)
    >>> e.set_path('output', f'/tmp/{e.name}/output', force=True)
    >>> os.listdir(f'/tmp/{e.name}')
    ['processing', 'output']
    """
    # for sns in self.__getattribute__('path').__dict__.keys():
    self.path.__setattr__(name, path)

    path = os.path.abspath(os.path.expanduser(path))
    if path:
      if path.endswith('.h5'):
        path = os.path.dirname(os.path.abspath(path))
      else:
        if not path.endswith('/'):
          if not path.endswith('\\'):
            if '\\' in path:
              path = f'{path}\\'
              self.path.__setattr__(name, path)
            else:
              path = f'{path}/'
              self.path.__setattr__(name, path)

      if not os.path.exists(path):
        message = f'''The {name} path: {path} does not exist. \
        Do you want to create it ?'''
        if force or doce.util.query_yes_no(message):
          os.makedirs(path)
          if not force:
            print('Path succesfully created.')

  def __str__(
    self,
    style='str'
    ):
    """Provide a textual description of the experiment

    List all members of the class and theirs values

    parameters
    ----------
    style : str
      If 'str', return the description as a string.

      If 'html', return the description with an html format.

  	Returns
  	-------
    description : str
        If style == 'str' : a carriage return separated enumeration
        of the members of the class experiment.

        If style == 'html' : an html version of the description

  	Examples
  	--------

    >>> import doce
    >>> print(doce.Experiment())
    name
    description
    author: no name
    address: noname@noorg.org
    version: 0.1
    status:
      run_id: ...
      verbose: 0
    selector: []
    parameter
    metric
    path:
      code_raw: ...
      code: ...
      archive_raw:
      archive:
      export_raw: export
      export: export
    host: []

    >>> import doce
    >>> doce.Experiment().__str__(style='html')
        '<div>name</div><div>description</div><div>author: no name</div><div>address: noname@noorg.org</div><div>version: 0.1</div><div>status:</div><div>  run_id: ...</div><div>  verbose: 0</div><div>selector: []</div><div>parameter</div><div>metric</div><div>path:</div><div>  code_raw: ...</div><div>  code: ...</div><div>  archive_raw: </div><div>  archive: </div><div>  export_raw: export</div><div>  export: export</div><div>host: []</div><div></div>'
    """
    description = ''
    for atr in self._atrs:
      if not isinstance(inspect.getattr_static(self, atr), types.FunctionType):
        if isinstance(self.__getattribute__(atr), (types.SimpleNamespace, Path)):
          description += atr
          if len(self.__getattribute__(atr).__dict__.keys()):
            description+=':'
          description+='\r\n'
          for sns in self.__getattribute__(atr).__dict__.keys():
            description+=f'  {sns}: {str(self.__getattribute__(atr).__getattribute__(sns))}\r\n'
        elif isinstance(self.__getattribute__(atr), (str, list)):
          description+=atr
          if str(self.__getattribute__(atr)):
            description += f': {str(self.__getattribute__(atr))}'
          description += '\r\n'
        else:
          description+=atr
          if str(self.__getattribute__(atr)):
            description += f': \r\n{str(self.__getattribute__(atr))}'
          description += '\r\n'
    if style == 'html':
      desc = description.replace('\r\n', '</div><div>').replace('\t', '&emsp;')
      description = f'<div>{desc}</div>'
    return description

  def send_mail(
    self,
    title='',
    body=''):
    """Send an email to the email address given in experiment.address.

    Send an email to the experiment.address email address using the smtp service from gmail.
    For privacy, please consider using a dedicated gmail account
    by setting experiment._gmail_id and experiment._gmail_app_password.
    For this, you will need to create a gmail account, set two-step validation
    and allow connection with app password.

    See https://support.google.com/accounts/answer/185833?hl=en for reference.

    Parameters
    ----------

    title : str
      the title of the email in plain text format

    body : str
      the body of the email in html format

    Examples
    --------
    >>> import doce
    >>> e=doce.Experiment()
    >>> e.address = 'john.doe@no-log.org'
    >>> e.send_mail('hello', '<div> good day </div>')
    Sent message entitled: [doce]  id ... hello ...

    """

    import smtplib

    header = f'''From: doce mailer <{self._gmail_id}@gmail.com> \r\nTo: {self.author} {self.address}\r\nMIME-Version: 1.0 \r\nContent-type: text/html \r\nSubject: [doce] {self.name} id {self.status.run_id} {title}\r\n'''

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(f'{self._gmail_id}@gmail.com', self._gmail_app_password)
    exp_desc = self.__str__(style = 'html')
    server.sendmail(self._gmail_id, self.address, f'{header}{body}<h3> {exp_desc}</h3>')
    server.quit()
    print(f'''Sent message entitled: [doce] {self.name} id {self.status.run_id} \
     {title} at {time.ctime(time.time())}''')

  def perform(
    self,
    selector,
    function=None,
    *parameters,
    nb_jobs=1,
    progress='d',
    log_file_name='',
    mail_interval=0,
    tag=''
    ):
    r"""Operate the function with parameters on the :term:`settings<setting>` set
    generated using :term:`selector`.

    Operate a given function on the setting set generated using selector.
    The setting set can be browsed in parallel by setting nb_jobs>1.
    If log_file_name is not empty, a faulty setting do not stop the execution,
    the error is stored and another setting is executed. If progress is set to True,
    a graphical display of the progress through the setting set is displayed.

    This function is essentially a wrapper to the function :meth:`doce.Plan.do`.

    Parameters
    ----------

    selector : a list of literals or a list of lists of literals
      :term:`selector` used to specify the :term:`settings<setting>` set

    function : function(:class:`~doce.Plan`, :class:`~doce.Experiment`, \*parameters) (optional)
      A function that operates on a given setting within the experiment environnment
      with optional parameters.

      If None, a description of the given setting is shown.

    *parameters : any type (optional)
      parameters to be given to the function.

    nb_jobs : int > 0 (optional)
      number of jobs.

      If nb_jobs = 1, the setting set is browsed sequentially in a depth first
      traversal of the settings tree (default).

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

    mail_interval : float (optional)
      interval for sending email about the status of the run.

      If 0, no email is sent (default).

      It >0, an email is sent as soon as an setting is done and the difference
      between the current time and the time the last mail was sent is larger than mail_interval.
    
    tag : string (optional)
      specify a tag to be added to the output names

    See Also
    --------

    doce.Plan.do

    Examples
    --------

    >>> import time
    >>> import random
    >>> import doce

    >>> e=doce.Experiment()
    >>> e.add_plan('plan', factor1=[1, 3], factor2=[2, 5])

    >>> # this function displays the sum of the two modalities of the current setting
    >>> def my_function(setting, experiment):
    ...  print(f'{setting.factor1}+{setting.factor2}={setting.factor1+setting.factor2}')

    >>> # sequential execution of settings
    >>> nb_failed = e.perform([], my_function, nb_jobs=1, progress='')
    1+2=3
    1+5=6
    3+2=5
    3+5=8
    >>> # arbitrary order execution of settings due to the parallelization
    >>> nb_failed = e.perform([], my_function, nb_jobs=3, progress='') # doctest: +SKIP
    3+2=5
    1+5=6
    1+2=3
    3+5=8
    """

    return self._plan.select(selector).perform(
      function,
      self,
      *parameters,
      nb_jobs=nb_jobs,
      progress=progress,
      log_file_name=log_file_name,
      mail_interval=mail_interval
      )

  def select(self, selector, show=False, plan_order_factor=None):
    experiment_id = 'all'
    if '/' in selector:
      selector_split = selector.split('/')
      experiment_id = selector_split[0]
      if len(selector_split)>1:
        selector = selector_split[1]
        try:
          selector = ast.literal_eval(selector)
        except:
          pass
      else:
        selector = ''
    self.selector = selector

    plans = self.plans()
    if len(plans)==1:
      self._plan = getattr(self, plans[0])
    else:
      if experiment_id == 'all':
        o_plans = []
        for plan in plans:
          if show:
            print(f'Plan {plan}:')
            print(getattr(self, plan).as_panda_frame())
          o_plans.append(getattr(self, plan))
        self._plan = self._plan.merge(o_plans)
        if show and len(plans)>1:
          print('Those plans can be selected using the selector parameter.')
          print('Otherwise the merged plan is considered: ')
      else:
        if experiment_id.isnumeric():
          experiment_id = plans[int(experiment_id)]
        print(f'Plan {experiment_id} is selected')
        self._plan = getattr(self, experiment_id)
    self._plan.check()

    if plan_order_factor:
      self._plan = self._plan.order_factor(plan_order_factor)
    if show:
      print(self._plan.as_panda_frame())
    if self._check_setting_length:
      self._plan.check_length()
    return self._plan.select(selector)

  def clean_data_sink(
    self,
    path,
    selector=None,
    reverse=False,
    force=False,
    keep=False,
    wildcard='*',
    setting_encoding=None,
    archive_path = None,
    verbose=0
    ):
    r""" Perform a cleaning of a data sink (directory or h5 file).

    This method is essentially a wrapper to :meth:`doce._plan.clean_data_sink`.

    Parameters
    ----------

    path : str
      If has a / or \\\, a valid path to a directory or .h5 file.

      If has no / or \\\, a member of the name_space self.path.

    selector : a list of literals or a list of lists of literals (optional)
      :term:`selector` used to specify the :term:`settings<setting>` set

    reverse : bool (optional)
      If False, remove any entry corresponding to the setting set (default).

      If True, remove all entries except the ones corresponding to the setting set.

    force: bool (optional)
      If False, prompt the user before modifying the data sink (default).

      If True, do not prompt the user before modifying the data sink.

    wildcard : str (optional)
      end of the wildcard used to select the entries to remove or to keep (default: '*').

    setting_encoding : dict (optional)
      format of the identifier describing the :term:`setting`.
      Please refer to :meth:`doce.Plan.identifier` for further information.

    archive_path : str (optional)
      If not None, specify an existing directory where the specified data will be moved.

      If None, the path doce.Experiment._archive_path is used (default).

    See Also
    --------

    doce._plan.clean_data_sink, doce.Plan.id

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import os
    >>> e=doce.Experiment()
    >>> e.set_path('output', '/tmp/test', force=True)
    >>> e.add_plan('plan', factor1=[1, 3], factor2=[2, 4])
    >>> def my_function(setting, experiment):
    ...   np.save(f'{experiment.path.output}{setting.identifier()}_sum.npy', setting.factor1+setting.factor2)
    ...   np.save(f'{experiment.path.output}{setting.identifier()}_mult.npy', setting.factor1*setting.factor2)
    >>> nb_failed = e.perform([], my_function, progress='')
    >>> os.listdir(e.path.output)
    ['factor1=1+factor2=4_mult.npy', 'factor1=1+factor2=4_sum.npy', 'factor1=3+factor2=4_sum.npy', 'factor1=1+factor2=2_mult.npy', 'factor1=1+factor2=2_sum.npy', 'factor1=3+factor2=2_mult.npy', 'factor1=3+factor2=4_mult.npy', 'factor1=3+factor2=2_sum.npy']

    >>> e.clean_data_sink('output', [0], force=True)
    >>> os.listdir(e.path.output)
    ['factor1=3+factor2=4_sum.npy', 'factor1=3+factor2=2_mult.npy', 'factor1=3+factor2=4_mult.npy', 'factor1=3+factor2=2_sum.npy']

    >>> e.clean_data_sink('output', [1, 1], force=True, reverse=True, wildcard='*mult*')
    >>> os.listdir(e.path.output)
    ['factor1=3+factor2=4_sum.npy', 'factor1=3+factor2=4_mult.npy', 'factor1=3+factor2=2_sum.npy']

    Here, we remove all the files that match the wildcard *mult*
    in the directory /tmp/test that do not correspond to the settings
    that have the first factor set to the second modality and the second factor
    set to the second modality.

    >>> import doce
    >>> import tables as tb
    >>> e=doce.Experiment()
    >>> e.set_path('output', '/tmp/test.h5')
    >>> e.add_plan('plan', factor1=[1, 3], factor2=[2, 4])
    >>> e.set_metric(name = 'sum')
    >>> e.set_metric(name = 'mult')
    >>> def my_function(setting, experiment):
    ...   h5 = tb.open_file(experiment.path.output, mode='a')
    ...   sg = experiment.add_setting_group(
    ...     h5, setting,
    ...     output_dimension={'sum': 1, 'mult': 1})
    ...   sg.sum[0] = setting.factor1+setting.factor2
    ...   sg.mult[0] = setting.factor1*setting.factor2
    ...   h5.close()
    >>> nb_failed = e.perform([], my_function, progress='')
    >>> h5 = tb.open_file(e.path.output, mode='r')
    >>> print(h5)
    /tmp/test.h5 (File) ''
    Last modif.: '...'
    Object Tree:
    / (RootGroup) ''
    /factor1=1+factor2=2 (Group) 'factor1=1+factor2=2'
    /factor1=1+factor2=2/mult (Array(1,)) 'mult'
    /factor1=1+factor2=2/sum (Array(1,)) 'sum'
    /factor1=1+factor2=4 (Group) 'factor1=1+factor2=4'
    /factor1=1+factor2=4/mult (Array(1,)) 'mult'
    /factor1=1+factor2=4/sum (Array(1,)) 'sum'
    /factor1=3+factor2=2 (Group) 'factor1=3+factor2=2'
    /factor1=3+factor2=2/mult (Array(1,)) 'mult'
    /factor1=3+factor2=2/sum (Array(1,)) 'sum'
    /factor1=3+factor2=4 (Group) 'factor1=3+factor2=4'
    /factor1=3+factor2=4/mult (Array(1,)) 'mult'
    /factor1=3+factor2=4/sum (Array(1,)) 'sum'
    >>> h5.close()

    >>> e.clean_data_sink('output', [0], force=True)
    >>> h5 = tb.open_file(e.path.output, mode='r')
    >>> print(h5)
    /tmp/test.h5 (File) ''
    Last modif.: '...'
    Object Tree:
    / (RootGroup) ''
    /factor1=3+factor2=2 (Group) 'factor1=3+factor2=2'
    /factor1=3+factor2=2/mult (Array(1,)) 'mult'
    /factor1=3+factor2=2/sum (Array(1,)) 'sum'
    /factor1=3+factor2=4 (Group) 'factor1=3+factor2=4'
    /factor1=3+factor2=4/mult (Array(1,)) 'mult'
    /factor1=3+factor2=4/sum (Array(1,)) 'sum'
    >>> h5.close()

    >>> e.clean_data_sink('output', [1, 1], force=True, reverse=True, wildcard='*mult*')
    >>> h5 = tb.open_file(e.path.output, mode='r')
    >>> print(h5)
    /tmp/test.h5 (File) ''
    Last modif.: '...'
    Object Tree:
    / (RootGroup) ''
    /factor1=3+factor2=4 (Group) 'factor1=3+factor2=4'
    /factor1=3+factor2=4/mult (Array(1,)) 'mult'
    /factor1=3+factor2=4/sum (Array(1,)) 'sum'
    >>> h5.close()

    Here, the same operations are conducted on a h5 file.
    """

    if '/' not in path and '\\' not in path:
      path = self.__getattribute__('path').__getattribute__(path)
    if path:
      self._plan.select(selector).clean_data_sink(
        path,
        reverse=reverse,
        force=force,
        keep=keep,
        wildcard=wildcard,
        setting_encoding=setting_encoding,
        archive_path=archive_path,
        verbose=verbose
        )

  def plans(self):
    # names = []
    # for attribute in dir(self):
    #   if attribute[0] != '_' and isinstance(getattr(self, attribute), doce.Plan):
    #     names.append(attribute)
    return self._plans

  def add_plan(self, name, **kwargs):
    self.__setattr__(name, doce.Plan(name, **kwargs))
    self._plan = getattr(self, name)
    self._plans.append(name)
  
  def get_current_plan(self):
    return self._plan

  def set_metric(self,
    name = None,
    output = None,
    func = np.mean,
    path = 'output',
    percent=False,
    higher_the_better=False,
    lower_the_better=False,
    significance=False,
    precision=None,
    description = '',
    unit = ''
    ):

    if name is None:
      raise Exception('A metric must of a name.')
    if not isinstance(name, str):
      raise Exception('A metric name must be a string.')
    if significance and not lower_the_better and not higher_the_better:
      raise Exception('Significance analysis requires either lower_the_better or higher_the_better to set be to True.')
    if precision is None:
      precision = self._display.metric_precision
    if output is None:
      output = name

    self.metric.__setattr__(name, {
      'name':name,
      'output':output,
      'path':path,
      'func':func,
      'percent':percent,
      'higher_the_better':higher_the_better,
      'lower_the_better':lower_the_better,
      'significance': significance,
      'precision':precision,
      'description':description,
      'unit':unit
      })

  
  def default(self, plan='', factor='', modality=''):
    getattr(self, plan).default(factor, modality)

  def skip_setting(self, setting):
    if self._resume:
      for path in self.__getattribute__('path').__dict__.keys():
        if path.endswith('.h5'):
          print('todo')
        else:
          if path not in self._doce_paths:
            check = glob.glob(f'{self.path.__getattribute__(path)}{setting.identifier()}_*.npy')
            if check:
              return True
    return False

  def get_output(self, output='', selector=None, path='', tag='', plan=None):
    """ Get the output vector from an .npy or a group of a .h5 file.

    Get the output vector as a numpy array from an .npy or a group of a .h5 file.

    Parameters
    ----------

    output: str
      The name of the output. 

    selector: list
      Settings selector.

    path: str
      Name of path as defined in the experiment,
      or a valid path to a directory in the case of .npy storage,
      or a valid path to an .h5 file in the case of hdf5 storage.

    plan: str
      Name of plan to be considered.

    Returns
    -------

    setting_metric: list of np.Array
      stores for each valid setting an np.Array with the values of the metric selected.

    setting_description: list of list of str
      stores for each valid setting, a compact description of the modalities of each factors.
      The factors with the same modality accross all the set of settings is stored
      in constant_setting_description.

    constant_setting_description: str
      compact description of the factors with the same modality accross all the set of settings.

    Examples
    --------

    >>> import doce
    >>> import numpy as np
    >>> import pandas as pd

    >>> experiment = doce.experiment.Experiment()
    >>> experiment.name = 'example'
    >>> experiment.set_path('output', '/tmp/{experiment.name}/', force=True)
    >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
    >>> experiment.set_metric(name = 'm1_mean', output = 'm1', func = np.mean)
    >>> experiment.set_metric(name = 'm1_std', output = 'm1', func = np.std)
    >>> experiment.set_metric(name = 'm2_min', output = 'm2', func = np.min)
    >>> experiment.set_metric(name = 'm2_argmin', output = 'm2', func = np.argmin)

    >>> def process(setting, experiment):
    ...  output1 = setting.f1+setting.f2+np.random.randn(100)
    ...  output2 = setting.f1*setting.f2*np.random.randn(100)
    ...  np.save(f'{experiment.path.output+setting.identifier()}_m1.npy', output1)
    ...  np.save(f'{experiment.path.output+setting.identifier()}_m2.npy', output2)
    >>> nb_failed = experiment.perform([], process, progress='')

    >>> (setting_output,
    ...  setting_description,
    ...  constant_setting_description
    ... ) = experiment.get_output(output = 'm1', selector = [1], path='output')
    >>> print(constant_setting_description)
    f1=2
    >>> print(setting_description)
    ['f2=1', 'f2=2', 'f2=3']
    >>> print(len(setting_output))
    3
    >>> print(setting_output[0].shape)
    (100,)
    """

    if plan:
      plan = getattr(self, plan)
    else:
      if len(self.plans()) > 1:
        o_plans = []
        for plan in self.plans():
          o_plans.append(getattr(self, plan))
        self._plan = self._plan.merge(o_plans)
      plan = self._plan

    if path:
      if not (r'\/' in path or r'\\' in path):
        path = getattr(self.path, path)
      return get_from_path(
        output,
        settings=plan.select(selector),
        path=path,
        tag=tag
        )
    data = []
    settings = []
    for path_iterator in self.path.__dict__:
      if not path.endswith('_raw'):
        path_iterator = getattr(self.path, path_iterator)
        (data_path, setting_path, header_path) = get_from_path(
          output,
          settings=plan.select(selector),
          path=path_iterator,
          tag=tag
          )
        if data_path:
          for data_setting in data_path:
            data.append(data_setting)
          for setting_description in setting_path:
            settings.append(setting_description)

    return (data, settings, header_path)

  def add_setting_group(
    self,   file_id,
    setting,
    output_dimension=None,
    setting_encoding=None
    ):
    """adds a group to the root of a valid py_tables Object in order to
    store the metrics corresponding to the specified setting.

    adds a group to the root of a valid py_tables Object in order to
    store the metrics corresponding to the specified setting.
    The encoding of the setting is used to set the name of the group.
    For each metric, a Floating point Pytable Array is created.
    For any metric, if no dimension is provided in the output_dimension dict,
    an expandable array is instantiated. If a dimension is available, 
    a static size array is instantiated.

    Parameters
    ----------

    file_id: py_tables file Object
    a valid py_tables file Object, leading to an .h5 file opened with writing permission.

    setting: :class:`doce.Plan`
    an instantiated Factor object describing a setting.

    output_dimension: dict
    for metrics for which the dimensionality of the storage vector is known,
    each key of the dict is a valid metric name and each corresponding value
    is the size of the storage vector.

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
    >>> experiment.set_metric(name = 'm1_mean', output = 'm1', func = np.mean)
    >>> experiment.set_metric(name = 'm1_std', output = 'm1', func = np.std)
    >>> experiment.set_metric(name = 'm2_min', output = 'm2', func = np.min)
    >>> experiment.set_metric(name = 'm2_argmin', output = 'm2', func = np.argmin)

    >>> def process(setting, experiment):
    ...  h5 = tb.open_file(experiment.path.output, mode='a')
    ...  sg = experiment.add_setting_group(h5, setting, output_dimension = {'m1':100})
    ...  sg.m1[:] = setting.f1+setting.f2+np.random.randn(100)
    ...  sg.m2.append(setting.f1*setting.f2*np.random.randn(100))
    ...  h5.close()
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
    """
    import tables as tb
    import warnings
    from tables import NaturalNameWarning
    warnings.filterwarnings('ignore', category=NaturalNameWarning)

    if not setting_encoding:
      setting_encoding={}
    #   setting_encoding={'factor_separator':'_', 'modality_separator':'_'}
    group_name = setting.identifier(**setting_encoding)
    # print(group_name)
    if not file_id.__contains__('/'+group_name):
      setting_group = file_id.create_group('/', group_name, str(setting))
    else:
      setting_group = file_id.root._f_get_child(group_name)
    for metric in self.metric.name():
      output = getattr(self.metric, metric)['output']
      if getattr(self.metric, metric)['description']:
        description = getattr(self.metric, metric)['description']
      else:
        description = output

      if getattr(self.metric, metric)['unit']:
        description += ' in ' + getattr(self.metric, metric)['unit']

      if output_dimension and output in output_dimension:
        if not setting_group.__contains__(output):
          file_id.create_array(
            setting_group,
            output,
            np.zeros((output_dimension[output]))*np.nan,
            description)
      else:
        if setting_group.__contains__(output):
          setting_group._f_get_child(output)._f_remove()
        file_id.create_earray(setting_group, output, tb.Float64Atom(), (0,), description)

    return setting_group


def get_from_path(
  metric,
  settings = None,
  path = '',
  tag='',
  setting_encoding=None,
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
    In the case of .npy storage, a valid path to the main directory.
    In the case of .h5 storage, a valid path to an .h5 file.

  setting_encoding : dict
    Encoding of the setting. See doce.Plan.id for references.

  verbose : bool
    In the case of .npy metric storage, if verbose is set to True,
    print the file_name seeked for the metric.

    In the case of .h5 metric storage, if verbose is set to True,
    print the group seeked for the metric.

  Returns
  -------

  setting_metric: list of np.Array
    stores for each valid setting an np.Array with the values of the metric selected.

  setting_description: list of list of str
    stores for each valid setting, a compact description of the modalities of each factors.
    The factors with the same modality accross all the set of settings is stored in constant_setting_description.

  constant_setting_description: str
    compact description of the factors with the same modality accross all the set of settings.

  Examples
  --------

  >>> import doce
  >>> import numpy as np
  >>> import pandas as pd

  >>> experiment = doce.experiment.Experiment()
  >>> experiment.name = 'example'
  >>> experiment.set_path('output', f'/tmp/{experiment.name}/', force=True)
  >>> experiment.add_plan('plan', f1 = [1, 2], f2 = [1, 2, 3])
  >>> experiment.set_metric(name = 'm1_mean', output = 'm1', func = np.mean)
  >>> experiment.set_metric(name = 'm1_std', output = 'm1', func = np.std)
  >>> experiment.set_metric(name = 'm2_min', output = 'm2', func = np.min)
  >>> experiment.set_metric(name = 'm2_argmin', output = 'm2', func = np.argmin)
  >>> def process(setting, experiment):
  ...  metric1 = setting.f1+setting.f2+np.random.randn(100)
  ...  metric2 = setting.f1*setting.f2*np.random.randn(100)
  ...  np.save(f'{experiment.path.output}{setting.identifier()}_m1.npy', metric1)
  ...  np.save(f'{experiment.path.output}{setting.identifier()}_m2.npy', metric2)
  >>> nb_failed = experiment.perform([], process, progress='')

  >>> (setting_metric,
  ...  setting_description,
  ...  constant_setting_description) = get_from_path(
  ...      'm1',
  ...      experiment._plan.select([1]),
  ...      experiment.path.output)
  >>> print(constant_setting_description)
  f1=2
  >>> print(setting_description)
  ['f2=1', 'f2=2', 'f2=3']
  >>> print(len(setting_metric))
  3
  >>> print(setting_metric[0].shape)
  (100,)
  """

  import tables as tb
  import warnings
  from tables import NaturalNameWarning
  warnings.filterwarnings('ignore', category=NaturalNameWarning)

  setting_metric = []
  setting_descriptions = []
  if not setting_encoding:
    setting_encoding = {}
  setting_description_format = copy.deepcopy(setting_encoding)
  setting_description_format['style'] = 'list'
  setting_description_format['default'] = True
  setting_description_format['sort'] = False

  if isinstance(path, str):
    if path.endswith('.h5'):
      if tag:
        path = path[:-3]+'_'+tag+'.h5'
      h5_fid = tb.open_file(path, mode='r')
      for setting in settings:
        if h5_fid.root.__contains__(setting.identifier(**setting_encoding)):
          if verbose:
            print(f'Found group {setting.identifier(**setting_encoding)}')
          setting_group = h5_fid.root._f_get_child(setting.identifier(**setting_encoding))
          if setting_group.__contains__(metric):
            setting_metric.append(np.array(setting_group._f_get_child(metric)))
            setting_descriptions.append(setting.identifier(**setting_description_format))
        elif verbose:
          print(f'** Unable to find group {setting.identifier(**setting_encoding)}')
      h5_fid.close()
    else:
      if tag:
        path += tag+'/'
      for setting in settings:
        file_name = f'{path}{setting.identifier(**setting_encoding)}_{metric}.npy'
        if os.path.exists(file_name):
          if verbose:
            print(f'Found {file_name}')
          setting_metric.append(np.load(file_name))
          setting_descriptions.append(setting.identifier(**setting_description_format))
        elif verbose:
          print(f'** Unable to find {file_name}')

  (setting_descriptions, _,
  constant_setting_description,
  _) = eu.prune_setting_description(setting_descriptions, show_unique_setting = True)

  for setting_description_index, setting_description in enumerate(setting_descriptions):
    setting_descriptions[setting_description_index] = ', '.join(setting_description)

  return (setting_metric, setting_descriptions, constant_setting_description)
  
class Path:
  """handle storage of path to disk """
  def __setattr__(
    self,
    name,
    value
    ):
    object.__setattr__(self, f'{name}_raw', value)
    object.__setattr__(
      self,
      name,
      os.path.expanduser(value)
      )


if __name__ == '__main__':
  import doctest
  doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
