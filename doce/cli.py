"""Handle interaction with the doce module using the command line interface."""

import sys
import argparse
import ast
import os
import copy
import subprocess
import shutil
import time
import re
import numpy as np
import inspect
import dataframe_image
import doce

def main(experiment = None, func = None, display_func = None):
  """This method shall be called from the main script of the experiment
  to control the experiment using the command line.

  This method provides a front-end for running a doce experiment.
  It should be called from the main script of the experiment.
  The main script must define the **experiment** object that will be called before processing
  and a **func** function that will be run for each setting.


  Examples

  Assuming that the file experiment_run.py contains:

  >>> import doce
  >>> if __name__ == "__main__":
  ...   doce.experiment.run() # doctest: +SKIP
  >>> def set(experiment, args=None):
  ...   experiment._plan.factor1=[1, 3]
  ...   experiment._plan.factor2=[2, 4]
  ...   return experiment
  >>> def step(setting, experiment):
  ...   print(setting.identifier())

  Executing this file with the --run option gives:

  $ python experiment_run.py -r
   factor1_1_factor2_2
   factor1_1_factor2_4
   factor1_3_factor2_2
   factor1_3_factor2_4

  Executing this file with the --help option gives:

  $ python experiment_run.py -h

  """

  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-A',
      '--archive',
      type=str,
      help=r'archive the selected  settings from a given path. \
      If the argument does not have / or \, the argument is interpreted as a member \
      of the experiments path. The files are copied to the path experiment.path.archive if set.',
      nargs='?',
      const=''
  )
  parser.add_argument(
      '-c',
      '--compute',
      type=int,
      help=r'perform computation. Integer parameter sets the number of jobs computed in parallel \
      (default to one core).',
      nargs='?',
      const=1
  )
  parser.add_argument(
      '-C',
      '--copy',
      help=r'copy codebase to the host defined by the host (-H) argument.',
      action='store_true'
  )
  parser.add_argument(
      '-d',
      '--display',
      type=str,
      help=r'display metrics. \
      If no parameter is given, consider the default display and show all metrics. \
      If the parameter contain a list of integers, use the default display \
      and show only the selected metrics defined by the integer list. \
      If the str parameter contain a name, run the display method with this name. \
      If the parameter is of the type factor:metric_numeric_id, organizes the table \
      with the modalities of the factor as columns \
      and display the metric number metric_numeric_id.',
      nargs='?',
      default='-1'
  )
  parser.add_argument(
      '-D',
      '--detached',
      help=r'Perform the computation in a detached mode, \
      meaning that if one setting fails, doce continues to loop over \
      the remaining settings to be computed.',
      action='store_true'
  )
  parser.add_argument(
      '-e',
      '--export',
      type=str,
      help=r'Export the display of reduced metrics \
      for different file types (html, png, pdf). If parameter is empty, all exports are made. \
      If parameter has a dot, interpreted as a filename which should be of support type. \
      If parameter has nothing before the dot, interpreted as file type, and experiment.name is used. \
      If parameter has no dot, interpreted as file name with no extension, \
      and all exports are made.',
      nargs='?',
      default='none'
  )
  parser.add_argument(
      '-f',
      '--files',
      help=r'list files.',
      action='store_true'
  )
  parser.add_argument(
      '-H',
      '--host',
      type=int,
      help=r'running on specified HOST. \
      Integer defines the index in the host array of the experiment. \
      -2 (default) runs attached on the local host, -1 runs detached on the local host through a screen, \
      -3 is a flag meaning that the experiment runs detached (no stop at failing settings).',
      default=-2)
  parser.add_argument(
      '-i',
      '--information',
      help=r'show information about the experiment.',
      action='store_true'
  )
  parser.add_argument(
      '-j',
      '--job',
      type=str,
      help=r'Launch one job per setting with provided template. Template must contain two keys. \
      one is the launch key with the command that is used for launching the job\
      <DOCE_LAUNCH>slurm<DOCE_LAUNCH>, and the other <DOCE_SETTING> match the location\
      where the doce command should be inserted. Jobs files are stored in the jobs folder. \
      If -c or --compute is set, a command is issued per job file and the jobs directory is deleted.',
      nargs='?',
      const=''
  )
  parser.add_argument(
      '-K',
      '--keep',
      type=str,
      help=r'keep only the selected settings \
      from a given path. If the argument does not have / or \, the argument is \
      interpreted as a member of the experiments path. Unwanted files are moved \
      to the path experiment.path.archive if set, deleted otherwise.',
      nargs='?',
      const=''
  )
  parser.add_argument(
      '-l',
      '--list',
      help=r'list settings.',
      action='store_true'
  )
  parser.add_argument(
      '-M',
      '--mail',
      help=r'send email at the beginning and end of the computation. \
      If a positive integer value x is provided, additional emails \
      are sent every x hours.',
      nargs='?',
      default='-1'
  )

  parser.add_argument(
      '-o',
      '--order',
      type=str,
      help=r'specify the order of the factors as a permutation array of indices. \
      For example -o \'[4, 3, 2, 1]\' invert the factors of a plan of 4 factors.',
      nargs='?',
      default='None'
  )

  parser.add_argument(
      '-p',
      '--plan',
      help=r'show the active plan of the experiment.',
      action='store_true'
  )
  parser.add_argument(
      '-P',
      '--progress',
      help=r'display progress bar. Argument controls the display of the current \
      setting: d alphanumeric description, s numeric selector, ds combination of \
      both (default d).',
      nargs='?',
      const='d'
  )
  parser.add_argument(
      '-R',
      '--remove',
      type=str,
      help=r'remove the selected  settings from a given path. \
      If the argument does \ not have / or \, the argument is interpreted \
      as a member of the experiments \ path. Unwanted files are moved \
      to the path experiment.path.archive if set, \ deleted otherwise.',
      nargs='?',
      const=''
  )
  parser.add_argument(
      '-s',
      '--select',
      type=str,
      help=r'selection of plan and settings, for example plan_name/factor1=modality2+factor4=modality1',
      default='[]'
  )
  parser.add_argument(
      '-S',
      '--skip',
      help=r'check availability of any metric of a given setting and skip \
      computation if available.',
      action='store_true')
  parser.add_argument(
      '-u',
      '--user_data',
      type=str,
      help=r'a dict specified as str (for example, \'{\"test\": 1}\') \
      that will be available in experiment.user_data (user_data.test=1).',
      default='{}'
  )

  parser.add_argument(
    '-t',
    '--tag',
    type=str,
    help=r'define a computation tag to be added to the names of the outputs.',
    default=''
  )

  parser.add_argument(
      '-v',
      '--version',
      help=r'print version',
      action='store_true'
  )
  parser.add_argument(
      '-V',
      '--verbose',
      help=r'level of verbosity (default 0: silent).',
      action='store_true'
  )
  args = parser.parse_args()

  if args.mail is None:
    args.mail = 0
  else:
    args.mail = float(args.mail)

  if args.export is None:
    args.export = 'all'
  if args.progress is None:
    args.progress = ''

  selector = re.sub(r"[\n\t\s]*", "", args.select)
  try:
    selector = ast.literal_eval(selector)
  except:
    pass

  # module = sys.argv[0][:-3]
  # try:
  #   config = importlib.import_module(module)
  # except:
  #   print(f'{sys.argv[0]} should implement a valid python module.')
  #   raise ValueError

  if not experiment:
    experiment = doce.Experiment()

  if args.tag:
    for path in experiment.path.__dict__.keys():
      if not path.endswith('_raw') and path != 'code' and path != 'archive'and path != 'export': 
        new_path = getattr(experiment.path, path)
        if new_path.endswith('.h5'):
          new_path = new_path[:-3]+'_'+args.tag+'.h5'
        else:
          new_path += '/'+args.tag
        experiment.set_path(path, new_path)
    # for path in experiment.path.__dict__.keys():
    #   print(path)
    #   print(getattr(experiment.path, path))

  if isinstance(args.user_data, dict):
    experiment.user_data = args.user_data

  if args.version:
    print("Experiment version " + experiment.version)
    exit(1)

  experiment.status.verbose = args.verbose
  experiment._resume = args.skip
  if args.order:
    plan_order_factor = ast.literal_eval(args.order)
  else:
    plan_order_factor = None
  experiment.select(selector, show=args.plan, plan_order_factor=plan_order_factor)

  if args.information:
    print(experiment)

  if args.list:
    experiment.perform(
        experiment.selector,
        progress='',
        function=lambda s,
        e: print(s)
    )

  def job_managment(setting, experiment):
    _, file_extension = os.path.splitext(experiment.job_template_file_name)
    job_file_name = 'jobs/'+setting.identifier()+file_extension

    job_template_file = open(experiment.job_template_file_name, 'r')
    job_template_lines = job_template_file.readlines()
    job_file = open(job_file_name, 'w')
    launch_command = ''
    lines = []
    for line in job_template_lines:
      m = re.search('<DOCE_LAUNCH>(.+?)<DOCE_LAUNCH>', line)
      if m:
        launch_command = m.group(1)
      script_file_name = inspect.stack()[-1].filename
      command = 'python3 '+script_file_name+' -c -s '+setting.identifier()
      line = line.replace('<DOCE_SETTING>', command)
      line = line.replace('<DOCE_NAME>', experiment.name)
      lines.append(line)

    launch_command += ' '+job_file_name
    job_file.writelines(lines)
    job_file.close()
    if experiment.job_launch:
      os.system(launch_command)
    else:
      print(launch_command)
      

  if args.job:
    if os.path.isdir('jobs'):
      shutil.rmtree('jobs')
    os.makedirs('jobs')
    experiment.job_template_file_name = args.job
    if args.compute:
      experiment.job_launch = True
    else:
      experiment.job_launch = False
    experiment.perform(
        experiment.selector,
        progress='',
        function=job_managment
    )
    if experiment.job_launch:
      shutil.rmtree('jobs')
    else:
      print('Up are the commands available.\nPlease inspect scripts files available in the jobs directory.\nIf correct please add -c or --compute to the command line for launching the jobs.')
    exit()
  if args.files:
    experiment.perform(
        experiment.selector,
        progress='',
        function=lambda s,
        e: print(s.identifier())
    )

  if args.remove:
    experiment.clean_data_sink(
        args.remove,
        experiment.selector,
        archive_path=experiment.path.archive,
        verbose=experiment.status.verbose
    )
  if args.keep:
    experiment.clean_data_sink(
        args.keep,
        experiment.selector,
        reverse=True,
        archive_path=experiment.path.archive,
        verbose=experiment.status.verbose
    )
  if args.archive:
    if experiment.path.archive:
      experiment.clean_data_sink(
          args.archive,
          experiment.selector,
          keep=True,
          archive_path=experiment.path.archive,
          verbose=experiment.status.verbose
      )
    else:
      print('Please set the path.archive path before issuing an archive command.')

  log_file_name = ''
  if args.host > -2:

    import argunparse

    unparser = argunparse.ArgumentUnparser()
    kwargs = copy.deepcopy(vars(args))
    kwargs['host'] = -3
    command = unparser.unparse(
        **kwargs).replace('\'', '\"').replace('\"', '\\\"')
    if args.verbose:
      command += '; bash '
    command = 'screen -dm bash -c \'python3 {experiment.name}.py {command}\''
    message = 'experiment launched on local host'
    if args.host > -1:
      if args.copy:
        sync_command = f'rsync -r {experiment.path.code}* {experiment.host[args.host]}:{experiment.path.code_raw}'
        print(f'Sycing code repository to host: {experiment.host[args.host]}')
        print(sync_command)
        os.system(sync_command)
        print('')
      command = 'ssh {experiment.host[args.host]} "cd {experiment.path.code_raw}; {command}"'
      message = 'Experiment launched.'
    print(f'Sending experiment to host: {experiment.host[args.host]}')
    print('')
    print(command)
    os.system(command)
    print('')
    print(message)
    sys.exit()
  print()
  if args.host == -3 or args.detached:
    log_file_name = '/tmp/doce_{experiment.name}_{experiment.status.run_id}.txt'
  if args.mail > -1:
    experiment.send_mail(
      f'{args.select} has started.',
      f'<div> Selector = {args.select}</div>'
      )
  if args.compute and func:
    experiment.perform(
      experiment.selector,
      func,
      nb_jobs=args.compute,
      log_file_name=log_file_name,
      progress=args.progress,
      mail_interval=float(args.mail)
      )

  select_display = []
  select_factor = ''
  display = True
  if args.display == '-1':
    display = False
  elif args.display is not None:
    if '[' in args.display:
      select_display = ast.literal_eval(args.display)
    elif ':' in args.display:
      display_split = args.display.split(':')
      select_display = [int(display_split[1])]
      select_factor = display_split[0]
    else:
      select_display = [int(args.display)]

  body = '<div> Selector = {args.select}</div>'
  if display:
    if display_func:
      display_func(
          experiment,
          experiment._plan.select(experiment.selector)
          )
    else:
      (data_frame, header, styler, significance, c_metric) = data_frame_display(
          experiment, args, select_display, select_factor)
      if data_frame is not None:
        print(header)
        # pd.set_option('precision', 2)
        print(data_frame)
      if args.export != 'none' and styler is not None:
        export_data_frame(experiment, args, data_frame, styler, header, significance, c_metric)
      if args.mail > -1:
        body += f'<div> {header} </div><br>{styler.render()}'

  if args.host == -3 or args.detached:
    log_file_name = f'/tmp/doce_{experiment.name}_{experiment.status.run_id}.txt'
    if os.path.exists(log_file_name):
      print(f'Some settings have failed. Log available at: {log_file_name}')
      with open(log_file_name, 'r') as file:
        log = file.read()
        if log:
          log_html = log.replace('\n', '<br>')
          body += f'<h2> Error log </h2>{log_html}'
  if args.mail > -1:
    experiment.send_mail(f'{args.select} is over.', body)


