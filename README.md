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

#### Note: to exempt requests from Django's CSRF protection middleware, you must explicitly import the controller into urls.py and pass it to csrf_exempt:

	from django.views.decorators.csrf import csrf_exempt
	from prefs.dash.views import json_rpc_controller

	url(r'^json-rpc/$', csrf_exempt(json_rpc_controller),


### Write your view functions and add them to the controller as named routes


	@json_rpc_controller.add_route()
	def get_user_id(request, user_id=None, auth_key=None):
		return {
			'user_id': user_id,
			'auth_key': auth_key,
		}

Routes should return dictionaries. If a route returns an object, foo it is wrapped in {"data": foo} before a JSON response is rendered.


## Logging

To enable logging, put this in your settings.py:

	DJANGO_JSON_RPC_DEBUG = True

Make sure your application has a default logger available.  Logging fails silently.

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
	def get_user_id(request, user_id, auth_key):
		return {
			'user_id': user_id,
			'auth_key': auth_key,
		}

If you pass a requirements dictionary, each parameter to be evaluated must at least contatin {'type': foo} where foo is the string representation of the JSON type required.

Requirements dictionaries can additionally contain the following keys specifying the following types of values:

	{
		'type': 'unicode',
		'length': int,
		'allowed_characters': re._pattern_type,
	}

	{
		'type': 'int',
		'min': int,
		'max': int,
	}

	{
		'type': 'bool',
	},

	{
		'type': 'null',
	},

	{
		'type': 'dict',
		'allowed_keys': list,
	},

	{
		'type': 'array',
		'length': int,
	},

