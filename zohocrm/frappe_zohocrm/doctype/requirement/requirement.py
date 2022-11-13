# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

from zcrmsdk.src.com.zoho.crm.api.record import Record
from zcrmsdk.src.com.zoho.crm.api.util import Choice
import json


class Requirement(Document):
    def autoname(self):
        self.name = make_autoname(
            "RQ-%s-.#####" % (self.crm_created_time.strftime("%Y%m"))
        )

    def sync_from_crm_record(self, crm_record):
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
