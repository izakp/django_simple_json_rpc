'''

Simple Django JSON-RPC.  Implements JSON-RPC 2.0 Specification:
http://www.jsonrpc.org/specification

Features:
- simple routing
- automatic error handling
- internal logging
- type checking and specifcation of required parameters

'''

import datetime
import json
import re
import inspect

from django_json_rpc.responses import *
from django_json_rpc.exceptions import *

from django.http import HttpResponseNotAllowed

LOG = False

try:
	from django.conf import settings
	if settings.DJANGO_JSON_RPC_DEBUG:
		import logging
		logger = logging.getLogger(__name__)
		LOG = True
except:
	pass

VALIDATORS = {
	'unicode': {
		'type': unicode,
		'length': int,
		'allowed_characters': re._pattern_type,
	},
	'int': {
		'type': int,
		'min': int,
		'max': int,
	},
	'bool': {
		'type': bool,
	},
	'null': {
		'type': None,
	},
	'dict': {
		'type': dict,
		'allowed_keys': list,
	},
	'array': {
		'type': list,
		'length': int,
	},
}

class JsonRpcController(object):
	# this object holds the following mappings function_name -> (function_callable, required_paramters_list, function_arg_length)

	def __init__(self):
		self.routes = {}

	def log(self, message, level='info'):
		if LOG:
			if level == 'info':
				logger.info(message)
			if level == 'debug':
				logger.debug(message)
			if level == 'warning':
				logger.warning(message)
			if level == 'error':
				logger.error(message)
			if level == 'critical':
				logger.critical(message)

	# this is a decorator, so we can easily expose any function
	def add_route(self, required_parameters=None):
		# put function into the map, along with its required parameters and number of arguments
		def wrap(function):
			self.routes[function.__name__] = (function, required_parameters, len(inspect.getargspec(function).args))
		return wrap

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

	def validate_parameter(self, parameter, param_validators):

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


	def check_named_parameters(self, parameters, required_parameters):

		for param_name, param_validators in required_parameters.iteritems():
			try:
				parameter = parameters[param_name]

			except KeyError:
				self.log('missing required parameter %s' % param_name)
				return False

			try:
				self.validate_parameter(parameter, param_validators)
			except AssertionError, e:
				self.log('%s %s' % (e, param_name))
				return False

		return True

	def __call__(self, request, *args, **kwargs):

		if request.method != 'POST':
			return HttpResponseNotAllowed(['POST'])

		# decode raw JSON data
		try:
			request_struct = json.loads(request.raw_post_data)
		except ValueError:
			self.log('Invalid JSON was received by the server')
			return JsonRpcParseError()

		try:
			# process batch requests

			if isinstance(request_struct, list):
				response = []
				for request_dict in request_struct:

					assert isinstance(request_dict, dict)

					(result, request_id, error) = self.process_request(request, request_dict)

					response.append(self.wrap_batch_response(result, request_id, error))

				return JsonResponse(content=response)

			# process single requests

			assert isinstance(request_struct, dict)

			(result, request_id, error) = self.process_request(request, request_struct)

			if not error:
				return JsonRpcResponse(result=result, request_id=request_id)
			else:
				return JsonRpcErrorResponse(error=result, request_id=request_id)

		except AssertionError:
			self.log('Invalid JSON was received by the server')
			return JsonRpcParseError()

	def process_request(self, request, request_dict):

		'''
		we can be sure we have a valid structure now.  Let's proceed and catch exceptions here

		-- parameters
			- request (request object)
			- request_dict (request dictionary to process)

		-- returns
			tuple (result, request_id)
		'''

		# get the request ID
		request_id = request_dict.get('id', None)

		error = False

		#dispatch the request
		try:
			result = self.dispatch_request(request, request_dict)
		except JsonRpcException, e:
			result = self.render_exception_to_result(e)
			error = True

		return (result, request_id, error)


	def dispatch_request(self, request, request_dict):

		# try to get the most important keys
		try:
			method = request_dict['method']
			parameters = request_dict['parameters']
		except KeyError:
			self.log('The JSON sent is not a valid Request object')
			raise JsonRpcInvalidRequest()

		# get function from route map
		try:
			(function, required_parameters, function_arg_length) = self.routes[method]
		except KeyError:
			self.log('Method %s does not exist.' % method)
			raise JsonRpcMethodNotFound()

		if not isinstance(parameters, list) and not isinstance(parameters, dict):
			self.log('Invalid parameter struct calling method %s' % method)
			raise JsonRpcInvalidParameters()

		# For positional parameters
		if isinstance(parameters, list):
			# check that we have the right number of parameters before calling the function
			if len(parameters) != function_arg_length - 1: # ignore request as the first argument
				self.log('Invalid number of positional parameters for method %s' % method)
				raise JsonRpcInvalidParameters()

			# call route function with positional parameters
			try:
				result = function(request, *parameters)
				return self.render_result(result)
			except Exception, e:
				self.log('Internal Error calling %s : %s' % (method, e))
				raise JsonRpcInternalError()

		# For named parameters
		# if required named parameters are provided, verify them
		if required_parameters:
			if not self.check_named_parameters(parameters, required_parameters):
				self.log('Invalid named parameters for method %s' % method)
				raise JsonRpcInvalidParameters()

		# check that we have the right number of parameters before calling the function

		if len(parameters.items()) != function_arg_length - 1: # ignore request as the first argument
			self.log('Invalid number of named parameters for method %s' % method)
			raise JsonRpcInvalidParameters()

		# call route function with named parameters
		try:
			result = function(request, **parameters)
			return self.render_result(result)
		except Exception, e:
			self.log('Internal Error calling %s : %s' % (method, e))
			raise JsonRpcInternalError()
