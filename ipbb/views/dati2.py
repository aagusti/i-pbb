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
       Propinsi, Dati2)
from ..views.tools import deferred_propinsi

SESS_ADD_FAILED = 'dati2 add failed'
SESS_EDIT_FAILED = 'dati2 edit failed'

########                    
# List #
########    
@view_config(route_name='dati2', renderer='templates/dati2/list.pt',
             permission='edit')
def view_list(request):
    #rows = DBSession.query(Dati2).filter(Dati2.id > 0).order_by('email')
    return dict(rows=1)
    
##########                    
# Action #
##########    
@view_config(route_name='dati2-act', renderer='json')
def register_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('propinsi.kode'))
        columns.append(ColumnDT('propinsi.nama'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        
        query = Dati2.query().join(Propinsi)
        rowTable = DataTables(req, Dati2, query, columns)
        return rowTable.output_result()
        
#######    
# Add #
#######
def form_validator(form, value):
    def err_name():
        raise colander.Invalid(form,
            'Dati2 %s already used by ID %d' % (
                value['nama'], found.id))
                
    def err_code():
        raise colander.Invalid(form,
            'Dati2 %s already used by ID %d' % (
                value['kode'], found.id))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Dati2).filter_by(id=uid)
        dati2 = q.first()
    else:
        dati2 = None
        
    if 'nama' in value: # optional
        found = Dati2.get_by_nama(value['nama'])
        if dati2:
            if found and found.id != dati2.id:
                err_name()
        elif found:
            err_name()
            
    if 'kode' in value: # optional
        found = Dati2.get_by_kode(value['propinsi_id'], value['kode'])
        if dati2:
            if found and found.id != dati2.id:
                err_code()
        elif found:
            err_code()
            
class AddSchema(colander.Schema):
                    
    propinsi_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_propinsi,
                    title = 'Propinsi')
                    
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
                    title='Nama Kab'
                    )

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_propinsi=Propinsi.get_deferred())
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, dati2, row=None):
    if not row:
        row = Dati2()
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Dati2 %s has been saved.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('dati2'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='dati2-add', renderer='templates/dati2/add.pt',
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
                return HTTPFound(location=request.route_url('dati2-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Dati2).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Dati2 ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='dati2-edit', renderer='templates/dati2/edit.pt',
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
                return HTTPFound(location=request.route_url('dati2-edit',
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
@view_config(route_name='dati2-delete', renderer='templates/dati2/delete.pt',
             permission='edit')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Dati2 ID %d %s has been deleted.' % (row.id, row.email)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

