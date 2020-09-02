# Configuration file for jupyter-nbconvert.

#------------------------------------------------------------------------------
# Application(SingletonConfigurable) configuration
#------------------------------------------------------------------------------

## This is an application.

## The date format used by logging formatters for %(asctime)s
#c.Application.log_datefmt = '%Y-%m-%d %H:%M:%S'

## The Logging format template
#c.Application.log_format = '[%(name)s]%(highlevel)s %(message)s'

## Set the log level by value or name.
#c.Application.log_level = 30

#------------------------------------------------------------------------------
# JupyterApp(Application) configuration
#------------------------------------------------------------------------------

## Base class for Jupyter applications

## Answer yes to any prompts.
#c.JupyterApp.answer_yes = False

## Full path of a config file.
#c.JupyterApp.config_file = ''

## Specify a config file to load.
#c.JupyterApp.config_file_name = ''

## Generate default config file.
#c.JupyterApp.generate_config = False

#------------------------------------------------------------------------------
# NbConvertApp(JupyterApp) configuration
#------------------------------------------------------------------------------

## This application is used to convert notebook files (*.ipynb) to various other
#  formats.
#
#  WARNING: THE COMMANDLINE INTERFACE MAY CHANGE IN FUTURE RELEASES.

## The export format to be used, either one of the built-in formats ['asciidoc',
#  'custom', 'html', 'latex', 'markdown', 'notebook', 'pdf', 'python', 'rst',
#  'script', 'slides'] or a dotted object name that represents the import path
#  for an `Exporter` class
#c.NbConvertApp.export_format = 'html'

## read a single notebook from stdin.
#c.NbConvertApp.from_stdin = False

## URL base for ipywidgets package
#c.NbConvertApp.ipywidgets_base_url = 'https://unpkg.com/'

## List of notebooks to convert. Wildcards are supported. Filenames passed
#  positionally will be added to the list.
#c.NbConvertApp.notebooks = []

## overwrite base name use for output files. can only be used when converting one
#  notebook at a time.
#c.NbConvertApp.output_base = ''

## Directory to copy extra files (figures) to. '{notebook_name}' in the string
#  will be converted to notebook basename.
#c.NbConvertApp.output_files_dir = '{notebook_name}_files'

## PostProcessor class used to write the results of the conversion
#c.NbConvertApp.postprocessor_class = ''

## Whether to apply a suffix prior to the extension (only relevant when
#  converting to notebook format). The suffix is determined by the exporter, and
#  is usually '.nbconvert'.
#c.NbConvertApp.use_output_suffix = True

## Writer class used to write the  results of the conversion
#c.NbConvertApp.writer_class = 'FilesWriter'

#------------------------------------------------------------------------------
# NbConvertBase(LoggingConfigurable) configuration
#------------------------------------------------------------------------------

## Global configurable class for shared config
#
#  Useful for display data priority that might be used by many transformers

## Deprecated default highlight language as of 5.0, please use language_info
#  metadata instead
#c.NbConvertBase.default_language = 'ipython'

## An ordered list of preferred output type, the first encountered will usually
#  be used when converting discarding the others.
c.NbConvertBase.display_data_priority = ['image/png', 'image/jpeg', 'text/markdown', 'text/plain', 'text/html', 'application/pdf', 'text/latex', 'image/svg+xml']

#------------------------------------------------------------------------------
# Exporter(LoggingConfigurable) configuration
#------------------------------------------------------------------------------

## Class containing methods that sequentially run a list of preprocessors on a
#  NotebookNode object and then return the modified NotebookNode object and
#  accompanying resources dict.

