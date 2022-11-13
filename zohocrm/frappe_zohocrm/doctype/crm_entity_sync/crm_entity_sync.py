# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from zcrmsdk.src.com.zoho.crm.api import HeaderMap, ParameterMap
from zcrmsdk.src.com.zoho.crm.api.util.choice import Choice as crm_choice
from zcrmsdk.src.com.zoho.crm.api.users.user import User as crm_user
from zcrmsdk.src.com.zoho.crm.api.record import (
    Record as crm_record,
    RecordOperations,
)
from frappe.utils import cstr
import json
from datetime import datetime, date
from zcrmsdk.src.com.zoho.crm.api.initializer import Initializer
from zcrmsdk.src.com.zoho.api.authenticator.oauth_token import OAuthToken
from zcrmsdk.src.com.zoho.crm.api.sdk_config import SDKConfig
from zcrmsdk.src.com.zoho.api.authenticator.store import FileStore
from zcrmsdk.src.com.zoho.crm.api.user_signature import UserSignature
from zcrmsdk.src.com.zoho.crm.api.dc import USDataCenter, INDataCenter


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


class CRMEntitySync(Document):
    def __init__(self, *args, **kwargs):
        self.record_operations = RecordOperations()
        self.header_instance = HeaderMap()
        self.param_instance = ParameterMap()

        if not Initializer.get_initializer():
            initialize_crm()

        super(CRMEntitySync, self).__init__(*args, **kwargs)

    @frappe.whitelist()
    def run_sync(self):

        frappe.msgprint("Enqueued syncing for: " + self.crm_entity_name, alert=True)
        self._sync(self.crm_entity_name, last_modified=self.last_sync_time)

    def get_crm_owner(self, record):
        owner = record.get_key_value("Owner")
        if owner:
            return owner.get_key_value("email")

    def _sync(self, module_name, last_modified=None):
        print("syncing %s since %s" % (module_name, last_modified))
        response = self.record_operations.get_records(
            module_name, self.param_instance, self.header_instance
        )

        response_object = response.get_object()
        if response_object is not None:
            if isinstance(response_object, object):
                try:
                    for d in response_object.get_data():
                        id = cstr(d.get_id())
                        doc = (
                            frappe.db.exists("CRM Entity", id)
                            and frappe.get_doc("CRM Entity", id)
                            or frappe.get_doc(
                                {
                                    "doctype": "CRM Entity",
                                    "crm_id": id,
                                    "crm_module": module_name,
                                    "crm_created_time": get_created_time(d),
                                    "crm_created_by": get_created_by(d),
                                    "frappe_doctype": self.frappe_doctype,
                                }
                            )
                        )
                        doc.update(
                            {
                                "crm_owner": self.get_crm_owner(d),
                                "crm_modified_time": get_modified_time(d),
                                "crm_modified_by": get_modified_by(d),
                            }
                        )
                        doc.set(
                            "data_json",
                            json.dumps(d.get_key_values(), cls=RecordEncoder),
                        )
                        doc.save()
                    self.db_set("last_sync_time", frappe.utils.now())
                except frappe.exceptions.DoesNotExistError:
                    pass
