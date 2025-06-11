import calendar

from pymisp import PyMISP
from ..db_class.db import *
import uuid
import json
import datetime
from ..utils import utils, jsonschema_flowintel
from ..case.TaskCore import TaskModel
from ..case.CaseCore import CaseModel
from ..templating.TemplateCase import TemplateModel
from ..templating.TaskTemplateCore import TaskModel as TaskTemplateModel


def case_creation_from_importer(case, current_user):
    if not utils.validateImporterJson(case, jsonschema_flowintel.caseSchema):
        return {"message": f"Case '{case['title']}' format not okay"}
    for task in case["tasks"]:
        if not utils.validateImporterJson(task, jsonschema_flowintel.taskSchema):
            return {"message": f"Task '{task['title']}' format not okay"}


    #######################
    ## Case Verification ##
    #######################

    ## Caseformat is valid
    # title
    if Case.query.filter_by(title=case["title"]).first():
        return {"message": f"Case Title '{case['title']}' already exist"}
    # deadline
    if case["deadline"]:
        try:
            loc_date = datetime.datetime.strptime(case["deadline"], "%Y-%m-%d %H:%M")
            case["deadline_date"] = loc_date.date()
            case["deadline_time"] = loc_date.time()
        except Exception as e:
            print(e)
            return {"message": f"Case '{case['title']}': deadline bad format, %Y-%m-%d %H:%M"}
    else:
        case["deadline_date"] = ""
        case["deadline_time"] = ""
    # recurring_date
    if case["recurring_date"]:
        if case["recurring_type"]:
            try:
                datetime.datetime.strptime(case["recurring_date"], "%Y-%m-%d %H:%M")
            except:
                return {"message": f"Case '{case['title']}': recurring_date bad format, %Y-%m-%d"}
        else:
            return {"message": f"Case '{case['title']}': recurring_type is missing"}
    # recurring_type
    if case["recurring_type"] and not case["recurring_date"]:
        return {"message": f"Case '{case['title']}': recurring_date is missing"}
    # uuid
    if Case.query.filter_by(uuid=case["uuid"]).first():
        case["uuid"] = str(uuid.uuid4())

    # tags
    for tag in case["tags"]:
        if not utils.check_tag(tag):
            return {"message": f"Case '{case['title']}': tag '{tag}' doesn't exist"}
    
    # Clusters
    for i in range(0, len(case["clusters"])):
        case["clusters"][i] = case["clusters"][i]["name"]

    case["custom_tags"] = []
        
    
    #######################
    ## Task Verification ##
    #######################

    ## Task format is valid
    for task in case["tasks"]:
        if Task.query.filter_by(uuid=task["uuid"]).first():
            task["uuid"] = str(uuid.uuid4())

        if task["deadline"]:
            try:
                loc_date = datetime.datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                task["deadline_date"] = loc_date.date()
                task["deadline_time"] = loc_date.time()
            except:
                return {"message": f"Task '{task['title']}': deadline bad format, %Y-%m-%d %H:%M"}
        else:
            task["deadline_date"] = ""
            task["deadline_time"] = ""

        for tag in task["tags"]:
            if not utils.check_tag(tag):
                return {"message": f"Task '{task['title']}': tag '{tag}' doesn't exist"}
            
        # Clusters
        for i in range(0, len(task["clusters"])):
            task["clusters"][i] = task["clusters"][i]["name"]
        
        task["custom_tags"] = []

    #################
    ## DB Creation ##
    ################

    ## Case creation
    case_created = CaseModel.create_case(case, current_user)
    if case["notes"]:
        CaseModel.modif_note_core(case_created.id, current_user, case["notes"])

    ## Task creation
    for task in case["tasks"]:
        task_created = TaskModel.create_task(task, case_created.id, current_user)
        if task["notes"]:
            for note in task["notes"]:
                loc_note = TaskModel.create_note(task_created.id, current_user)
                TaskModel.modif_note_core(task_created.id, current_user, note["note"], loc_note.id)
        
        if task["subtasks"]:
            for subtask in task["subtasks"]:
                TaskModel.create_subtask(task_created.id, subtask["description"], current_user)
        
        if task["urls_tools"]:
            for urls_tools in task["urls_tools"]:
                TaskModel.create_url_tool(task_created.id, urls_tools["name"], current_user)


