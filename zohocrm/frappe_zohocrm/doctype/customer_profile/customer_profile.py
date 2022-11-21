# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import json
from zohocrm.frappe_zohocrm.doctype.crm_entity.crm_entity import write_to_crm


class CustomerProfile(Document):
    def validate(self):
        pass

    def sync_from_crm_record(self, crm_record):
        self.flags.in_sync_from_crm = True
        self.update({"account_name": crm_record.get("Account_Name")})
        self.save()

    def on_update(self):
        if not self.flags.in_sync_from_crm:
            write_to_crm(self)