## List of preprocessors available by default, by name, namespace, instance, or
#  type.
#c.Exporter.default_preprocessors = ['nbconvert.preprocessors.TagRemovePreprocessor', 'nbconvert.preprocessors.RegexRemovePreprocessor', 'nbconvert.preprocessors.ClearOutputPreprocessor', 'nbconvert.preprocessors.ExecutePreprocessor', 'nbconvert.preprocessors.coalesce_streams', 'nbconvert.preprocessors.SVG2PDFPreprocessor', 'nbconvert.preprocessors.CSSHTMLHeaderPreprocessor', 'nbconvert.preprocessors.LatexPreprocessor', 'nbconvert.preprocessors.HighlightMagicsPreprocessor', 'nbconvert.preprocessors.ExtractOutputPreprocessor', 'nbconvert.preprocessors.ClearMetadataPreprocessor']

## Extension of the file that should be written to disk
#c.Exporter.file_extension = '.txt'

## List of preprocessors, by name or namespace, to enable.
#c.Exporter.preprocessors = []

#------------------------------------------------------------------------------
# TemplateExporter(Exporter) configuration
#------------------------------------------------------------------------------

## Exports notebooks into other file formats.  Uses Jinja 2 templating engine to
#  output new formats.  Inherit from this class if you are creating a new
#  template type along with new filters/preprocessors.  If the filters/
#  preprocessors provided by default suffice, there is no need to inherit from
#  this class.  Instead, override the template_file and file_extension traits via
#  a config file.
#
#  Filters available by default for templates:
#
#  - add_anchor - add_prompts - ansi2html - ansi2latex - ascii_only -
#  citation2latex - comment_lines - convert_pandoc - escape_latex -
#  filter_data_type - get_lines - get_metadata - highlight2html - highlight2latex
#  - html2text - indent - ipython2python - json_dumps - markdown2asciidoc -
#  markdown2html - markdown2latex - markdown2rst - path2url - posix_path -
#  prevent_list_blocks - strip_ansi - strip_dollars - strip_files_prefix -
#  strip_trailing_newline - wrap_text

## This allows you to exclude code cells from all templates if set to True.
#c.TemplateExporter.exclude_code_cell = False

## This allows you to exclude code cell inputs from all templates if set to True.
#c.TemplateExporter.exclude_input = False

## This allows you to exclude input prompts from all templates if set to True.
#c.TemplateExporter.exclude_input_prompt = False

## This allows you to exclude markdown cells from all templates if set to True.
#c.TemplateExporter.exclude_markdown = False

## This allows you to exclude code cell outputs from all templates if set to
#  True.
#c.TemplateExporter.exclude_output = False

## This allows you to exclude output prompts from all templates if set to True.
#c.TemplateExporter.exclude_output_prompt = False

## This allows you to exclude raw cells from all templates if set to True.
#c.TemplateExporter.exclude_raw = False

## This allows you to exclude unknown cells from all templates if set to True.
#c.TemplateExporter.exclude_unknown = False

## Dictionary of filters, by name and namespace, to add to the Jinja environment.
#c.TemplateExporter.filters = {}

## formats of raw cells to be included in this Exporter's output.
#c.TemplateExporter.raw_mimetypes = []

##
#c.TemplateExporter.template_extension = '.tpl'

## Name of the template file to use
#c.TemplateExporter.template_file = ''

##
#c.TemplateExporter.template_path = ['.']

#------------------------------------------------------------------------------
# ASCIIDocExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

## Exports to an ASCIIDoc document (.asciidoc)

#------------------------------------------------------------------------------
# HTMLExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

## Exports a basic HTML document.  This exporter assists with the export of HTML.
#  Inherit from it if you are writing your own HTML template and need custom
#  preprocessors/filters.  If you don't need custom preprocessors/ filters, just
#  change the 'template_file' config option.

## The text used as the text for anchor links.
#c.HTMLExporter.anchor_link_text = '¶'

#------------------------------------------------------------------------------
# LatexExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

## Exports to a Latex template.  Inherit from this class if your template is
#  LaTeX based and you need custom transformers/filters. If you don't need custom
#  transformers/filters, just change the  'template_file' config option.  Place
#  your template in the special "/latex"  subfolder of the "../templates" folder.