def case_template_creation_from_importer(template):
    if not utils.validateImporterJson(template, jsonschema_flowintel.caseTemplateSchema):
        return {"message": f"Case template '{template['title']}' format not okay"}
    for task in template["tasks_template"]:
        if not utils.validateImporterJson(task, jsonschema_flowintel.taskTemplateSchema):
            return {"message": f"Task Template '{task['title']}' format not okay"}
        
    #######################
    ## Case Verification ##
    #######################

    ## Caseformat is valid
    # title
    if Case_Template.query.filter_by(title=template["title"]).first():
        return {"message": f"Case Template Title '{template['title']}' already exist"}
    
    # uuid
    if Case_Template.query.filter_by(uuid=template["uuid"]).first():
        template["uuid"] = str(uuid.uuid4())

    # tags
    for tag in template["tags"]:
        if not utils.check_tag(tag):
            return {"message": f"Case Template '{template['title']}': tag '{tag}' doesn't exist"}
    
    # Clusters
    for i in range(0, len(template["clusters"])):
        template["clusters"][i] = template["clusters"][i]["name"]

    template["custom_tags"] = []
        
    
    #######################
    ## Task Verification ##
    #######################

    ## Task format is valid
    for task in template["tasks_template"]:
        if Task.query.filter_by(uuid=task["uuid"]).first():
            task["uuid"] = str(uuid.uuid4())

        for tag in task["tags"]:
            if not utils.check_tag(tag):
                return {"message": f"Task '{task['title']}': tag '{tag}' doesn't exist"}
            
        # Clusters
        for i in range(0, len(task["clusters"])):
            task["clusters"][i] = task["clusters"][i]["name"]
        
        task["custom_tags"] = []

    #################
    ## DB Creation ##
    ################

    ## Case creation
    template["tasks"] = []
    case_created = TemplateModel.create_case(template)
    if template["notes"]:
        TemplateModel.modif_note_core(case_created.id, template["notes"])

    ## Task creation
    for task in template["tasks_template"]:
        # task_created = TaskModel.create_task(task, case_created.id, current_user)
        task_created = TaskTemplateModel.add_task_template_core(task)
        TemplateModel.add_task_case_template({"tasks": [task_created.id]}, case_created.id)
        if task["notes"]:
            for note in task["notes"]:
                loc_note = TaskTemplateModel.create_note(task_created.id)
                TaskTemplateModel.modif_note_core(task_created.id, note["note"], loc_note.id)
        
        if task["subtasks"]:
            for subtask in task["subtasks"]:
                TaskTemplateModel.create_subtask(task_created.id, subtask["description"])
        
        if task["urls_tools"]:
            for urls_tools in task["urls_tools"]:
                TaskTemplateModel.create_url_tool(task_created.id, urls_tools["name"])



    
def importer_core(files_list, current_user, importer_type):
    for file in files_list:
        if files_list[file].filename:
            try:
                file_data = json.loads(files_list[file].read().decode())
                if type(file_data) == list:
                    for case in file_data:
                        if importer_type == 'case':
                            res = case_creation_from_importer(case, current_user)
                        elif importer_type == 'template':
                            res = case_template_creation_from_importer(case, current_user)
                        if res: return res
                else:
                    if importer_type == 'case':
                        return case_creation_from_importer(file_data, current_user)
                    elif importer_type == 'template':
                        return case_template_creation_from_importer(file_data)
            except Exception as e:
                print(e)
                return {"message": "Something went wrong"}


def chart_dict_constructor(input_dict):
    loc_dict = []
    for elem in input_dict:
        loc_dict.append({
            "calendar": elem,
            "count": input_dict[elem]
        })
    return loc_dict