def data_frame_display(experiment, args, select_display, select_factor):

  import pandas as pd

  selector = experiment.selector
  if select_factor:
    factor_index = experiment._plan.factors().index(select_factor)

    selector = experiment._plan.expand_selector(selector, select_factor)

    masked_selector_factor = selector[factor_index]

    selector[factor_index] = [0]
    experiment._plan.select(selector).__set_settings__()
    settings = experiment._plan._settings

    for setting in settings:
      setting[factor_index] = masked_selector_factor

  (table, columns, header, nb_factor_columns, modification_time_stamp, significance) = experiment.metric.reduce(
    experiment._plan.select(selector),
    experiment.path,
    factor_display=experiment._display.factor_format_in_reduce,
    metric_display=experiment._display.metric_format_in_reduce,
    factor_display_length=experiment._display.factor_format_in_reduce_length,
    metric_display_length=experiment._display.metric_format_in_reduce_length,
    verbose=args.verbose
    )

  if len(table) == 0:
    return (None, '', None, None, None)
  if select_factor:
    modalities = getattr(experiment._plan, select_factor)[masked_selector_factor]
    header_short = header.replace(
        select_factor + ': ' + str(modalities[0]) + ' ', '')
    header = f'metric: {columns[nb_factor_columns+select_display[0]]} for factor {header_short} {select_factor}'

    columns = columns[:nb_factor_columns]
    for modality in modalities:
      columns.append(str(modality))

    significance = np.zeros((len(settings), len(modalities)))
    for row_index, _ in enumerate(table):
      table[row_index] = table[row_index][:nb_factor_columns]
    # print(settings)
    for setting_index, setting in enumerate(settings):
      (setting_descriptions, _, _, _, setting_modification_time_stamp, setting_p_values) = experiment.metric.reduce(
        experiment._plan.select(setting),
        experiment.path,
        factor_display=experiment._display.factor_format_in_reduce,
        metric_display=experiment._display.metric_format_in_reduce,
        factor_display_length=experiment._display.factor_format_in_reduce_length,
        metric_display_length=experiment._display.metric_format_in_reduce_length,
        verbose=args.verbose
        )
      modification_time_stamp += setting_modification_time_stamp # ???
      significance[setting_index, :] = setting_p_values[:, select_display[0]]
      for setting_description in setting_descriptions:
        table[setting_index].append(setting_description[1 + select_display[0]])

  if significance is not None:
    best = significance == -1
    significance = significance > experiment._display.pValue
    significance = significance.astype(float)
    significance[best] = -1
    if select_display and not select_factor:
      significance = significance[:, select_display]

  if experiment._display.pValue == 0:
    for table_row_index, in enumerate(table):
      table[table_row_index][-len(significance[table_row_index]):] = significance[table_row_index]

  if modification_time_stamp:
    print(f'Displayed data generated from {time.ctime(min(modification_time_stamp))} \
     to {time.ctime(max(modification_time_stamp))}')
  data_frame = pd.DataFrame(table, columns=columns)  # .fillna('-')

  if (select_display and
      not select_factor and
      len(columns) >= max(select_display) + nb_factor_columns
      ):
    columns = [columns[i] for i in [
        *range(nb_factor_columns)] + [s + nb_factor_columns for s in select_display]]
    data_frame = data_frame[columns]

  table_style = dict(selector="th", props=[
           ('text-align', 'center'), ('border-bottom', '.1rem solid')])

  # Construct a selector of which columns are numeric
  numeric_col_selector = data_frame.dtypes.apply(
      lambda d: issubclass(np.dtype(d).type, np.number))
  c_metric = []
  c_metric_precision = []
  bool_selector = []
  c_int = {}
  precision_format = {}
  for column_index, column in enumerate(columns):
    # if data_frame[column].dtypes == 'bool':
    #   bool_selector.append(column) 
    if np.sum(np.array(data_frame[column])==-99999)+np.sum(np.array(data_frame[column])==0)+np.sum(np.array(data_frame[column])==1) == np.array((data_frame[column])).size:
      bool_selector.append(column)
      data_frame[column] = data_frame[column].replace({-99999: 0})
      data_frame = data_frame.astype({column: 'bool'})
    if column_index >= nb_factor_columns:
      c_metric.append(column)
      if select_factor:
        precision = getattr(experiment.metric, experiment.metric.name()[select_display[0]])['precision']
      else:
        precision = getattr(experiment.metric, column.split(' ')[0])['precision']
      if '%' in column:
        c_metric_precision.append(precision-2)
        precision_format[metric_direction(column, experiment.metric, 'html')] = f'{{:0.{str(precision-2)}f}}'
      else:
        c_metric_precision.append(precision)
        precision_format[metric_direction(column, experiment.metric, 'html')] = f'{{:0.{str(precision)}f}}'

  d_precision = pd.Series(c_metric_precision, index=c_metric, dtype=np.intc)
  data_frame = data_frame.round(d_precision)
 
  for column in columns:
    if isinstance(data_frame[column][0], float):
      is_integer = True
      for data_column in data_frame[column]:
        if not data_column.is_integer():
          is_integer = False
      if is_integer:
        c_int[column] = 'int32'

  data_frame = data_frame.astype(c_int).applymap(remove_special)
  columns = data_frame.columns.to_series()
  data_frame.columns = data_frame.columns.to_series().apply(metric_direction, **{'metrics': experiment.metric, 'output_type':'html'})
  
  styler = data_frame.applymap(pretty_bool).style.set_properties(subset=data_frame.columns[numeric_col_selector],
                                   **{'width': '10em', 'text-align': 'right'})\
      .set_properties(subset=data_frame.columns[~numeric_col_selector],
                      **{'width': '10em', 'text-align': 'left'})\
      .set_properties(subset=bool_selector,
                      **{'width': '10em', 'text-align': 'center'})\
      .set_properties(subset=data_frame.columns[nb_factor_columns-1],
                      **{'border-right': '.1rem solid'})\
      .set_table_styles([table_style])\
      .format(precision_format).applymap(lambda x: 'color: white' if pd.isnull(x) else '')

  if not experiment._display.show_row_index:
    styler.hide_index()
  if experiment._display.bar:
    styler.bar(subset=data_frame.columns[nb_factor_columns:],
               align='mid', color=['#d65f5f', '#5fba7d'])
  if experiment._display.highlight:
    for c_metric_index, c_metric_name in enumerate(c_metric):
      c_metric[c_metric_index] = metric_direction(c_metric_name, experiment.metric, 'html')
    styler.apply(highlight_stat, subset=c_metric, axis=None,
                 **{'significance': significance})
    styler.apply(highlight_best, subset=c_metric, axis=None,
                 **{'significance': significance})

  data_frame.columns = columns.apply(metric_direction, **{'metrics': experiment.metric, 'output_type':'text'})
  return (data_frame.fillna('-').applymap(int_bool), header, styler, significance, c_metric)

