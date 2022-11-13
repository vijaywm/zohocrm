# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from zohocrm.frappe_zohocrm.doctype.crm_entity_sync.crm_entity_sync import get_by_id


class RequirementItem(Document):
    def sync_from_crm_record(self, crm_record):
        self.update(
            {
                "requirement_item_name": crm_record.get("Name"),
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
