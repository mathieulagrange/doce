"""handle interaction with the doce module using the command line"""

import sys
import argparse
import ast
import importlib
import os
import copy
import subprocess
import shutil
import time
import re
import numpy as np
import doce

def main():
  """This method shall be called from the main script of the experiment
  to control the experiment using the command line.

  This method provides a front-end for running a doce experiment.
  It should be called from the main script of the experiment.
  The main script must define a **set** function that will be called before processing
  and a **step** function that will be processed for each setting.

  It may also define a **display** function that will used to monitor the results.
  This main script can define any functions that can be used
  within the **set**, **step**, and **display** functions.

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
      '-E',
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
      help=r'selection of settings',
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

  module = sys.argv[0][:-3]
  try:
    config = importlib.import_module(module)
  except:
    print(f'{sys.argv[0]} should implement a valid python module.')
    raise ValueError

  if hasattr(config, 'set'):
    experiment = config.set(args)
  else:
    experiment = doce.Experiment()

  if isinstance(args.user_data, dict):
    experiment.user_data = args.user_data

  if args.version:
    print("Experiment version " + experiment.version)
    exit(1)

  experiment.status.verbose = args.verbose
  experiment._resume = args.skip

  experiment.select(selector, show=args.plan)

  if args.information:
    print(experiment)

  if args.list:
    experiment.perform(
        experiment.selector,
        progress='',
        function=lambda s,
        e: print(s)
    )
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
          setting_encoding=experiment._setting_encoding,
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
  if args.compute and hasattr(config, 'step'):
    experiment.perform(
      experiment.selector,
      config.step,
      nb_jobs=args.compute,
      log_file_name=log_file_name,
      progress=args.progress,
      mail_interval=float(args.mail)
      )

  select_display = []
  select_factor = ''
  display_method = ''
  display = True
  if args.display == '-1':
    display = False
  elif args.display is not None:
    if '[' in args.display:
      select_display = ast.literal_eval(args.display)
    elif ':' in args.display:
      display_split = args.display.split(':')
      select_display = [int(display_split[0])]
      select_factor = display_split[1]
    else:
      select_display = [int(args.display)]

  body = '<div> Selector = {args.select}</div>'
  if display:
    if hasattr(config, display_method):
      getattr(config, display_method)(
          experiment, experiment._plan.select(experiment.selector))
    else:
      (data_frame, header, styler) = data_frame_display(
          experiment, args, config, select_display, select_factor)
      if data_frame is not None:
        print(header)
        # pd.set_option('precision', 2)
        print(data_frame)
      if args.export != 'none' and styler is not None:
        export_data_frame(experiment, args, data_frame, styler, header)
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


def data_frame_display(experiment, args, config, select_display, select_factor):

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
    experiment.path.output,
    factor_display=experiment._display.factor_format_in_reduce,
    metric_display=experiment._display.metric_format_in_reduce,
    factor_display_length=experiment._display.factor_format_in_reduce_length,
    metric_display_length=experiment._display.metric_format_in_reduce_length,
    verbose=args.verbose,
    reduction_directive_module=config
    )

  if len(table) == 0:
    return (None, '', None)
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
        experiment.path.output,
        factor_display=experiment._display.factor_format_in_reduce,
        metric_display=experiment._display.metric_format_in_reduce,
        factor_display_length=experiment._display.factor_format_in_reduce_length,
        metric_display_length=experiment._display.metric_format_in_reduce_length,
        verbose=args.verbose,
        reduction_directive_module=config
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
  c_percent = []
  c_no_percent = []
  c_minus = []
  c_no_minus = []
  c_metric = []
  c_int = {}
  precision_format = {}
  for column_index, column in enumerate(columns):
    if column_index >= nb_factor_columns:
      c_metric.append(column)
      if '%' in column:
        precision_format[column] = f'{{:0.{str(experiment._display.metric_precision-2)}f}}'
        c_percent.append(column)
      else:
        precision_format[column] = f'{{:0.{str(experiment._display.metric_precision)}f}}'
        c_no_percent.append(column)
      if column[-1] == '-':
        c_minus.append(column)
      else:
        c_no_minus.append(column)

  d_percent = pd.Series([experiment._display.metric_precision - 2]
                       * len(c_percent), index=c_percent, dtype=np.intc)
  d_no_percent = pd.Series([experiment._display.metric_precision]
                           * len(c_no_percent), index=c_no_percent, dtype=np.intc)
  data_frame = data_frame.round(d_percent).round(d_no_percent)

  for column in columns:
    if isinstance(data_frame[column][0], float):
      is_integer = True
      for data_column in data_frame[column]:
        if not data_column.is_integer():
          is_integer = False
      if is_integer:
        c_int[column] = 'int32'
  data_frame = data_frame.astype(c_int)

  styler = data_frame.style.set_properties(subset=data_frame.columns[numeric_col_selector],
                                   **{'width': '10em', 'text-align': 'right'})\
      .set_properties(subset=data_frame.columns[~numeric_col_selector],
                      **{'width': '10em', 'text-align': 'left'})\
      .set_properties(subset=data_frame.columns[nb_factor_columns],
                      **{'border-left': '.1rem solid'})\
      .set_table_styles([table_style])\
      .format(precision_format).applymap(lambda x: 'color: white' if pd.isnull(x) else '')
  if not experiment._display.show_row_index:
    styler.hide_index()
  if experiment._display.bar:
    styler.bar(subset=data_frame.columns[nb_factor_columns:],
               align='mid', color=['#d65f5f', '#5fba7d'])
  if experiment._display.highlight:
    styler.apply(highlight_stat, subset=c_metric, axis=None,
                 **{'significance': significance})
    styler.apply(highlight_best, subset=c_metric, axis=None,
                 **{'significance': significance})

  return (data_frame.fillna('-'), header, styler)

def highlight_stat(data_frame, significance):
  import pandas as pd
  data_frame = pd.DataFrame('', index=data_frame.index, columns=data_frame.columns)
  if significance is not None:
    data_frame = data_frame.where(significance <= 0, 'color: blue')
  return data_frame

def highlight_best(data_frame, significance):
  import pandas as pd
  data_frame = pd.DataFrame('', index=data_frame.index, columns=data_frame.columns)
  if significance is not None:
    data_frame = data_frame.where(significance > -1, 'font-weight: bold')
  return data_frame

def export_data_frame(experiment, args, data_frame, styler, header):
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
    out_file.write(styler.render())
  if 'csv' in args.export or args.export == 'all':
    data_frame.to_csv(path_or_buf=f'{export_file_name}.csv',
              index=experiment._display.show_row_index)
    print('csv export: {export_file_name}.csv')
  if 'xls' in args.export or args.export == 'all':
    data_frame.to_excel(excel_writer=f'{export_file_name}.xls',
                index=experiment._display.show_row_index
                )
    print('excel export: {export_file_name}.xls')

  if 'tex' in args.export or args.export == 'all':
    data_frame.to_latex(buf=f'{export_file_name}.tex',
                index=experiment._display.show_row_index,
                bold_rows=True,
                caption=header
                )
    print(f'tex export: {export_file_name}.tex')
    print('please add \\usepackage{booktabs} to the preamble of your main .tex file')

  if 'png' in args.export or args.export == 'all':
    print('Creating image...')
    if shutil.which('wkhtmltoimage') is not None:
      subprocess.call(
          f'wkhtmltoimage -f png --width 0 {export_file_name}.html {export_file_name}.png',
          shell=True
          )
      print(f'png export: {export_file_name}.png')
    else:
      print('''generation of png is handled by converting the html generated \
          from the result dataframe using the wkhtmltoimage tool. \
          This tool must be installed and reachable from you path.''')
  if 'pdf' in args.export or args.export == 'all':
    print('Creating pdf...')
    if shutil.which('wkhtmltopdf'):
      subprocess.call(
          f'wkhtmltopdf {export_file_name}.html {export_file_name}.pdf', shell=True)
    else:
      print('Generation of pdf is handled by converting the html generated from the result \
        dataframe using the wkhtmltoimage tool which must be installed \
        and reachable from you path.'
        )

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
