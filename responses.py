import json

from django.http import HttpResponse

class JsonResponse(HttpResponse):
	def __init__(self, content, mimetype='application/json', status=None, content_type=None):
		super(JsonResponse, self).__init__(
			content=json.dumps(content),
			mimetype=mimetype,
			status=status,
			content_type=content_type,
        )

class JsonRpcResponse(JsonResponse):
	def __init__(self, result, request_id=None):
		super(JsonRpcResponse, self).__init__(
			content = {
				'jsonrpc': "2.0",
				'result': result,
				'id': request_id,
			}
		)

class JsonRpcErrorResponse(JsonResponse):
	def __init__(self, error, request_id=None):
		super(JsonRpcErrorResponse, self).__init__(
			content = {
				'jsonrpc': "2.0",
				'error': error,
				'id': request_id,
			}
		)

class JsonRpcParseError(JsonRpcErrorResponse):
	def __init__(self):
		super(JsonRpcParseError, self).__init__(
			error = {
				'code': -32700,
				'message': 'Invalid JSON was received by the server.',
			}
		)

class JsonRpcInvalidRequest(JsonRpcErrorResponse):
	def __init__(self, request_id):
		super(JsonRpcInvalidRequest, self).__init__(
			error = {
				'code': -32600,
				'message': 'The JSON sent is not a valid Request object.',
			},
			request_id = request_id
		)

class JsonRpcMethodNotFound(JsonRpcErrorResponse):
	def __init__(self, request_id):
		super(JsonRpcMethodNotFound, self).__init__(
			error = {
				'code': -32601,
				'message': 'The method does not exist / is not available.',
			},
			request_id = request_id
		)

class JsonRpcInvalidParameters(JsonRpcErrorResponse):
	def __init__(self, request_id):
		super(JsonRpcInvalidParameters, self).__init__(
			error = {
				'code': -32602,
				'message': 'Invalid method parameter(s).',
			},
			request_id = request_id
		)

class JsonRpcInternalError(JsonRpcErrorResponse):
	def __init__(self, request_id):
		super(JsonRpcInternalError, self).__init__(
			error = {
				'code': -32603,
				'message': 'Internal JSON-RPC error.',
			},
			request_id = request_id
		)

class JsonRpcCustomError(JsonRpcErrorResponse):
	def __init__(self, code = None, message = None, request_id=None):
		super(JsonRpcCustomError, self).__init__(
			error = {
				'code': code, # -32000 to -32099
				'message': message, # Reserved for implementation-defined server-errors.
			},
			request_id = request_id
		)
