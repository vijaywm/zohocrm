# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from zohocrm.frappe_zohocrm.doctype.crm_entity.crm_entity import write_to_crm


class CRMContact(Document):
    def sync_from_crm_record(self, crm_record):
        pass
        self.save()

    def on_update(self):
        write_to_crm(self)
