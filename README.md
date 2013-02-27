django-simple-json-rpc
======================

import re

from prefs.django_json_rpc import JsonRpcController

json_rpc_controller = JsonRpcController() #point your URL here url(r'^rpc/$', 'json_rpc_controller', name='json_rpc_controller'),

REQUIRED_PARAMETERS = {
	'user_id': {
		'type': 'unicode',
		'length': 2,
		'allowed_characters': re.compile("^[a-zA-Z0-9]+$"),
	},
	'auth_key': {
		'type': 'int',
		'min': 1,
		'max': 9,
	},
}

@json_rpc_controller.add_method(required_parameters=REQUIRED_PARAMETERS)
def get_user_id(request, user_id=None, auth_key=None):
	return {
		'user_id': user_id,
		'auth_key': auth_key,
	}

