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


class test_responses(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.json_rpc_controller = JsonRpcController()

        @cls.json_rpc_controller.add_route()
        def subtract(request, x, y):
            return x - y

        cls.factory = RequestFactory()

    def test_positional_params(self):
        payload = '{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}'
        req = self.factory.request(payload)
        res = self.json_rpc_controller(req)

        self.assertEqual('{"jsonrpc": "2.0", "result": 19, "id": 1}', res.content)

        content = json.loads(res.content)
        self.assertEqual(19, content["result"])

