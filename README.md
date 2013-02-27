django-simple-json-rpc
======================

Simple Django JSON-RPC.  Implements JSON-RPC 2.0 Specification:
http://www.jsonrpc.org/specification

Features:
- simple routing
- automatic error handling
- internal logging
- type checking and specifcation of required parameters

## Example Set Up

### Setting up an endpoint

Put this in your application's views.py:


	from prefs.django_json_rpc import JsonRpcController
	json_rpc_controller = JsonRpcController()


...and call the instantiated controller by pointing to it in urls.py:


	url(r'^json-rpc/$', 'views.json_rpc_controller'),


### Write your view functions and add them to the controller as named routes


	@json_rpc_controller.add_route(required_parameters=REQUIRED_PARAMETERS)
	def get_user_id(request, user_id=None, auth_key=None):
		return {
			'user_id': user_id,
			'auth_key': auth_key,
		}

Routes should return dictionaries. If a route returns an object, foo it is wrapped in {"data": foo} before a JSON response is rendered.

## Evaluating Named Parameters

Type checking and other requirements can be enforced on named parameters.  For example, to require the parameters user_id as an alphanumeric character and auth_key as an integer, create a requirements dict and pass it to add_route as required_parameters.

	import re

	REQUIRED_PARAMETERS = {
		'user_id': {
			'type': 'unicode',
			'allowed_characters': re.compile("^[a-zA-Z0-9]+$"),
		},
		'auth_key': {
			'type': 'int',
		},
	}

	@json_rpc_controller.add_route(required_parameters=REQUIRED_PARAMETERS)
	def get_user_id(request, user_id=None, auth_key=None):
		return {
			'user_id': user_id,
			'auth_key': auth_key,
		}


## Logging

To enable logging, put this in your settings.py:

	DJANGO_JSON_RPC_DEBUG = True

Make sure your application has a default logger available.  Logging fails silently.