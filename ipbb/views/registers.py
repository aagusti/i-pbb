from email.utils import parseaddr
from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    )
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
import transaction
import colander
from deform import (
    Form,
    ValidationFailure,
    widget,
    )
from ..models import (
    DBSession,User
    )
 
from ..views.tools import (
    deferred_propinsi, deferred_dati2, deferred_periode, deferred_status,
    deferred_bayar, STATUS, BAYAR, PERIODE)
 
from ..models.ipbb import (
    Registers, Propinsi, Dati2
    )
from datatables import ColumnDT, DataTables
from ..models.ipbb import Registers

SESS_ADD_FAILED = 'Register add failed'
SESS_EDIT_FAILED = 'Register edit failed'

############
# Register #
############
@view_config(route_name='register', renderer='templates/register/list.pt')
def view_register(request):
    return dict(project='i-pbb')

    
##########                    
# Action #
##########    
@view_config(route_name='register-act', renderer='json')
def register_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('tgl_register'))
        columns.append(ColumnDT('status'))
        query = DBSession.query(Registers)
        rowTable = DataTables(req, Registers, query, columns)
        return rowTable.output_result()


#######    
# Add #
#######
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')

def form_validator(form, value):
    def err_email():
        raise colander.Invalid(form,
            'Email %s already used by register ID %d' % (
                value['e_mail'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Register name %s already used by ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Registers).filter_by(id=uid)
        register = q.first()
    else:
        register = None
    q = DBSession.query(Registers).filter_by(e_mail=value['e_mail'])
    found = q.first()
    if register:
        if found and found.id != register.id:
            err_email()
    elif found:
        err_email()
    if 'nama' in value: # optional
        found = Registers.get_by_nama(value['nama'])
        if register:
            if found and found.id != register.id:
                err_name()
        elif found:
            err_name()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )    

class AddSchema(colander.Schema):
    e_mail = colander.SchemaNode(colander.String(),
                                validator=email_validator)
                                
    password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=6),
                widget=widget.CheckedPasswordWidget(size=20),
                description='Type your password and confirm it')

    propinsi_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_propinsi,
                    title="Propinsi")
                    
    dati2_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_dati2,
                    title="Kabupaten/Kota")
                  
    alamat_pemda = colander.SchemaNode(
                    colander.String(),
                    )

    no_telpon =  colander.SchemaNode(
                    colander.String())
                    
    nama_pic = colander.SchemaNode(
                    colander.String(),
                    title='Penanggung Jawab')

    nip_pic = colander.SchemaNode(
                    colander.String(),
                    title='NIP')
                    
    no_hp =  colander.SchemaNode(
                    colander.String())

    jns_bayar = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_bayar)

    tagih_nama   = colander.SchemaNode(
                    colander.String())

    tagih_alamat = colander.SchemaNode(
                    colander.String())

    periode_bayar = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_periode)

    rpc_url = colander.SchemaNode(
                    colander.String())

    rpc_userid = colander.SchemaNode(
                    colander.String())

    rpc_password = colander.SchemaNode(
                    colander.String(),
                    widget=widget.PasswordWidget(size=20))

   
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_bayar=BAYAR, daftar_periode=PERIODE, 
                         daftar_propinsi=Propinsi.get_deferred(), daftar_dati2=Dati2.get_deferred())
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = Registers()
    
    user = DBSession.query(User).filter_by(email=values['e_mail']).first()
    if not user:
        user = User()
        
    row.from_dict(values)
    if values['password']:
        row.password = values['password']
        user.password = values['password']
        
    if values['rpc_password']:
        row.rpc_password = values['rpc_password']
    area = Dati2.get_by_id(values['dati2_id'])
    row.kode = "%s%s" % (area.propinsi.kode, area.kode)
    row.nama = area.nama
    if 'id' in values:
        row.tgl_update = datetime.now()
    else:
        row.tgl_register = datetime.now()
        row.tgl_valid = row.tgl_register
        user.status = 1
    user.user_name = values['nip_pic']
    user.email = values['e_mail']
        
    DBSession.add(user)
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Register %s has been saved.' % row.e_mail)
        
def route_list(request):
    return HTTPFound(location=request.route_url('home'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='register-add', renderer='templates/register/add.pt')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #request.session[SESS_ADD_FAILED] = e.render()               
                return dict(form=form) #HTTPFound(location=request.route_url('register-add'))
            save_request(dict(controls), request)
        return route_list(request)
    #elif SESS_ADD_FAILED in request.session:
    #    return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Registers).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Register ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='register-edit', renderer='templates/register/add.pt',
             permission='register-edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #request.session[SESS_EDIT_FAILED] = e.render()               
                return dict(form=form) #return HTTPFound(location=request.route_url('register-edit',
                                  #id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    #elif SESS_EDIT_FAILED in request.session:
    #    return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='register-delete', renderer='templates/register/delete.pt',
             permission='register-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Register ID %d %s has been deleted.' % (row.id, row.e_mail)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())
        