##
#c.LatexExporter.template_extension = '.tplx'

#------------------------------------------------------------------------------
# MarkdownExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

## Exports to a markdown document (.md)

#------------------------------------------------------------------------------
# NotebookExporter(Exporter) configuration
#------------------------------------------------------------------------------

## Exports to an IPython notebook.
#
#  This is useful when you want to use nbconvert's preprocessors to operate on a
#  notebook (e.g. to execute it) and then write it back to a notebook file.

## The nbformat version to write. Use this to downgrade notebooks.
#c.NotebookExporter.nbformat_version = 4

#------------------------------------------------------------------------------
# PDFExporter(LatexExporter) configuration
#------------------------------------------------------------------------------

## Writer designed to write to PDF files.
#
#  This inherits from :class:`LatexExporter`. It creates a LaTeX file in a
#  temporary directory using the template machinery, and then runs LaTeX to
#  create a pdf.

## Shell command used to run bibtex.
#c.PDFExporter.bib_command = ['bibtex', '{filename}']

## Shell command used to compile latex.
#c.PDFExporter.latex_command = ['xelatex', '{filename}', '-quiet']

## How many times latex will be called.
#c.PDFExporter.latex_count = 3

## Whether to display the output of latex commands.
#c.PDFExporter.verbose = False

#------------------------------------------------------------------------------
# PythonExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

## Exports a Python code file.

#------------------------------------------------------------------------------
# RSTExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

## Exports reStructuredText documents.

#------------------------------------------------------------------------------
# ScriptExporter(TemplateExporter) configuration
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# SlidesExporter(HTMLExporter) configuration
#------------------------------------------------------------------------------

## Exports HTML slides with reveal.js

## URL to load font awesome from.
#
#  Defaults to loading from cdnjs.
#c.SlidesExporter.font_awesome_url = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.css'

## URL to load jQuery from.
#
#  Defaults to loading from cdnjs.
#c.SlidesExporter.jquery_url = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js'

## URL to load require.js from.
#
#  Defaults to loading from cdnjs.
#c.SlidesExporter.require_js_url = 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js'

## If True, enable scrolling within each slide
#c.SlidesExporter.reveal_scroll = False

## Name of the reveal.js theme to use.
#
#  We look for a file with this name under
#  ``reveal_url_prefix``/css/theme/``reveal_theme``.css.
#
#  https://github.com/hakimel/reveal.js/tree/master/css/theme has list of themes
#  that ship by default with reveal.js.
#c.SlidesExporter.reveal_theme = 'simple'

## Name of the reveal.js transition to use.
#
#  The list of transitions that ships by default with reveal.js are: none, fade,
#  slide, convex, concave and zoom.
#c.SlidesExporter.reveal_transition = 'slide'

## The URL prefix for reveal.js (version 3.x). This defaults to the reveal CDN,
#  but can be any url pointing to a copy  of reveal.js.
#
#  For speaker notes to work, this must be a relative path to a local  copy of
#  reveal.js: e.g., "reveal.js".
#
#  If a relative path is given, it must be a subdirectory of the current
#  directory (from which the server is run).
#
#  See the usage documentation
#  (https://nbconvert.readthedocs.io/en/latest/usage.html#reveal-js-html-
#  slideshow) for more details.
#c.SlidesExporter.reveal_url_prefix = ''

#------------------------------------------------------------------------------
# Preprocessor(NbConvertBase) configuration
#------------------------------------------------------------------------------

## A configurable preprocessor
#
#  Inherit from this class if you wish to have configurability for your
#  preprocessor.
#
#  Any configurable traitlets this class exposed will be configurable in profiles
#  using c.SubClassName.attribute = value
#
#  you can overwrite :meth:`preprocess_cell` to apply a transformation
#  independently on each cell or :meth:`preprocess` if you prefer your own logic.
#  See corresponding docstring for information.
#
#  Disabled by default and can be enabled via the config by
#      'c.YourPreprocessorName.enabled = True'