def stats_core(cases):
    cases_opened_month = {month: 0 for month in calendar.month_name if month}
    cases_opened_year = {}
    cases_closed_month = {month: 0 for month in calendar.month_name if month}
    cases_closed_year = {}
    cases_elapsed_time = {}
    total_opened_cases = 0
    total_closed_cases = 0

    tasks_opened_month = {month: 0 for month in calendar.month_name if month}
    tasks_opened_year = {}
    tasks_closed_month = {month: 0 for month in calendar.month_name if month}
    tasks_closed_year = {}
    tasks_elapsed_time = {}
    tasks_per_case = {}
    total_opened_tasks = 0
    total_closed_tasks = 0

    current_year = datetime.datetime.now().year

    for case in cases:
        if case.creation_date.year == current_year:
            cases_opened_month[case.creation_date.strftime("%B")] += 1
            if case.finish_date:
                cases_closed_month[case.finish_date.strftime("%B")] += 1

        if case.creation_date.year not in cases_opened_year: # initialize dict
            cases_opened_year[case.creation_date.year] = 0
        cases_opened_year[case.creation_date.year] += 1

        if case.finish_date:
            if case.finish_date.year not in cases_closed_year: # initialize dict
                cases_closed_year[case.finish_date.year] = 0
            cases_closed_year[case.finish_date.year] += 1

            loc = case.finish_date - case.creation_date
            loc = loc.days // 7
            if loc not in cases_elapsed_time:
                cases_elapsed_time[loc] = 0
            cases_elapsed_time[loc] += 1

            total_closed_cases += 1
        else:
            total_opened_cases += 1

        # Tasks part
        for task in case.tasks:
            if task.creation_date.year == current_year:
                tasks_opened_month[task.creation_date.strftime("%B")] += 1
                if task.finish_date:
                    tasks_closed_month[task.finish_date.strftime("%B")] += 1

            if task.creation_date.year not in tasks_opened_year: # initialize dict
                tasks_opened_year[task.creation_date.year] = 0
            tasks_opened_year[task.creation_date.year] += 1

            if task.finish_date:
                if task.finish_date.year not in tasks_closed_year: # initialize dict
                    tasks_closed_year[task.finish_date.year] = 0
                tasks_closed_year[task.finish_date.year] += 1

                loc = task.finish_date - task.creation_date
                loc = loc.days // 7
                if loc not in tasks_elapsed_time:
                    tasks_elapsed_time[loc] = 0
                tasks_elapsed_time[loc] += 1

                total_closed_tasks += 1
            else:
                total_opened_tasks += 1
            
            if not case.nb_tasks in tasks_per_case:
                tasks_per_case[case.nb_tasks] = 0
            tasks_per_case[case.nb_tasks] += 1


    loc_cases_opened_month = chart_dict_constructor(cases_opened_month)
    loc_cases_opened_year = chart_dict_constructor(cases_opened_year)

    loc_cases_closed_month = chart_dict_constructor(cases_closed_month)
    loc_cases_closed_year = chart_dict_constructor(cases_closed_year)

    loc_cases_elapsed_time = chart_dict_constructor(cases_elapsed_time)

    loc_tasks_opened_month = chart_dict_constructor(tasks_opened_month)
    loc_tasks_opened_year = chart_dict_constructor(tasks_opened_year)

    loc_tasks_closed_month = chart_dict_constructor(tasks_closed_month)
    loc_tasks_closed_year = chart_dict_constructor(tasks_closed_year)

    loc_tasks_elapsed_time = chart_dict_constructor(tasks_elapsed_time)
    loc_tasks_per_case = chart_dict_constructor(tasks_per_case)

    return {"cases-opened-month": loc_cases_opened_month, "cases-opened-year": loc_cases_opened_year,
            "cases-closed-month": loc_cases_closed_month, "cases-closed-year": loc_cases_closed_year,
            "cases-elapsed-time": loc_cases_elapsed_time,
            "total_opened_cases": total_opened_cases, "total_closed_cases": total_closed_cases,
            "tasks-opened-month": loc_tasks_opened_month, "tasks-opened-year": loc_tasks_opened_year,
            "tasks-closed-month": loc_tasks_closed_month, "tasks-closed-year": loc_tasks_closed_year,
            "tasks-elapsed-time": loc_tasks_elapsed_time, "tasks-per-case": loc_tasks_per_case,
            "total_opened_tasks": total_opened_tasks, "total_closed_tasks": total_closed_tasks}


        

    # loc_cases_opened_month = [
    #     {'calendar': 'January', 'count': 25}, {'calendar': 'February', 'count': 5}, {'calendar': 'March', 'count': 10}, 
    #     {'calendar': 'April', 'count': 30}, {'calendar': 'May', 'count': 3}, {'calendar': 'June', 'count': 12}, 
    #     {'calendar': 'July', 'count': 4}, {'calendar': 'August', 'count': 33}, {'calendar': 'September', 'count': 21}, 
    #     {'calendar': 'October', 'count': 55}, {'calendar': 'November', 'count': 7}, {'calendar': 'December', 'count': 70}]
    
    # loc_cases_closed_month = [
    #     {'calendar': 'January', 'count': 11}, {'calendar': 'February', 'count': 6}, {'calendar': 'March', 'count': 1}, 
    #     {'calendar': 'April', 'count': 4}, {'calendar': 'May', 'count': 20}, {'calendar': 'June', 'count': 9}, 
    #     {'calendar': 'July', 'count': 3}, {'calendar': 'August', 'count': 3}, {'calendar': 'September', 'count': 30}, 
    #     {'calendar': 'October', 'count': 50}, {'calendar': 'November', 'count': 6}, {'calendar': 'December', 'count': 3}]
    
    # loc_cases_opened_year = [
    #     {'calendar': '2024', "count": 50}, {'calendar': '2025', "count": 31}
    # ]
    # loc_cases_closed_year = [
    #     {'calendar': '2024', "count": 50}, {'calendar': '2025', "count": 20}
    # ]

    # loc_cases_elapsed_time = [
    #     {"calendar": 1, "count": 30}, {"calendar": 5, "count": 20}, {"calendar": 10, "count": 3}, {"calendar": 24, "count": 2}
    # ]

    # return {"cases-opened-month": loc_cases_opened_month, "cases-opened-year": loc_cases_opened_year,
    #         "cases-closed-month": loc_cases_closed_month, "cases-closed-year": loc_cases_closed_year,
    #         "elapsed-time": loc_cases_elapsed_time}

