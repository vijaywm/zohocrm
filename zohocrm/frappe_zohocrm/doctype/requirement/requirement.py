# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

from zcrmsdk.src.com.zoho.crm.api.record import Record
from zcrmsdk.src.com.zoho.crm.api.util import Choice
import json

API_FIELD_NAME = {}


class Requirement(Document):
    def __init__(self, *args, **kwargs):
        super(Requirement, self).__init__(*args, **kwargs)
        self.crm_instance_name = "Deals-Requirement"

    def autoname(self):
        self.crm_created_time = frappe.utils.get_datetime(self.crm_created_time)
        self.name = make_autoname(
            "RQ-%s-.#####" % (self.crm_created_time.strftime("%Y%m"))
        )

    def sync_from_crm_record(self, crm_record):
        self.flags.in_sync_from_crm = True
        self.update(
            {
                "deal_name": crm_record.get("Deal_Name"),
                "account_name": json.loads(crm_record.get("Account_Name", "{}")).get(
                    "name"
                ),
                "closing_date": crm_record.get("Closing_Date"),
            }
        )

        self.save()

    def on_update(self):
        frappe.get_doc("CRM Entity Sync", self.crm_instance_name).write_to_crm(
            self, API_FIELD_NAME
        )

        # # delink Requirement Item if not in child table
        # for d in frappe.db.get_all("Requirement Item", {"deal_name": self.name}):
        #     if [x for x in self.items if x.requirement_item == d.name]:
        #         d.update("deal_name", None)

        # # link all Requirement Items in child table to this deal
        # for d in self.items:
        #     frappe.db.set_value(
        #         "Requirement Item", d.requirement_item, "deal_name", self.name
        #     )
