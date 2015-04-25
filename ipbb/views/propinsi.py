from sqlalchemy import not_
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from datatables import ColumnDT, DataTables
    
from ..models import (
    DBSession,
    )

from ..models.ipbb import(
       Propinsi)

SESS_ADD_FAILED = 'propinsi add failed'
SESS_EDIT_FAILED = 'propinsi edit failed'

########                    
# List #
########    
@view_config(route_name='propinsi', renderer='templates/propinsi/list.pt',
             permission='edit')
def view_list(request):
    #rows = DBSession.query(Propinsi).filter(Propinsi.id > 0).order_by('email')
    return dict(rows=1)
    
##########                    
# Action #
##########    
@view_config(route_name='propinsi-act', renderer='json')
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
        
        query = Propinsi.query()
        rowTable = DataTables(req, Propinsi, query, columns)
        return rowTable.output_result()
        
#######    
# Add #
#######
def form_validator(form, value):
    def err_name():
        raise colander.Invalid(form,
            'Propinsi %s already used by ID %d' % (
                value['nama'], found.id))
                
    def err_code():
        raise colander.Invalid(form,
            'Propinsi %s already used by ID %d' % (
                value['kode'], found.id))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Propinsi).filter_by(id=uid)
        propinsi = q.first()
    else:
        propinsi = None
        
    if 'nama' in value: # optional
        found = Propinsi.get_by_nama(value['nama'])
        if propinsi:
            if found and found.id != propinsi.id:
                err_name()
        elif found:
            err_name()
            
    if 'kode' in value: # optional
        found = Propinsi.get_by_kode(value['kode'])
        if propinsi:
            if found and found.id != propinsi.id:
                err_code()
        elif found:
            err_code()
            
@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )    

class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
                    colander.String(),
                    widget=widget.TextInputWidget(
                                  mask='99',
                                  mask_placeholder = '#'),
                                  
                    )
                    
    nama = colander.SchemaNode(
                    colander.String(),
                    widget=widget.TextInputWidget(
                                  max_len=30),
                    )

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, propinsi, row=None):
    if not row:
        row = Propinsi()
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Propinsi %s has been saved.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('propinsi'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='propinsi-add', renderer='templates/propinsi/add.pt',
             permission='edit')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('propinsi-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Propinsi).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Propinsi ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='propinsi-edit', renderer='templates/propinsi/edit.pt',
             permission='edit')
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
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('propinsi-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='propinsi-delete', renderer='templates/propinsi/delete.pt',
             permission='edit')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Propinsi ID %d %s has been deleted.' % (row.id, row.email)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

