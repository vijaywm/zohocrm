# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMContact(Document):
    def sync_from_crm_record(self, crm_record):
        pass
        # self.update({"account_name": crm_record.get("Account_Name")})

        self.save()