def pretty_bool(val):
  if isinstance(val, bool):
    if val:
      return '&#11044'
    else:
      return ''
  return val

def escape_tex(val):
  if isinstance(val, str):
    val = val.replace('_', '\_').replace('%', '\%').replace('$', '\$').replace('{', '\{').replace('}', '\}')
  return val


def int_bool(val):
  if isinstance(val, bool):
    return int(val)
  return val

def remove_special(val):
  if val == -99999 or val == '-99999':
    return ''
  return val

def highlight_stat(data_frame, significance):
  import pandas as pd
  data_frame = pd.DataFrame('', index=data_frame.index, columns=data_frame.columns)
  if significance is not None:
    data_frame = data_frame.where(significance <= 0, 'color: blue')
  return data_frame

def tex(data_col, significance, metric_names):
  print(metric_names)
  print(data_col.name)
  if data_col.name in metric_names:
    metric_index = metric_names.index(data_col.name)
    for data_index, data in enumerate(data_col):
      if significance[data_index, metric_index] == -1:
        data_col[data_index] = f'\textbf{{{data_col[data_index]}}}'
      if significance[data_index, metric_index] == 1:
        data_col[data_index] = f'\textcolor{{blue}}{{{data_col[data_index]}}}'
    print(data_col.name)
  return data_col


