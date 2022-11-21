# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from zohocrm.frappe_zohocrm.doctype.crm_entity_sync.crm_entity_sync import CRMEntitySync

FIELDS_TO_SKIP = ["owner"]


class CRMEntity(Document):
    def validate(self):
        pass

    def on_update(self):
        """Create/Update frappe doc connected to this CRM Record"""
        doc = frappe.db.get_value(self.frappe_doctype, filters={"crm_id": self.name})
        if doc:
            doc = frappe.get_doc(self.frappe_doctype, doc)
        else:
            doc = frappe.get_doc({"doctype": self.frappe_doctype})
            doc.update(
                {
                    "crm_id": self.name,
                    "crm_created_time": self.crm_created_time,
                    "crm_created_by": self.crm_created_by,
                }
            )

        # sync common fields
        doc.update(
            {
                "crm_owner": self.crm_owner,
                "crm_modified_time": self.crm_modified_time,
                "crm_modified_by": self.crm_modified_by,
            }
        )

        record = json.loads(self.data_json)

        # sync with meta fields
        for k, v in record.items():
            key = frappe.scrub(k).lower()
            if (
                not key in FIELDS_TO_SKIP
                and key in doc.meta.get_fieldnames_with_value()
            ):
                doc.set(key, v)

        # handle link fields: get name from id
        for df in doc.meta.get_link_fields():
            link_value = doc.get(df.fieldname)
            if (
                link_value
                and isinstance(link_value, str)
                and link_value.startswith("{")
            ):
                try:
                    link_name = frappe.get_value(
                        df.options,
                        filters={"crm_id": json.loads(link_value).get("id")},
                    )
                    if not link_name:
                        frappe.log_error(
                            "Link does not exist. {}: {}".format(df.options, df.value)
                        )
                    doc.set(df.fieldname, link_name)
                except:
                    frappe.log_error(
                        "Link field parse error. {}:{}".format(df.options, link_value)
                    )

        try:
            doc.flags.ignore_links = True
            doc.sync_from_crm_record(record)
        except Exception:
            frappe.log_error(
                "Error syncing {} to {}. {}".format(
                    self.crm_module, self.frappe_doctype, self.name
                )
            )


def write_to_crm(doc):
    crm_instance = frappe.get_doc("CRM Entity Sync", "Accounts-Customer Profile")
    crm_instance.write_to_crm(doc)