##
#c.Preprocessor.enabled = False

#------------------------------------------------------------------------------
# CSSHTMLHeaderPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Preprocessor used to pre-process notebook for HTML output.  Adds IPython
#  notebook front-end CSS and Pygments CSS to HTML output.

## CSS highlight class identifier
#c.CSSHTMLHeaderPreprocessor.highlight_class = '.highlight'

## Name of the pygments style to use
#c.CSSHTMLHeaderPreprocessor.style = 'default'

#------------------------------------------------------------------------------
# ClearMetadataPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Removes all the metadata from all code cells in a notebook.

#------------------------------------------------------------------------------
# ClearOutputPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Removes the output from all code cells in a notebook.

##
#c.ClearOutputPreprocessor.remove_metadata_fields = {'scrolled', 'collapsed'}

#------------------------------------------------------------------------------
# ConvertFiguresPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Converts all of the outputs in a notebook from one format to another.

## Format the converter accepts
#c.ConvertFiguresPreprocessor.from_format = ''

## Format the converter writes
#c.ConvertFiguresPreprocessor.to_format = ''

#------------------------------------------------------------------------------
# ExecutePreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Executes all the cells in a notebook

## If `False` (default), when a cell raises an error the execution is stopped and
#  a `CellExecutionError` is raised. If `True`, execution errors are ignored and
#  the execution is continued until the end of the notebook. Output from
#  exceptions is included in the cell output in both cases.
#c.ExecutePreprocessor.allow_errors = False

## If False (default), errors from executing the notebook can be allowed with a
#  `raises-exception` tag on a single cell, or the `allow_errors` configurable
#  option for all cells. An allowed error will be recorded in notebook output,
#  and execution will continue. If an error occurs when it is not explicitly
#  allowed, a `CellExecutionError` will be raised. If True, `CellExecutionError`
#  will be raised for any error that occurs while executing the notebook. This
#  overrides both the `allow_errors` option and the `raises-exception` cell tag.
#c.ExecutePreprocessor.force_raise_errors = False

## If execution of a cell times out, interrupt the kernel and continue executing
#  other cells rather than throwing an error and stopping.
#c.ExecutePreprocessor.interrupt_on_timeout = False

## The time to wait (in seconds) for IOPub output. This generally doesn't need to
#  be set, but on some slow networks (such as CI systems) the default timeout
#  might not be long enough to get all messages.
#c.ExecutePreprocessor.iopub_timeout = 4

## Path to file to use for SQLite history database for an IPython kernel.
#
#  The specific value `:memory:` (including the colon at both end but not the
#  back ticks), avoids creating a history file. Otherwise, IPython will create a
#  history file for each kernel.
#
#  When running kernels simultaneously (e.g. via multiprocessing) saving history
#  a single SQLite file can result in database errors, so using `:memory:` is
#  recommended in non-interactive contexts.
#c.ExecutePreprocessor.ipython_hist_file = ':memory:'

## The kernel manager class to use.
#c.ExecutePreprocessor.kernel_manager_class = 'builtins.object'

## Name of kernel to use to execute the cells. If not set, use the kernel_spec
#  embedded in the notebook.
#c.ExecutePreprocessor.kernel_name = ''

## If `False` (default), then the kernel will continue waiting for iopub messages
#  until it receives a kernel idle message, or until a timeout occurs, at which
#  point the currently executing cell will be skipped. If `True`, then an error
#  will be raised after the first timeout. This option generally does not need to
#  be used, but may be useful in contexts where there is the possibility of
#  executing notebooks with memory-consuming infinite loops.
#c.ExecutePreprocessor.raise_on_iopub_timeout = False

## If `graceful` (default), then the kernel is given time to clean up after
#  executing all cells, e.g., to execute its `atexit` hooks. If `immediate`, then
#  the kernel is signaled to immediately terminate.
#c.ExecutePreprocessor.shutdown_kernel = 'graceful'

