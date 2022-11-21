# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import json
from datetime import date, datetime

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, cint
from zcrmsdk.src.com.zoho.api.authenticator.oauth_token import OAuthToken
from zcrmsdk.src.com.zoho.api.authenticator.store import FileStore
from zcrmsdk.src.com.zoho.crm.api import HeaderMap, ParameterMap
from zcrmsdk.src.com.zoho.crm.api.dc import INDataCenter, USDataCenter
from zcrmsdk.src.com.zoho.crm.api.initializer import Initializer
from zcrmsdk.src.com.zoho.crm.api.record import Record as crm_record
from zcrmsdk.src.com.zoho.crm.api.record import RecordOperations, Record
from zcrmsdk.src.com.zoho.crm.api.sdk_config import SDKConfig
from zcrmsdk.src.com.zoho.crm.api.user_signature import UserSignature
from zcrmsdk.src.com.zoho.crm.api.users.user import User as crm_user
from zcrmsdk.src.com.zoho.crm.api.util.choice import Choice as crm_choice
from zcrmsdk.src.com.zoho.crm.api.record.body_wrapper import BodyWrapper
from zcrmsdk.src.com.zoho.crm.api.record.success_response import SuccessResponse
from zcrmsdk.src.com.zoho.crm.api.record.action_wrapper import ActionWrapper
from zcrmsdk.src.com.zoho.crm.api.util import Choice
from zcrmsdk.src.com.zoho.crm.api.record import *


def initialize_crm():
    def _initialize(settings):
        environment = globals()[settings.data_center].PRODUCTION()
        token = OAuthToken(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            grant_token=settings.grant_token,
            redirect_url=settings.redirect_uri,
        )

        sdk_config = SDKConfig(auto_refresh_fields=True, pick_list_validation=False)

        Initializer.initialize(
            user=UserSignature(settings.user_email),
            environment=environment,
            token=token,
            store=FileStore(settings.file_store_file_path),
            sdk_config=sdk_config,
            resource_path=settings.resource_path,
        )

    settings = frappe.get_doc("ZohoCRM Settings")
    _initialize(settings)


def get_owner(record):
    owner = record.get_key_value("Owner")
    return owner and owner.get_key_value("email")


def get_utc(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def get_modified_time(record):
    return get_utc(record.get_modified_time())


def get_created_time(record):
    return get_utc(record.get_created_time())


def get_modified_by(record):
    return record.get_modified_by().get_key_value("email")


def get_created_by(record):
    return record.get_created_by().get_key_value("email")


CRM_STANDARD_FIELDS = [
    "crm_id",
    "crm_owner",
    "crm_created_by",
    "crm_created_time",
    "crm_modified_by",
    "crm_modified_time",
]


class RecordEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S.%f")
        elif isinstance(obj, crm_user):
            return obj.get_key_value("email")
        elif isinstance(obj, crm_choice):
            return obj.get_value()
        elif isinstance(obj, crm_record):
            return json.dumps(obj.get_key_values(), cls=RecordEncoder)

        return json.JSONEncoder.default(self, obj)


def get_by_id(doctype, crm_id):
    name = frappe.get_value(doctype, filters={"crm_id": cstr(crm_id)})
    if name:
        return frappe.get_doc(doctype, name)


def get_crm_key(fieldname):
    return frappe.unscrub(fieldname).replace(" ", "_")


class CRMEntitySync(Document):
    def __init__(self, *args, **kwargs):
        self.record_operations = RecordOperations()
        self.header_instance = HeaderMap()
        self.param_instance = ParameterMap()

        if not Initializer.get_initializer():
            initialize_crm()

        super(CRMEntitySync, self).__init__(*args, **kwargs)

    @frappe.whitelist()
    def run_sync(self, entity_id=None):
        self._sync(last_modified=self.last_sync_time, entity_id=entity_id)

    def _sync(self, last_modified=None, entity_id=None):
        module_name = self.crm_entity_name
        print("syncing %s since %s" % (module_name, last_modified))

        if entity_id:
            print("syncing: ", entity_id, module_name)
            self.param_instance.add(GetRecordsParam.ids, cstr(entity_id))

        if last_modified:
            pass
            # self.header_instance.add(GetRecordHeader.if_modified_since, last_modified)

        response = self.record_operations.get_records(
            module_name, self.param_instance, self.header_instance
        )

        response_object = response.get_object()
        if response_object is not None:
            if isinstance(response_object, object):
                try:
                    for d in response_object.get_data():
                        print(d)
                        self.sync_doc(d)

                    if not entity_id:
                        self.db_set("last_sync_time", frappe.utils.now())
                except frappe.exceptions.DoesNotExistError:
                    pass

    def sync_doc(self, record=None):
        id = cstr(record.get_id())
        doc = (
            frappe.db.exists("CRM Entity", id)
            and frappe.get_doc("CRM Entity", id)
            or frappe.get_doc(
                {
                    "doctype": "CRM Entity",
                    "crm_id": id,
                    "crm_module": self.crm_entity_name,
                    "crm_created_time": get_created_time(record),
                    "crm_created_by": get_created_by(record),
                    "frappe_doctype": self.frappe_doctype,
                }
            )
        )
        doc.update(
            {
                "crm_owner": get_owner(record),
                "crm_modified_time": get_modified_time(record),
                "crm_modified_by": get_modified_by(record),
            }
        )
        doc.set(
            "data_json",
            json.dumps(record.get_key_values(), cls=RecordEncoder),
        )
        doc.save()

    def write_to_crm(self, doc):
        # https://www.zoho.com/crm/developer/docs/python-sdk/v2/record-samples.html?src=update_records
        record = Record()
        record.set_id(int(doc.crm_id))

        for field in doc.meta.get_data_fields():
            if field.fieldname in CRM_STANDARD_FIELDS:
                continue
            key = get_crm_key(field.fieldname)
            record.add_key_value(key, doc.get(field.fieldname) or "")

        for field in doc.meta.get_select_fields():
            if field.fieldname in CRM_STANDARD_FIELDS:
                continue
            key = get_crm_key(field.fieldname)
            # record.add_key_value(key, Choice(doc.get(field.fieldname)))

        for field in doc.meta.get("fields", {"fieldtype": "Int"}):
            key = get_crm_key(field.fieldname)
            record.add_key_value(key, doc.get(field.fieldname))
            print(key, doc.get(field.fieldname))

        for field in doc.meta.get(
            "fields", {"fieldtype": ["in", ["Currency", "Float"]]}
        ):
            key = get_crm_key(field.fieldname)
            record.add_key_value(key, flt(doc.get(field.fieldname)))

        request = BodyWrapper()
        request.set_data([record])

        response = self.record_operations.update_records(
            "Accounts", request, self.header_instance
        )
        if response is not None:
            response_object = response.get_object()
            if isinstance(response_object, ActionWrapper):
                for action_response in response_object.get_data():
                    if isinstance(action_response, SuccessResponse):
                        frappe.msgprint(
                            "updated %s: %s in crm" % (doc.doctype, doc.name), alert=1
                        )
                        print(action_response.get_details())
                        return

        print("Doc could not be synced")