def highlight_best(data_frame, significance):
  import pandas as pd
  data_frame = pd.DataFrame('', index=data_frame.index, columns=data_frame.columns)
  if significance is not None:
    data_frame = data_frame.where(significance > -1, 'font-weight: bold')
  return data_frame

def metric_direction(val, metrics, output_type):
  for metric in metrics.name():
    if len(val) >= len(getattr(metrics, metric)['name']) and getattr(metrics, metric)['name'] == val[:len(getattr(metrics, metric)['name'])]:
      if getattr(metrics, metric)['higher_the_better']:
        if output_type == 'tex':
          return val+' \\uparrow'
        elif output_type == 'text':
          return val+' +'  
        else:
          return val+' &#8593'   
      if getattr(metrics, metric)['lower_the_better']:
        if output_type == 'tex':
          return val+' \\downarrow'
        elif output_type == 'text':
          return val+' -'  
        else:
          return val+' &#8595'
  return val


def export_data_frame(experiment, args, data_frame, styler, header, significance, c_metric):
  if not os.path.exists(experiment.path.export):
    os.makedirs(experiment.path.export)
  if args.export == 'all':
    export_file_name = experiment.name
  else:
    args_split = args.export.split('.')
    # print(a)
    if args_split[0]:
      export_file_name = args_split[0]
    else:
      export_file_name = experiment.name
    if len(args_split) > 1:
      args.export = str(args_split[1])
    else:
      args.export = 'all'
      
  export_file_name = f'{experiment.path.export}/{export_file_name}'
  reload_header = '<script> window.onblur= function()\
    {window.onfocus= function () {location.reload(true)}}; </script>'
  with open(f'{export_file_name}.html', "w") as out_file:
    out_file.write(reload_header)
    out_file.write(f'<br><u>{header}</u><br><br>')
    out_file.write(styler.to_html())
  if 'csv' in args.export or args.export == 'all':
    data_frame.to_csv(path_or_buf=f'{export_file_name}.csv',
              index=experiment._display.show_row_index)
    print(f'csv export: {export_file_name}.csv')
  # if 'xls' in args.export or args.export == 'all':
  #   data_frame.to_excel(excel_writer=f'{export_file_name}.xls',
  #               index=experiment._display.show_row_index
  #               )
  #   print(f'excel export: {export_file_name}.xls')
  if 'tex' in args.export or args.export == 'all':
    data_frame.apply(tex, **{'significance': significance, 'metric_names': c_metric}).applymap(escape_tex)
    data_frame.columns = data_frame.columns.to_series().apply(metric_direction, **{'metrics': experiment.metric, 'output_type':'tex'}).apply(escape_tex)
    data_frame.to_latex(
                buf=f'{export_file_name}.tex',
                index=experiment._display.show_row_index,
                bold_rows=True,
                escape = False,
                caption=header.replace('_', '\_').replace('%', '\%').replace('$', '\$').replace('{', '\{').replace('}', '\}')
                )
    print(f'tex export: {export_file_name}.tex')
    print('please add \\usepackage{booktabs, textcolor} to the preamble of your main .tex file')

  if 'png' in args.export or args.export == 'all':
    print('Creating image using '+experiment._display.export_png)
    if experiment._display.export_png == 'wkhtmltoimage':
      if shutil.which('wkhtmltoimage') is not None:
        subprocess.call(
            f'wkhtmltoimage -f png --width 0 {export_file_name}.html {export_file_name}.png',
            shell=True
            )
        print(f'png export: {export_file_name}.png')
        # 
        # 
        # dfi.export(styler, f'{export_file_name}_3.png', dpi = 600, table_conversion='matplotlib')
      else:
        print('Generation of png is handled by converting the html output.')
        print('By default, doce tries to use wkhtmltoimage tool to do so.')
        print('This tool must be installed and reachable from you path.')
        print('Alternatively you can set experiment._display.export_png to \'chrome\' for an export with layout without the need of external depencencies aside from a reachable chrome. If you want ot rely only on python librairies, please use \'matlplotlib\' but most of the layout will be lost.')
    if experiment._display.export_png == 'chrome':
      dataframe_image.export(styler, f'{export_file_name}.png', dpi = 300)
    if experiment._display.export_png == 'matplotlib':
      dataframe_image.export(styler, f'{export_file_name}.png', dpi = 300, table_conversion='matplotlib')
  if 'pdf' in args.export or args.export == 'all':
    print('Creating pdf unsing '+experiment._display.export_pdf)
    if experiment._display.export_pdf == 'wkhtmltopdf':
      if shutil.which('wkhtmltopdf'):
        subprocess.call(
            f'wkhtmltopdf {export_file_name}.html {export_file_name}.pdf', shell=True)
      else:
        print('Generation of pdf is handled by converting the html output.')
        print('It uses the wkhtmltopdf tool to do so.')
        print('This tool must be installed and reachable from you path.')
        print('Alternatively you can set experiment._display.export_pdf to \'chrome\' for an export with layout without the need of external depencencies aside from a reachable chrome.')
    if experiment._display.export_pdf == 'chrome':
      dataframe_image.export(styler, f'{export_file_name}.pdf')

    print('Cropping {export_file_name}.pdf')
    if shutil.which('pdfcrop') is not None:
      subprocess.call(
          f'pdfcrop {export_file_name}.pdf {export_file_name}.pdf', shell=True)
      print('pdf export: {export_file_name}.pdf')
    else:
      print('''Crop of pdf is handled using the pdfcrop tool. \
        This tool must be installed and reachable from you path.''')

  if 'html' not in args.export and args.export != 'all':
    os.remove(f'{export_file_name}.html')
  else:
    print(f'html export: {export_file_name}.html')

if __name__ == '__main__':
  import doctest
  doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
