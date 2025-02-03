import fnmatch
import importlib
import os
import json
import re
import sys
import uuid
import random
import string
import jsonschema
from ..db_class.db import Tags, User
from functools import lru_cache

MODULES = {}
MODULES_CONFIG = {}
MODULE_PATH = os.path.join(os.getcwd(), "app", "modules")


def isUUID(uid):
    """Verify an uuid"""
    try:
        uuid.UUID(str(uid))
        return True
    except ValueError:
        return False


def generate_api_key(length=60):
    """Generate a new api key"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def get_user_api(api_key):
    """Get a user by its api key"""
    return User.query.filter_by(api_key=api_key).first()

def get_user_from_api(headers):
    """Try to get bot user by matrix id. If not, get basic user"""
    if "MATRIX-ID" in headers:
        bot = User.query.filter_by(last_name="Bot", first_name="Matrix").first()
        if bot:
            if bot.api_key == headers["X-API-KEY"]:
                user = User.query.filter_by(matrix_id=headers["MATRIX-ID"]).first()
                if user:
                    return user
    return get_user_api(headers["X-API-KEY"])


def verif_api_key(headers):
    """Check if api key belong to a user"""
    if not "X-API-KEY" in headers:
        return {"message": "Error no API key pass"}, 403
    user = get_user_api(headers["X-API-KEY"])
    if not user:
        return {"message": "API key not found"}, 403
    return {}

def form_to_dict(form):
    """Parse a form into a dict"""
    loc_dict = dict()
    for field in form._fields:
        if field == "files_upload":
            loc_dict[field] = dict()
            loc_dict[field]["data"] = form._fields[field].data
            loc_dict[field]["name"] = form._fields[field].name
        elif not field == "submit" and not field == "csrf_token":
            loc_dict[field] = form._fields[field].data
    return loc_dict

def create_specific_dir(specific_dir):
    """Create a specific directory if it doesn't exist"""
    if not os.path.isdir(specific_dir):
        os.mkdir(specific_dir)


def get_module_type():
    """Get module by type. Enumerate directory of modules."""
    type_list = list()
    for dir in os.listdir(MODULE_PATH):
        type_list.append(dir)
    return type_list

def get_modules_list():
    """Get modules available"""
    modulename_list = list()
    sys.path.append(MODULE_PATH)
    for root, dirnames, filenames in os.walk(MODULE_PATH):
        if os.path.basename(root) == '__pycache__':
            continue
        if re.match(r'^\.', os.path.basename(root)):
            continue
        for filename in fnmatch.filter(filenames, '*.py'):
            if filename == '__init__.py':
                continue
            modulename = filename.split(".")[0]
            root_dir = os.path.basename(root)
            MODULES[modulename] = importlib.import_module(root_dir + '.' + modulename)
            MODULES_CONFIG[modulename] = {"type": root_dir, "config": MODULES[modulename].module_config}
            modulename_list.append(modulename)

    loc_elem = []
    for elem in MODULES_CONFIG:
        if elem not in modulename_list:
            loc_elem.append(elem)
    
    for elem in loc_elem:
        del MODULES_CONFIG[elem]
        del MODULES[elem]

caseSchema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "uuid": {"type": "string"},
        "deadline:": {"type": "string"},
        "recurring_date:": {"type": "string"},
        "recurring_type:": {"type": "string"},
        "notes:": {"type": "string"},
        "is_private:": {"type": "boolean"},
        "tasks": {
            "type": "array", 
            "items": {"type": "object"},
        },
        "tags":{
            "type": "array",
            "items": {"type": "string"},
        },
        "clusters":{
            "type": "array",
            "items": {"type": "object"},
        },
    },
    "required": ['title']
}

taskSchema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "uuid": {"type": "string"},
        "deadline:": {"type": "string"},
        "url:": {"type": "string"},
        "notes:": {
            "type": "array", 
            "items": {"type": "object"},
        },
        "tags":{
            "type": "array",
            "items": {"type": "string"}
        },
        "clusters":{
            "type": "array",
            "items": {"type": "object"},
        },
    },
    "required": ['title']
}

def validateCaseJson(json_data):
    """Validate the format of a case's JSON"""
    try:
        jsonschema.validate(instance=json_data, schema=caseSchema)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        return False
    return True

def validateTaskJson(json_data):
    """Validate the format of a task's JSON"""
    try:
        jsonschema.validate(instance=json_data, schema=taskSchema)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        return False
    return True

def check_tag(tag):
    """Check if a tag exist in db"""
    r = Tags.query.filter_by(name=tag).first()
    if r:
        return True
    return False



@lru_cache
def get_object_templates():
    """Get object template.
    
    Enumerate misp-objects by walking through misp-objects submodule directory
    """
    templates = []
    objects_dir = os.path.join(os.getcwd(), "modules/misp-objects/objects")

    for root, dirs, __ in os.walk(objects_dir):
        for template_dir in dirs:
            template_def = os.path.join(root, template_dir, "definition.json")
            raw_template = open(template_def)
            raw_template = json.load(raw_template)

            attributes = []
            for name, attribute in raw_template["attributes"].items():
                attributes.append(
                    {
                        "name": name,
                        "description": attribute.get("description"),
                        "disable_correlation": attribute.get(
                            "disable_correlation", False
                        ),
                        "misp_attribute": attribute["misp-attribute"],
                        "multiple": attribute.get("multiple", False),
                        "ui_priority": attribute.get("ui-priority", 0),
                        "sane_default": attribute.get("sane_default"),
                    }
                )

            template = {
                "uuid": raw_template["uuid"],
                "name": raw_template["name"],
                "description": raw_template["description"],
                "meta_category": raw_template["meta-category"],
                "version": raw_template["version"],
                "attributes": attributes,
                "requiredOneOf": raw_template.get("requiredOneOf", []),
            }

            templates.append(template)

    templates = sorted(templates, key=lambda d: d['name'])

    return templates
