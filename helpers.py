def render_result(self, data):
	if not isinstance(data, dict):
		result = {}
		result['data'] = result
	else:
		result = data
	return result

def render_exception_to_result(self, e):
	result = {
		'code': e.code,
		'message': e.message,
	}
	return result

def wrap_batch_response(self, result, request_id, error):
	content = {
		'jsonrpc': "2.0",
		'id': request_id,
	}

	if not error:
		content['result'] = result
	else:
		content['error'] = result

	return content

def validate_parameter(parameter, param_validators):

	assert 'type' in param_validators, 'Validators must specify a type'

	param_type = param_validators['type']

	assert param_type in VALIDATORS, 'Unknown parameter type'

	assert isinstance(parameter, VALIDATORS[param_type]['type']), 'Invalid parameter type'

	if param_type == 'unicode':

		if 'length' in param_validators:
			assert isinstance(param_validators['length'], VALIDATORS[param_type]['length']), 'Invalid validator'
			assert len(parameter) is param_validators['length'], 'Received invalid parameter'

		if 'allowed_characters' in param_validators:
			assert isinstance(param_validators['allowed_characters'], VALIDATORS[param_type]['allowed_characters']), 'Invalid validator'
			assert param_validators['allowed_characters'].match(parameter) is not None, 'Received invalid parameter'

	if param_type == 'int':

		if 'min' in param_validators:
			assert isinstance(param_validators['min'], VALIDATORS[param_type]['min']), 'Invalid validator'
			assert parameter > param_validators['min'], 'Received invalid parameter'

		if 'max' in param_validators:
			assert isinstance(param_validators['max'], VALIDATORS[param_type]['max']), 'Invalid validator'
			assert parameter < param_validators['max'], 'Received invalid parameter'

	if param_type == 'array':

		if 'length' in param_validators:
			assert isinstance(param_validators['length'], VALIDATORS[param_type]['length']), 'Invalid validator'
			assert len(parameter) is param_validators['length'], 'Received invalid parameter'

	if param_type == 'dict':
		if 'allowed_keys' in param_validators:
			assert isinstance(param_validators['allowed_keys'], VALIDATORS[param_type]['allowed_keys']), 'Invalid validator'
			for key, value in parameter.iteritems():
				assert key in param_validators['allowed_keys'], 'Received invalid parameter'
