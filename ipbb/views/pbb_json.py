from sqlalchemy.sql.expression import text 
from pyramid.view import view_config
from pyramid_rpc.jsonrpc import jsonrpc_method
from hashlib import md5
from datetime import datetime
from ..models import (
    DBSession, 
    )
from ..models.ipbb import (
    Registers)
import hmac
import hashlib
import base64
import json
import requests
from ..tools import (
    get_settings,
    )
from ..models import (
    User,
    )

LIMIT = 1000
CODE_OK = 0
CODE_NOT_FOUND = -1
CODE_INVALID_LOGIN = -10
CODE_NETWORK_ERROR = -11

########        
# Auth #
########
def auth(username, signature, fkey):
    settings = get_settings()
    user = User.get_by_name(username)
    if not user:
        return
    
    value = "%s&%s" % (username,int(fkey)); 
    key = str(user.rpc_password)
    lsignature = hmac.new(key, msg=value, digestmod=hashlib.sha256).digest()
    encodedSignature = base64.encodestring(lsignature).replace('\n', '')
    
    if encodedSignature==signature:
       return user


def auth_from_rpc(request):
    user = auth(request.environ['HTTP_USERID'], request.environ['HTTP_SIGNATURE'], request.environ['HTTP_KEY'])
    if user:
        return dict(code=CODE_OK, message='OK')
    return dict(code=CODE_INVALID_LOGIN, message='Gagal login')
    
#######        
# PBB #
#######
def generate_header(userid,password):
    utc_date = datetime.utcnow()
    tStamp = int((utc_date-datetime.strptime('1970-01-01 00:00:00','%Y-%m-%d %H:%M:%S')).total_seconds())
    value = "%s&%s" % (str(userid),tStamp)
    key = str(password) 
    signature = hmac.new(key, msg=value, digestmod=hashlib.sha256).digest() 
    encodedSignature = base64.encodestring(signature).replace('\n', '')
    headers = {'userid':userid,
               'signature':encodedSignature,
               'key':tStamp}
    return headers
    
@jsonrpc_method(method='get_ipbb', endpoint='pbb')
def get_ipbb(request, nop):
    resp = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
        
    nop = nop.strip()
    pemda = nop[:4]
    row = DBSession.query(Registers).filter_by(kode=pemda, status=1).first()
    if not row:
        return dict(code=CODE_NOT_FOUND, message='Pemda Not Registered')
        
    headers = generate_header(row.rpc_userid, row.rpc_password)
    #headers = generate_header('admin', 'admin')
    
    data = {
              "jsonrpc": "2.0",
              "method": "get_ipbb",
              "params": [nop],
              "id":1
            }
            
    jsondata=json.dumps(data, ensure_ascii=False)        
    url = row.rpc_url
    rows = requests.post(url, data=jsondata,headers=headers)
    row_dicted = json.loads(rows.text)
    if 'result' in row_dicted:
        if row_dicted['result']['code']==0:
            return row_dicted['result']
 
    return dict(code=CODE_NETWORK_ERROR, message='Network Error')
   