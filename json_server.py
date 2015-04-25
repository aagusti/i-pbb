from pyramid.config import Configurator
from pyramid_rpc.jsonrpc import jsonrpc_method

@jsonrpc_method(endpoint='pbb')
def get_ipbb(request, name):
    return 'hello, %s!' % name

def main(global_conf, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_rpc.jsonrpc')
    config.add_jsonrpc_endpoint('pbb', '/pbb')
    config.scan(__name__)
    return config.make_wsgi_app()

if __name__ == '__main__':
    from paste.httpserver import serve
    app = main({})
    serve(app, 'localhost', 6543)