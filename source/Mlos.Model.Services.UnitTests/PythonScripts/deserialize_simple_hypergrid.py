assert 'HypergridJsonDecoder' in locals(), "Make sure to execute the 'create_dimensions_and_spaces.py' script first.'"

success = False
try:
    deserialized_simple_hypergrid = json.loads(cs_simple_hypergrid_json_string, cls=HypergridJsonDecoder)
    success = True
except Exception as e:
    success = False
    exception_message = str(e)