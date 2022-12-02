# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe


def after_insert_comment(doc, method):
    print(doc.as_dict(), method)
    if doc.comment_type == "Deleted":
        return

    for d in frappe.db.get_all(
        "CRM Entity Sync",
        {"frappe_doctype": doc.reference_doctype},
        limit_page_length=1,
    ):
        frappe.get_doc("CRM Entity Sync", d.name).add_note(doc)
