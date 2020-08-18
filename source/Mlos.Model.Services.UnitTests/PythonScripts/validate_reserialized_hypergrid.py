assert 'HypergridJsonDecoder' in locals(), "Make sure to execute the 'create_dimensions_and_spaces.py' script first.'"


success = False

try:
	redeserialized_simple_hypergrid = json.loads(cs_reserialized_hypergrid_json_string, cls=HypergridJsonDecoder)
	assert redeserialized_simple_hypergrid in simple_hypergrid, "redeserialized_simple_hypergrid is not in simple_hypergrid"
	assert simple_hypergrid in redeserialized_simple_hypergrid, "simple_hypergrid is not in redeserialized_simple_hypergrid"
	success = True
except Exception as e:
	success = False
	exception_message = str(e)