def get_case_by_tags(current_user):
    cases = Case.query.join(Case_Org, Case_Org.case_id==Case.id).where(Case_Org.org_id==current_user.org_id).all()
    dict_case_tag = {}
    dict_case_cluster_tag = {}
    dict_case_custom_tag = {}

    for case in cases:
        custom = Custom_Tags.query.join(Case_Custom_Tags, Case_Custom_Tags.custom_tag_id==Custom_Tags.id).filter_by(case_id=case.id).all()
        for c in custom:
            if not c.name in dict_case_custom_tag:
                dict_case_custom_tag[c.name] = 0
            dict_case_custom_tag[c.name] += 1

        tags = Tags.query.join(Case_Tags, Case_Tags.tag_id==Tags.id).filter_by(case_id=case.id).all()
        for t in tags:
            if not t.name in dict_case_tag:
                dict_case_tag[t.name] = 0
            dict_case_tag[t.name] += 1
        
        cluster = Cluster.query.join(Case_Galaxy_Tags, Case_Galaxy_Tags.cluster_id==Cluster.id).filter_by(case_id=case.id).all()
        for cl in cluster:
            if not cl.tag in dict_case_cluster_tag:
                dict_case_cluster_tag[cl.tag] = 0
            dict_case_cluster_tag[cl.tag] += 1

        
        dict_task_tag = {}
        dict_task_cluster_tag = {}
        dict_task_custom_tag = {}
        for task in case.tasks:
            custom = Custom_Tags.query.join(Task_Custom_Tags, Task_Custom_Tags.custom_tag_id==Custom_Tags.id).filter_by(task_id=task.id).all()
            for c in custom:
                if not c.name in dict_task_custom_tag:
                    dict_task_custom_tag[c.name] = 0
                dict_task_custom_tag[c.name] += 1

            tags = Tags.query.join(Task_Tags, Task_Tags.tag_id==Tags.id).filter_by(task_id=task.id).all()
            for t in tags:
                if not t.name in dict_task_tag:
                    dict_task_tag[t.name] = 0
                dict_task_tag[t.name] += 1
            
            cluster = Cluster.query.join(Task_Galaxy_Tags, Task_Galaxy_Tags.cluster_id==Cluster.id).filter_by(task_id=task.id).all()
            for cl in cluster:
                if not cl.tag in dict_task_cluster_tag:
                    dict_task_cluster_tag[cl.tag] = 0
                dict_task_cluster_tag[cl.tag] += 1


    return {"case_custom_tags": chart_dict_constructor(dict_case_custom_tag), 
            "case_tags": chart_dict_constructor(dict_case_tag), 
            "case_clusters": chart_dict_constructor(dict_case_cluster_tag),
            "task_custom_tags": chart_dict_constructor(dict_task_custom_tag), 
            "task_tags": chart_dict_constructor(dict_task_tag), 
            "task_clusters": chart_dict_constructor(dict_task_cluster_tag)}


