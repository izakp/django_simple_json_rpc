'''

Simple Django JSON-RPC.  Implements JSON-RPC 2.0 Specification:
http://www.jsonrpc.org/specification

Features:
- simple routing
- automatic error handling
- internal logging
- type checking and specifcation of required parameters

'''

import json
import inspect

from responses import *
from exceptions import *
from helpers import *

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


class JsonRpcController(object): # this object holds the following mappings function_name -> (function_callable, required_paramters_list, function_arg_length)

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


	def add_route(self, required_parameters=None): # this is a decorator, so we can easily expose any function

		def wrap(function): # put function into the map, along with its required parameters and number of arguments
			self.routes[function.__name__] = (function, required_parameters, len(inspect.getargspec(function).args))
		return wrap


	def check_named_parameters(self, parameters, required_parameters):

		for param_name, param_validators in required_parameters.iteritems():
			try:
				parameter = parameters[param_name]

			except KeyError:
				self.log('missing required parameter %s' % param_name)
				return False

			try:
				validate_parameter(parameter, param_validators)
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

				assert len(request_struct) > 0

				response = []
				for request_dict in request_struct:

					(result, request_id, error) = self.process_request(request, request_dict)

					if request_id or error:
						response.append(wrap_batch_response(result, request_id, error))

				return JsonResponse(content=response)

			# process single requests
			assert isinstance(request_struct, dict)

			(result, request_id, error) = self.process_request(request, request_struct)

			# TODO: notifications should return nothing but Django gets angry if we return no HTTP response.

			if not error:
				return JsonRpcResponse(result=result, request_id=request_id)
			else:
				return JsonRpcErrorResponse(error=result, request_id=request_id)

		except AssertionError:
			self.log('The JSON sent is not a valid Request object.')
			return JsonRpcInvalidRequestError()

	def process_request(self, request, request_dict):

		'''
		-- parameters
			- request (request object)
			- request_dict (request dictionary to process)

		-- returns
			tuple (result, request_id, error)
		'''

		error = False

		# Dispatch the request and catch exceptions
		try:
			result = self.dispatch_request(request, request_dict)
		except JsonRpcException, e:
			result = render_exception_to_result(e)
			error = True

		# Get the request ID if available
		try:
			request_id = request_dict.get('id', None)
		except:
			request_id = None

		return (result, request_id, error)


	def dispatch_request(self, request, request_dict):

		'''
		-- parameters
			- request (request object)
			- request_dict (request dictionary to process)

		-- returns
			result (type varies, returned from called function)
		'''

		if not isinstance(request_dict, dict):
			raise JsonRpcInvalidRequest()

		# Try to get the most important keys
		try:
			method = request_dict['method']
			parameters = request_dict['params']

			if not isinstance(method, unicode) or not isinstance(parameters, list) and not isinstance(parameters, dict): #chaining can be a nice thing :)
				raise JsonRpcInvalidRequest()

		except KeyError:
			self.log('The JSON sent is not a valid Request object')
			raise JsonRpcInvalidRequest()

		# Get the function from route map
		try:
			(function, required_parameters, function_arg_length) = self.routes[method]
		except KeyError:
			self.log('Method %s does not exist.' % method)
			raise JsonRpcMethodNotFound()

		if not isinstance(parameters, list) and not isinstance(parameters, dict):
			self.log('Invalid parameter struct calling method %s' % method)
			raise JsonRpcInvalidParameters()

		# For positional parameters we have to unpack the parameters into a list ...
		if isinstance(parameters, list):
			if len(parameters) != function_arg_length - 1: # ignore request as the first argument
				self.log('Invalid number of positional parameters for method %s' % method)
				raise JsonRpcInvalidParameters()

			try:
				result = function(request, *parameters) # Finally the magic happens and we call the wrapped function!
				return result
			except Exception, e:
				self.log('Internal Error calling %s : %s' % (method, e))
				# propogate custom exceptions
				if isinstance(e, JsonRpcCustomError):
					raise
				else:
					raise JsonRpcInternalError()

		# ... while for named parameters we need to validate then unpack into a dictionary
		if required_parameters:
			if not self.check_named_parameters(parameters, required_parameters):
				self.log('Invalid named parameters for method %s' % method)
				raise JsonRpcInvalidParameters()

		if len(parameters.items()) != function_arg_length - 1:
			self.log('Invalid number of named parameters for method %s' % method)
			raise JsonRpcInvalidParameters()

		try:
			result = function(request, **parameters)
			return result
		except Exception, e:
			self.log('Internal Error calling %s : %s' % (method, e))
			# propogate custom exceptions
			if isinstance(e, JsonRpcCustomError):
				raise
			else:
				raise JsonRpcInternalError()
