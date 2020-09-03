# Configuration file for jupyter-nbconvert.


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
# Default:  ['text/html', 'application/pdf', 'text/latex', 'image/svg+xml', 'image/png', 'image/jpeg', 'text/markdown', 'text/plain']
c.NbConvertBase.display_data_priority = ['image/png', 'image/jpeg', 'text/markdown', 'text/plain', 'text/html', 'application/pdf', 'text/latex', 'image/svg+xml']