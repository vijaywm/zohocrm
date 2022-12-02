# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from zohocrm.frappe_zohocrm.doctype.crm_entity_sync.crm_entity_sync import get_by_id

API_FIELD_NAME = {"requirement_item_name": "Name"}


class RequirementItem(Document):
    def __init__(self, *args, **kwargs):
        super(RequirementItem, self).__init__(*args, **kwargs)
        self.crm_instance_name = "Requirement Items-Requirement Item"

    def sync_from_crm_record(self, crm_record):
        self.flags.in_sync_from_crm = True
        for field in API_FIELD_NAME:
            self.update(
                {
                    field: crm_record.get(API_FIELD_NAME[field])
                    # "requirement_item_name": crm_record.get("Name"),
                }
            )
        self.save()

        if crm_record.get("Requirement"):
            r = json.loads(crm_record.get("Requirement"))
            requirement = get_by_id("Requirement", r.get("id"))

            li = [
                d
                for d in requirement.requirement_line_items
                if d.requirement_item == self.name
            ]
            if not li:
                li = [
                    requirement.append(
                        "requirement_line_items",
                        {
                            "requirement_item": self.name,
                        },
                    )
                ]
            for d in li:
                d.update(
                    {
                        "requirement_item_name": self.requirement_item_name,
                    }
                )
            requirement.save()

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
