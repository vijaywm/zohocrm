# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cstr

from frappe.model.document import Document
from zcrmsdk.src.com.zoho.crm.api.record import (
    Record as ZCRMRecord,
    RecordOperations,
    GetRecordsParam,
)
from zcrmsdk.src.com.zoho.crm.api import HeaderMap, ParameterMap
from zcrmsdk.src.com.zoho.crm.api.record import Record
from zcrmsdk.src.com.zoho.crm.api.util import Choice

CRM_MODULE_NAME_MAP = {"Deals": "Requirement", "Accounts": "User"}


def get_lookup_value(crm_record, lookup, field):
    return crm_record.get_key_value(lookup).get_key_value(field)


def get_link_name(doctype, field, value):
    name = frappe.db.sql(
        """select name from `tab{doctype}` 
    where {field} = %s limit 1""".format(
            field=field, doctype=doctype
        ),
        (value,),
        pluck="name",
    )
    return name and name[0]


class ZohoCRM_Record(Document):
    def set_crm_standard_fields(self, crm_record: ZCRMRecord):
        self.set("zcrm_entity_id", cstr(crm_record.get_id()))
        self.update({"created_by": crm_record.get_created_by().get_key_value("email")})
        # crm_record.get_tag()

    def set_modified(self, crm_record):
        creation = get_utc(crm_record.get_created_time())
        frappe.db.sql(
            "update `tab{}` set creation = %s where name = %s".format(self.doctype),
            (creation, self.name),
        )
        modified = get_utc(crm_record.get_modified_time())
        frappe.db.sql(
            "update `tab{}` set modified = %s where name = %s".format(self.doctype),
            (modified, self.name),
        )

    def sync_from_crm_record(self, crm_record):
        pass
        self.set_crm_standard_fields(crm_record)

        for df in self.meta.fields:
            crm_name = frappe.unscrub(df.fieldname).replace(" ", "_")
            value = crm_record.get_key_value(crm_name)
            if not value:
                continue
            if not df.fieldtype == "Link":
                if isinstance(value, Choice):
                    self.update({df.fieldname: value.get_value()})
                else:
                    self.update({df.fieldname: value})
            elif isinstance(value, Record):
                pass

    @staticmethod
    def get_by_id(crm_module_name, crm_record):
        doctype = CRM_MODULE_NAME_MAP.get(crm_module_name)
        filters = {"zcrm_entity_id": cstr(crm_record.get_id())}
        doc = frappe.db.exists(doctype, filters)
        if doc:
            return frappe.get_doc(doctype, doc)

    @staticmethod
    def sync_doc(crm_module_name: str, crm_record: ZCRMRecord):

        print("Syncing:")
        print(crm_record.get_key_values())

        return

        doc = ZohoCRM_Record.get_by_id(crm_module_name, crm_record)
        if not doc:
            doc = frappe.new_doc(CRM_MODULE_NAME_MAP.get(crm_module_name))
        doc.sync_from_crm_record(crm_record)
        doc.save()
        doc.set_modified(crm_record)


def get_utc(dt):
    out = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    return out
