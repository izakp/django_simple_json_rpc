import json

from django.http import HttpResponse

class JsonResponse(HttpResponse):
	def __init__(self, content, mimetype='application/json', status=200, content_type=None):
		super(JsonResponse, self).__init__(
			content=json.dumps(content),
			mimetype=mimetype,
			status=status,	#what to put here?
			content_type=content_type,	#and here?
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

class JsonRpcInvalidRequestError(JsonRpcErrorResponse):
	def __init__(self):
		super(JsonRpcInvalidRequestError, self).__init__(
			error = {
				'code': -32600,
				'message': 'The JSON sent is not a valid Request object.',
			}
		)