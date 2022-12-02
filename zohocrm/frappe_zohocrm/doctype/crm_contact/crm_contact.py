# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

API_FIELD_NAME = {}


class CRMContact(Document):
    def __init__(self, *args, **kwargs):
        super(CRMContact, self).__init__(*args, **kwargs)
        self.crm_instance_name = "Contacts-CRM Contact"

    def sync_from_crm_record(self, crm_record):
        self.flags.in_sync_from_crm = True
        self.save()

    def on_update(self):
        frappe.get_doc("CRM Entity Sync", self.crm_instance_name).write_to_crm(
            self, API_FIELD_NAME
        )

    def after_insert(self):
        """create new record in crm"""
        if not self.crm_id:
            frappe.get_doc("CRM Entity Sync", self.crm_instance_name).create_in_crm(
                self, API_FIELD_NAME
            )
