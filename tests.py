import unittest
import json

from django_simple_json_rpc import JsonRpcController

#http://djangosnippets.org/snippets/963/
from django.test import Client
from django.test.client import FakePayload
from django.core.handlers.wsgi import WSGIRequest

class RequestFactory(Client):
	def request(self, payload=None, **request):
		"""
		Similar to parent class, but returns the request object as soon as it
		has created it.
		"""
		environ = {
			'HTTP_COOKIE': self.cookies,
			'PATH_INFO': '/',
			'QUERY_STRING': '',
			'REQUEST_METHOD': 'POST',
			'SCRIPT_NAME': '',
			'SERVER_NAME': 'testserver',
			'SERVER_PORT': 80,
			'SERVER_PROTOCOL': 'HTTP/1.1',
		}
		self.defaults['wsgi.input'] = FakePayload(payload)
		environ.update(self.defaults)
		environ.update(request)
		return WSGIRequest(environ)

SUBTRACT_METHOD_PARAMETERS = {
	'subtrahend': {
		'type': 'int',
	},
	'minuend': {
		'type': 'int',
	},
}

class test_responses(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.json_rpc_controller = JsonRpcController()

		@cls.json_rpc_controller.add_route()
		def subtract(request, x, y):
			return x - y

		@cls.json_rpc_controller.add_route()
		def subtract_named(request, subtrahend, minuend):
			return minuend - subtrahend

		@cls.json_rpc_controller.add_route(required_parameters=SUBTRACT_METHOD_PARAMETERS)
		def subtract_named_required(request, subtrahend, minuend):
			return minuend - subtrahend

		cls.factory = RequestFactory()

	def test_positional_params(self):
		payload = '{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		self.assertEqual('{"jsonrpc": "2.0", "result": 19, "id": 1}', res.content)

		content = json.loads(res.content)
		self.assertEqual(19, content["result"])

	def test_named_params(self):
		payload = '{"jsonrpc": "2.0", "method": "subtract_named", "params": {"subtrahend": 23, "minuend": 42}, "id": 3}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		self.assertEqual('{"jsonrpc": "2.0", "result": 19, "id": 3}', res.content)

		content = json.loads(res.content)
		self.assertEqual(19, content["result"])

	def test_invalid_positional_params(self):
		payload = '{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23, 3], "id": 3}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		self.assertEqual('{"jsonrpc": "2.0", "id": 3, "error": {"message": "Invalid method parameter(s).", "code": -32602}}', res.content)


	def test_invalid_named_params(self):
		payload = '{"jsonrpc": "2.0", "method": "subtract_named", "params": {"subtrahend": 23, "minuendzzzz": 42}, "id": 3}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		# parameters are not validated before calling route so we can expect an internal server error here
		self.assertEqual('{"jsonrpc": "2.0", "id": 3, "error": {"message": "Internal JSON-RPC error.", "code": -32603}}', res.content)


	def test_named_params_required(self):
		payload = '{"jsonrpc": "2.0", "method": "subtract_named_required", "params": {"subtrahend": 23, "minuend": 42}, "id": 3}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		self.assertEqual('{"jsonrpc": "2.0", "result": 19, "id": 3}', res.content)

		content = json.loads(res.content)
		self.assertEqual(19, content["result"])

	def test_invalid_named_params_required(self):
		payload = '{"jsonrpc": "2.0", "method": "subtract_named_required", "params": {"subtrahend": 23, "minuendzzzz": 42}, "id": 3}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		# parameters are validated before calling route so we can now expect an invalid parameters error
		self.assertEqual('{"jsonrpc": "2.0", "id": 3, "error": {"message": "Invalid method parameter(s).", "code": -32602}}', res.content)

	def test_method_not_found(self):
		payload = '{"jsonrpc": "2.0", "method": "foo", "params": {"subtrahend": 23, "minuendzzzz": 42}, "id": 3}'
		req = self.factory.request(payload)
		res = self.json_rpc_controller(req)

		# parameters are validated before calling route so we can now expect an invalid parameters error
		self.assertEqual('{"jsonrpc": "2.0", "id": 3, "error": {"message": "The method does not exist / is not available.", "code": -32601}}', res.content)