########################
# Case from MISP Event #
########################
def check_connection_misp(misp_instance_id: int, current_user: User):
    instance = Connector_Instance.query.get(misp_instance_id)
    if instance:
        user_connector_instance = User_Connector_Instance.query.filter_by(user_id=current_user.id,instance_id=instance.id).first()
        if user_connector_instance:
            # misp = PyMISP(instance.url, user_connector_instance.api_key, ssl=False, timeout=20)
            try:
                misp = PyMISP(instance.url, user_connector_instance.api_key, ssl=False, timeout=20)
            except:
                return "Error connecting to MISP"
            
            return misp
        return "No config found for the instance"
    return "Instance not found"

def check_event(event_id: int, misp_instance_id: int, current_user: User):
    misp = check_connection_misp(misp_instance_id, current_user)
    if type(misp) == PyMISP:
        event = misp.get_event(event_id, pythonify=True)

        if 'errors' in event:
            return "Event not found on this MISP instance"
        
        return event
    else:
        return misp
    

def check_case_misp_event(request_form, current_user) -> str:
    if request_form.get("case_title"):
        if Case.query.filter_by(title=request_form.get("case_title")).first():
            return "Case already exist"
    else:
        return "Case title empty"
    
    if not request_form.get("misp_event_id"):
        return "Need a misp event id"
    
    if not request_form.get("misp_instance_id"):
        return "Need a misp instance"
    
    if not request_form.get("case_template_id"):
        return "Need a case template"
    
    return check_event(request_form.get("misp_event_id"), request_form.get("misp_instance_id"), current_user)

