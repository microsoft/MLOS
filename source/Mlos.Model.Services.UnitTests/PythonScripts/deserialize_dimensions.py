assert 'continuous' in locals(), "Make sure to execute the 'create_dimensions_and_spaces.py' script first.'"

success = False
try:
    deserialized_continuous = json.loads(cs_continuous_dimension_json_string, cls=HypergridJsonDecoder)
    deserialized_discrete = json.loads(cs_discrete_dimension_json_string, cls=HypergridJsonDecoder)
    deserialized_ordinal = json.loads(cs_ordinal_dimension_json_string, cls=HypergridJsonDecoder)
    deserialized_categorical = json.loads(cs_categorical_dimension_json_string, cls=HypergridJsonDecoder)

    assert continuous == deserialized_continuous
    assert discrete == deserialized_discrete
    assert ordinal == deserialized_ordinal
    assert categorical == deserialized_categorical

    success = True
except Exception as e:
    success = False
    exception_message = str(e)