## The time to wait (in seconds) for the kernel to start. If kernel startup takes
#  longer, a RuntimeError is raised.
#c.ExecutePreprocessor.startup_timeout = 60

## If `True` (default), then the state of the Jupyter widgets created at the
#  kernel will be stored in the metadata of the notebook.
#c.ExecutePreprocessor.store_widget_state = True

## The time to wait (in seconds) for output from executions. If a cell execution
#  takes longer, an exception (TimeoutError on python 3+, RuntimeError on python
#  2) is raised.
#
#  `None` or `-1` will disable the timeout. If `timeout_func` is set, it
#  overrides `timeout`.
#c.ExecutePreprocessor.timeout = 30

## A callable which, when given the cell source as input, returns the time to
#  wait (in seconds) for output from cell executions. If a cell execution takes
#  longer, an exception (TimeoutError on python 3+, RuntimeError on python 2) is
#  raised.
#
#  Returning `None` or `-1` will disable the timeout for the cell. Not setting
#  `timeout_func` will cause the preprocessor to default to using the `timeout`
#  trait for all cells. The `timeout_func` trait overrides `timeout` if it is not
#  `None`.
#c.ExecutePreprocessor.timeout_func = None

#------------------------------------------------------------------------------
# ExtractOutputPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Extracts all of the outputs from the notebook file.  The extracted outputs are
#  returned in the 'resources' dictionary.

##
#c.ExtractOutputPreprocessor.extract_output_types = {'image/png', 'image/jpeg', 'image/svg+xml', 'application/pdf'}

##
#c.ExtractOutputPreprocessor.output_filename_template = '{unique_key}_{cell_index}_{index}{extension}'

#------------------------------------------------------------------------------
# HighlightMagicsPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Detects and tags code cells that use a different languages than Python.

## Syntax highlighting for magic's extension languages. Each item associates a
#  language magic extension such as %%R, with a pygments lexer such as r.
#c.HighlightMagicsPreprocessor.languages = {}

#------------------------------------------------------------------------------
# LatexPreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Preprocessor for latex destined documents.
#
#  Mainly populates the `latex` key in the resources dict, adding definitions for
#  pygments highlight styles.

## Name of the pygments style to use
#c.LatexPreprocessor.style = 'default'

#------------------------------------------------------------------------------
# RegexRemovePreprocessor(Preprocessor) configuration
#------------------------------------------------------------------------------

## Removes cells from a notebook that match one or more regular expression.
#
#  For each cell, the preprocessor checks whether its contents match the regular
#  expressions in the `patterns` traitlet which is a list of unicode strings. If
#  the contents match any of the patterns, the cell is removed from the notebook.
#
#  To modify the list of matched patterns, modify the patterns traitlet. For
#  example, execute the following command to convert a notebook to html and
#  remove cells containing only whitespace::
#
#    jupyter nbconvert --RegexRemovePreprocessor.patterns="['\s*\Z']"
#  mynotebook.ipynb
#
#  The command line argument sets the list of patterns to ``'\s*\Z'`` which
#  matches an arbitrary number of whitespace characters followed by the end of
#  the string.
#
#  See https://regex101.com/ for an interactive guide to regular expressions
#  (make sure to select the python flavor). See
#  https://docs.python.org/library/re.html for the official regular expression
#  documentation in python.

##
#c.RegexRemovePreprocessor.patterns = []

#------------------------------------------------------------------------------
# SVG2PDFPreprocessor(ConvertFiguresPreprocessor) configuration
#------------------------------------------------------------------------------

## Converts all of the outputs in a notebook from SVG to PDF.

## The command to use for converting SVG to PDF
#
#  This string is a template, which will be formatted with the keys to_filename
#  and from_filename.
#
#  The conversion call must read the SVG from {from_filename}, and write a PDF to
#  {to_filename}.
#c.SVG2PDFPreprocessor.command = ''

## The path to Inkscape, if necessary
#c.SVG2PDFPreprocessor.inkscape = ''