def create_case_misp_event(request_form, current_user):
    instance = Connector_Instance.query.get(request_form.get("misp_instance_id"))
    user_connector_instance = User_Connector_Instance.query.filter_by(user_id=current_user.id,instance_id=instance.id).first()
    misp = PyMISP(instance.url, user_connector_instance.api_key, ssl=False, timeout=20)
    
    event = misp.get_event(request_form.get("misp_event_id"), pythonify=True)

    case = TemplateModel.create_case_from_template(request_form.get("case_template_id"), request_form.get("case_title"), current_user)

    case.description = event.info
    case.ticket_id = f"MISP Event: {request_form.get("misp_event_id")}"
    case.is_private = True
    db.session.commit()

    for misp_tags in event.tags:
        tag = Tags.query.filter_by(name=misp_tags.name).first()
        if tag:
            if not Case_Tags.query.filter_by(tag_id=tag.id, case_id=case.id).first():
                CaseModel.add_tag(tag, case.id)

    for misp_galaxy in event.galaxies:
        for misp_cluster in misp_galaxy.clusters:
            cluster = Cluster.query.filter_by(tag=misp_cluster.tag_name).first()
            if cluster:
                if not Case_Galaxy_Tags.query.filter_by(cluster_id=cluster.id, case_id=case.id).first():
                    CaseModel.add_cluster(cluster, case.id)

    for obje in event.objects:
        loc_object = Case_Misp_Object(
            case_id=case.id,
            template_uuid=obje.template_uuid,
            name=obje.name,
            creation_date = datetime.datetime.now(tz=datetime.timezone.utc),
            last_modif = datetime.datetime.now(tz=datetime.timezone.utc)
        )

        db.session.add(loc_object)
        db.session.commit()

        for object_attr in obje.attributes:
            first_seen = None
            last_seen = None

            if object_attr.get("first_seen"):
                if type(object_attr.get("first_seen")) == datetime.datetime:
                    first_seen = object_attr.get("first_seen")
                else:
                    first_seen = datetime.datetime.strptime(object_attr.get("first_seen"), '%Y-%m-%dT%H:%M')
            if object_attr.get("last_seen"):
                if type(object_attr.get("last_seen")) == datetime.datetime:
                    last_seen = object_attr.get("last_seen")
                else:
                    last_seen = datetime.datetime.strptime(object_attr.get("last_seen"), '%Y-%m-%dT%H:%M')

            attr = Misp_Attribute(
                case_misp_object_id=loc_object.id,
                value=object_attr.value,
                type=object_attr.object_relation,
                first_seen=first_seen,
                last_seen=last_seen,
                comment=object_attr.get("comment"),
                ids_flag=object_attr.to_ids,
                creation_date = datetime.datetime.now(tz=datetime.timezone.utc),
                last_modif = datetime.datetime.now(tz=datetime.timezone.utc)
            )
            db.session.add(attr)
            db.session.commit()
        
        loc_object.last_modif = datetime.datetime.now(tz=datetime.timezone.utc)
        db.session.commit()

    case_connector_instance = Case_Connector_Instance(
        case_id=case.id,
        instance_id=instance.id,
        identifier=request_form.get("misp_event_id")
    )
    db.session.add(case_connector_instance)
    db.session.commit()

    return case


#################
# Note Template #
#################

def get_note_template(note_id: int):
    """Get a note template model"""
    return Note_Template_Model.query.get(note_id)

def get_all_note_template():
    """Get all note template"""
    return Note_Template_Model.query.all()

def get_note_template_by_page(page: int):
    """Get note template by page"""
    return Note_Template_Model.query.paginate(page=page, per_page=20, max_per_page=50)

import re

def extract_variables(template_str: str) -> list:
    return list(set(re.findall(r"{{\s*(\w+)\s*}}", template_str)))

def create_note_template(request_json: dict, current_user: int) -> Note_Template_Model:
    """Create a new note template model"""
    content = request_json["content"]
    list_params = extract_variables(content)
    n = Note_Template_Model(
        title=request_json["title"],
        description=request_json["description"],
        content = content,
        version = 1,
        params={"list": list_params},
        author=current_user.id,
        creation_date=datetime.datetime.now(tz=datetime.timezone.utc),
        last_modif=datetime.datetime.now(tz=datetime.timezone.utc)
    )
    db.session.add(n)
    db.session.commit()

    return n


def edit_content_note_template(note_id: int, request_json: dict) -> bool:
    content = request_json["content"]
    list_params = extract_variables(content)
    note_template = get_note_template(note_id)

    note_template.content = content
    note_template.params = {"list": list_params}

    db.session.commit()
    return True

def edit_note_template(note_id: int, request_json: dict) -> bool:
    note_template = get_note_template(note_id)

    note_template.title = request_json["title"]
    note_template.description = request_json["description"]
    # note_template.version = request_json["description"]

    db.session.commit()
    return True