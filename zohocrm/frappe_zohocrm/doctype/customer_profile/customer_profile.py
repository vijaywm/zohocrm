# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import json


API_FIELD_NAME = {}


class CustomerProfile(Document):
    def __init__(self, *args, **kwargs):
        super(CustomerProfile, self).__init__(*args, **kwargs)
        self.crm_instance_name = "Accounts-Customer Profile"

    def sync_from_crm_record(self, crm_record):
        self.flags.in_sync_from_crm = True
        self.update({"account_name": crm_record.get("Account_Name")})
        self.save()

    def on_update(self):
        frappe.get_doc("CRM Entity Sync", self.crm_instance_name).write_to_crm(
            self, API_FIELD_NAME
        )

    # def after_insert(self):
    #     """create new record in crm"""
    #     if not self.crm_id:
    #         frappe.get_doc("CRM Entity Sync", self.crm_instance_name).create_in_crm(
    #             self, API_FIELD_NAME
    #         )