#------------------------------------------------------------------------------
# TagRemovePreprocessor(ClearOutputPreprocessor) configuration
#------------------------------------------------------------------------------

## Removes inputs, outputs, or cells from a notebook that have tags that
#  designate they are to be removed prior to exporting the notebook.
#
#  Traitlets
#  ---------
#  remove_cell_tags
#      removes cells tagged with these values
#
#  remove_all_outputs_tags
#      removes entire output areas on cells
#      tagged with these values
#
#  remove_single_output_tags
#      removes individual output objects on
#      outputs tagged with these values
#
#  remove_input_tags
#      removes inputs tagged with these values

## Tags indicating cells for which the outputs are to be removed,matches tags in
#  `cell.metadata.tags`.
#c.TagRemovePreprocessor.remove_all_outputs_tags = set()

## Tags indicating which cells are to be removed,matches tags in
#  `cell.metadata.tags`.
#c.TagRemovePreprocessor.remove_cell_tags = set()

## Tags indicating cells for which input is to be removed,matches tags in
#  `cell.metadata.tags`.
#c.TagRemovePreprocessor.remove_input_tags = set()

## Tags indicating which individual outputs are to be removed,matches output *i*
#  tags in `cell.outputs[i].metadata.tags`.
#c.TagRemovePreprocessor.remove_single_output_tags = set()

#------------------------------------------------------------------------------
# WriterBase(NbConvertBase) configuration
#------------------------------------------------------------------------------

## Consumes output from nbconvert export...() methods and writes to a useful
#  location.

## List of the files that the notebook references.  Files will be  included with
#  written output.
#c.WriterBase.files = []

#------------------------------------------------------------------------------
# DebugWriter(WriterBase) configuration
#------------------------------------------------------------------------------

## Consumes output from nbconvert export...() methods and writes useful debugging
#  information to the stdout.  The information includes a list of resources that
#  were extracted from the notebook(s) during export.

#------------------------------------------------------------------------------
# FilesWriter(WriterBase) configuration
#------------------------------------------------------------------------------

## Consumes nbconvert output and produces files.

## Directory to write output(s) to. Defaults to output to the directory of each
#  notebook. To recover previous default behaviour (outputting to the current
#  working directory) use . as the flag value.
#c.FilesWriter.build_directory = ''

## When copying files that the notebook depends on, copy them in relation to this
#  path, such that the destination filename will be os.path.relpath(filename,
#  relpath). If FilesWriter is operating on a notebook that already exists
#  elsewhere on disk, then the default will be the directory containing that
#  notebook.
#c.FilesWriter.relpath = ''

#------------------------------------------------------------------------------
# StdoutWriter(WriterBase) configuration
#------------------------------------------------------------------------------

## Consumes output from nbconvert export...() methods and writes to the  stdout
#  stream.

#------------------------------------------------------------------------------
# PostProcessorBase(NbConvertBase) configuration
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# ServePostProcessor(PostProcessorBase) configuration
#------------------------------------------------------------------------------

## Post processor designed to serve files
#
#  Proxies reveal.js requests to a CDN if no local reveal.js is present

## Specify what browser should be used to open slides. See
#  https://docs.python.org/3/library/webbrowser.html#webbrowser.register to see
#  how keys are mapped to browser executables. If  not specified, the default
#  browser will be determined  by the `webbrowser`  standard library module,
#  which allows setting of the BROWSER  environment variable to override it.
#c.ServePostProcessor.browser = ''

## The IP address to listen on.
#c.ServePostProcessor.ip = '127.0.0.1'

## Should the browser be opened automatically?
#c.ServePostProcessor.open_in_browser = True

## port for the server to listen on.
#c.ServePostProcessor.port = 8000

## URL for reveal.js CDN.
#c.ServePostProcessor.reveal_cdn = 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/3.5.0'

## URL prefix for reveal.js
#c.ServePostProcessor.reveal_prefix = 'reveal.js'
