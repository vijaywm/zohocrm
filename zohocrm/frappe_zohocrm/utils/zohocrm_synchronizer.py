# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from datetime import datetime

from zcrmsdk.src.com.zoho.crm.api.record import (
    Record as ZCRMRecord,
    RecordOperations,
    GetRecordsParam,
)
from zcrmsdk.src.com.zoho.crm.api import HeaderMap, ParameterMap

from zohocrm.frappe_zohocrm.utils.zohocrm_record import ZohoCRM_Record

from zcrmsdk.src.com.zoho.crm.api.record import (
    Record as ZCRMRecord,
    RecordOperations,
    GetRecordsParam,
)
from zcrmsdk.src.com.zoho.api.authenticator.oauth_token import OAuthToken
from zcrmsdk.src.com.zoho.api.authenticator.store import FileStore
from zcrmsdk.src.com.zoho.crm.api.user_signature import UserSignature
from zcrmsdk.src.com.zoho.crm.api.sdk_config import SDKConfig
from zcrmsdk.src.com.zoho.crm.api.initializer import Initializer
from zcrmsdk.src.com.zoho.crm.api.dc import USDataCenter, INDataCenter
from zcrmsdk.src.com.zoho.crm.api.users import *


CRM_MODULE_NAME_MAP = {"Deals": "Requirement"}


def _initialize_crm():
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


def boot_session(bootinfo):
    _initialize_crm()


class ZohoCRM_Synchronizer:
    def __init__(self, *args, **kwargs):
        self.record_operations = RecordOperations()
        self.header_instance = HeaderMap()
        self.param_instance = ParameterMap()

    def get_all(self, module_name, last_modified=None):
        response = self.record_operations.get_records(
            module_name, self.param_instance, self.header_instance
        )

        response_object = response.get_object()
        if response_object is not None:
            if isinstance(response_object, object):
                for record in response_object.get_data():
                    doc = ZohoCRM_Record.sync_doc(module_name, record)

    # def sync_users(self):
    #     users_operations = UsersOperations()

    #     # Get instance of ParameterMap Class
    #     param_instance = ParameterMap()

    #     # Possible parameters for Get Users operation
    #     param_instance.add(GetUsersParam.page, 1)

    #     param_instance.add(GetUsersParam.per_page, 200)

    #     param_instance.add(GetUsersParam.type, "ActiveConfirmedUsers")

    #     # Get instance of ParameterMap Class
    #     header_instance = HeaderMap()

    #     # Possible headers for Get Users operation
    #     header_instance.add(
    #         GetUsersHeader.if_modified_since,
    #         datetime.fromisoformat("2019-07-07T10:00:00+05:30"),
    #     )

    #     # Call get_users method that takes ParameterMap instance and HeaderMap instance as parameters
    #     response = users_operations.get_users(param_instance, header_instance)

    #     if response is not None:

    #         # Get object from response
    #         response_object = response.get_object()

    #         if response_object is not None:

    #             if isinstance(response_object, object):
    #                 for record in response_object.get_data():

    #                     print(
    #                         response.get_key_values()
    #                     )  # Get the status code from response
