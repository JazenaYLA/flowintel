from flask import Blueprint, request

from flask_restx import Api, Resource
from ..decorators import api_required, admin_required
from . import connectors_core as ConnectorModel
from . import connectors_core_api as ConnectorModelApi
from ..utils import utils

api_connectors_blueprint = Blueprint('api_connectors', __name__)
api = Api(api_connectors_blueprint,
        title='flowintel API', 
        description='API to manage a case management instance.', 
        version='0.1', 
        default='GenericAPI', 
        default_label='Generic flowintel API', 
        doc='/doc/'
    )



@api.route('/all')
@api.doc(description='Get all Connectors')
class GetConnectors(Resource):
    method_decorators = [api_required]
    def get(self):
        connectors_list = list()
        for connector in ConnectorModel.get_connectors():
            connector_loc = connector.to_json()
            icon_loc = ConnectorModel.get_icon(connector.icon_id)
            icon_file = ConnectorModel.get_icon_file(icon_loc.file_icon_id)
            connector_loc["icon_filename"] = icon_file.name
            connector_loc["icon_uuid"] = icon_file.uuid
            connectors_list.append(connector_loc)
        return {"connectors": connectors_list}, 200
    
@api.route('/<cid>/instances')
@api.doc(description='Get instances of a connector')
class Getinstances(Resource):
    method_decorators = [api_required]
    def get(self, cid):
        connector = ConnectorModel.get_connector(cid)
        current_user = utils.get_user_from_api(request.headers)
        if connector:
            instance_list = list()
            for instance in connector.instances:
                if ConnectorModel.get_user_instance_both(user_id=current_user.id, instance_id=instance.id):
                    instance_list.append(instance.to_json())
            return {"instances": instance_list}, 200
        return {"message": "Connector not found", "toast_class": "danger-subtle"}, 404


@api.route('/add_connector', methods=['POST'])
@api.doc(description='Add a new connector')
class AddConnector(Resource):
    method_decorators = [admin_required, api_required]
    @api.doc(params={
        "name": "Required. Name of the connector",
        "description": "Description of the connector",
        "icon_select": "Id of an icon"
    })
    def post(self):
        if request.json:
            verif_dict = ConnectorModelApi.verif_add_connector(request.json)
            if not "message" in verif_dict:
                connector = ConnectorModel.add_connector_core(verif_dict)
                return {"message": f"Connector created", "connector_id": connector.id}, 200
            return verif_dict, 400
        return {"message": "Please give data"}, 400
    
@api.route('/<cid>/edit_connector', methods=['POST'])
@api.doc(description='Edit a connector')
class EditConnector(Resource):
    method_decorators = [admin_required, api_required]
    @api.doc(params={
        "name": "Required. Name of the connector",
        "description": "Description of the connector",
        "icon_select": "Id of an icon"
    })
    def post(self, cid):
        if request.json:
            verif_dict = ConnectorModelApi.verif_edit_connector(request.json, cid)
            if not "message" in verif_dict:
                connector = ConnectorModel.edit_connector_core(cid, verif_dict)
                return {"message": f"Connector created", "connector_id": connector.id}, 200
            return verif_dict, 400
        return {"message": "Please give data"}, 400
    
@api.route('/<cid>/add_instance', methods=['POST'])
@api.doc(description='Add a new instance of a connector')
class AddInstance(Resource):
    method_decorators = [api_required]
    @api.doc(params={
        "name": "Required. Name of the connector",
        "description": "Description of the connector",
        "type_select": "Name of the type. See '/api/connectors/type_select' for more info",
        "url": "Required. Url for the instance. Used by module to connect to service",
        "api_key": "Api key used by module to connect to service",
    })
    def post(self, cid):
        if ConnectorModel.get_connector(cid):
            if request.json:
                verif_dict = ConnectorModelApi.verif_add_instance(request.json)
                if not "message" in verif_dict:
                    instance = ConnectorModel.add_connector_instance_core(cid, verif_dict, utils.get_user_from_api(request.headers).id)
                    return {"message": f"Instance created", "connector_id": instance.id}, 200
                return verif_dict, 400
            return {"message": "Please give data"}, 400
        return {"message": "Connector not found"}, 404
    
@api.route('/<cid>/edit_instance/<iid>', methods=['POST'])
@api.doc(description='Edit an instance of a connector')
class EditInstance(Resource):
    method_decorators = [api_required]
    @api.doc(params={
        "name": "Required. Name of the connector",
        "description": "Description of the connector",
        "type_select": "Name of the type. See '/api/connectors/type_select' for more info",
        "url": "Required. Url for the instance. Used by module to connect to service",
        "api_key": "Api key used by module to connect to service",
    })
    def post(self, cid, iid):
        if ConnectorModel.get_connector(cid):
            if request.json:
                verif_dict = ConnectorModelApi.verif_edit_instance(request.json)
                if not "message" in verif_dict:
                    instance = ConnectorModel.edit_connector_instance_core(iid, verif_dict)
                    return {"message": f"Instance created", "connector_id": instance.id}, 200
                return verif_dict, 400
            return {"message": "Please give data"}, 400
        return {"message": "Connector not found"}, 404
    
@api.route('/type_select')
@api.doc(description='Get type select for instance')
class GetTypeSelect(Resource):
    method_decorators = [api_required]
    def get(self):
        return {"type_select": utils.get_module_type()}, 200
    

@api.route('/<cid>/delete')
@api.doc(description='Delete Connector')
class DeleteConnector(Resource):
    method_decorators = [admin_required, api_required]
    def get(self, cid):
        if ConnectorModel.get_connector(cid):
            if ConnectorModel.delete_connector_core(cid):
                return {"message":"Connector deleted"}, 200
            return {"message":"Error connector deleted"}, 400
        return {"message":"Connector not found"}, 404
    
@api.route('/<cid>/instance/<iid>/delete')
@api.doc(description='Delete an instance of connector')
class DeleteInstanceConnector(Resource):
    method_decorators = [api_required]
    def get(self, cid, iid):
        if ConnectorModel.get_connector(cid):
            if ConnectorModel.get_instance(iid):
                if ConnectorModel.delete_connector_instance_core(iid):
                    return {"message":"Instance deleted"}, 200
                return {"message":"Error connector deleted"}, 400
            return {"message":"Instance not found"}, 404
        return {"message":"Connector not found"}, 404