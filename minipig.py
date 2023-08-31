import socket
from typing import Callable,Any
from collections import namedtuple
import io
import sys
import time

HTTP_header = namedtuple('HTTP_header',['method','path','version'])



class WSGIServer:
    """一个简易的WSGI服务器"""
    
    default_sev_address = '',7777
    
    def __init__(self,server_address:tuple) -> None:
        self.server_soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_soc.bind(server_address or self.default_sev_address)
        self.server_soc.listen(1)
        host,port = self.server_soc.getsockname()[:2] #返回该socket的主机名和端口号
        self.server_name = socket.getfqdn(host) #返回完整限定域名
        self.server_port = port
        self.header_set = [] #用于接收app传回来的头部
        self.app = None #web应用
    
    
    def server_forever(self) -> None:
        sev = self.server_soc
        while True:
            self.client_conn,self.client_addr = sev.accept()
            self.handle_one_request()
    
    def set_app(self,app:Callable) -> None:
        """设置Web应用"""
        self.app = app
    
    def handle_one_request(self) -> None:
        """处理请求"""
        request_data = self.client_conn.recv(1024)
        self.request_data = request_data.decode('utf-8')
        environment =self.make_environment(self.request_data)
        response_body = self.app(environment,self.start_response)        
        try:
            response = self.make_response(response_body)
        
            self.client_conn.sendall(response)
        finally:
            self.client_conn.close()
        
    
    
    def make_environment(self,request):
        env = {}
        request_header = self.parse_request_data(request)
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = io.StringIO(self.request_data)
        env['wsgi.errors']  = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False
        env['REQUEST_METHOD'] = request_header.method
        env['PATH_INFO'] = request_header.path
        env['SERVER_NAME'] = self.server_name
        env['SERVER_PORT'] = self.server_port
        
        return env
    
    
    def parse_request_data(self,request:str) -> HTTP_header:
        """目前只解析http头部先"""
        request_header = request.splitlines()[0]
        request_header = request_header.rstrip('\r\n')
        method,path,version = request_header.split()
        request_header = HTTP_header(method=method,path=path,version=version)
        
        return  request_header
    
    
    def start_response(self, status, response_headers, exc_info=None):
        now_str = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
        server_header = [('Server','minipig v0.2'),
                         ('Date',now_str)]
        self.response_headers = [status, response_headers + server_header]
    
    
    def make_response(self,response_body) -> bytes:
        status_code,response_headers = self.response_headers
        response = f'HTTP/1.1 {status_code}\r\n'
        for h in response_headers:
            response += f'{h[0]} : {h[1]}\r\n'
        response += '\r\n'
        for rb in response_body:
            response += rb.decode('utf-8')
        
        response_bytes = response.encode()
        return response_bytes

def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    try:
        module = __import__(module)
    except ImportError:
        sys.exit('can find module')
    app = getattr(module,application)
    http_server = make_server(None, app)
    print(f'WSGIServer: Serving HTTP on port {http_server.server_port} ...\n')
    http_server.server_forever()
    