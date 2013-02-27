class JsonRpcException(Exception):
	code = 0
	message = None

class JsonRpcParseException(JsonRpcException):
	code = -32700
	message = 'Invalid JSON was received by the server.'

class JsonRpcInvalidRequest(JsonRpcException):
	code = -32600
	message = 'The JSON sent is not a valid Request object.'

class JsonRpcMethodNotFound(JsonRpcException):
	code = -32601
	message = 'The method does not exist / is not available.'

class JsonRpcInvalidParameters(JsonRpcException):
	code = -32602
	message = 'Invalid method parameter(s).'

class JsonRpcInternalError(JsonRpcException):
	code = -32603
	message = 'Internal JSON-RPC error.'

class JsonRpcCustomError(JsonRpcException):
	def __init__(self, code=None, message=None):
		self.code = code # -32000 to -32099
		self.message = message # Reserved for implementation-defined server-errors.
