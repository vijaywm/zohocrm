# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class ZCRMNote(Document):
    def sync_from_crm_record(self, crm_record):
        self.update(
            {"parent_id": json.loads(crm_record.get("Parent_Id", "{}")).get("id")}
        )

        self.save()
