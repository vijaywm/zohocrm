# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist(allow_guest=True)
def update_record(**args):
    print(args)
    if args.get("module_name") and args.get("id"):
        frappe.set_user("Administrator")
        for sync in frappe.db.get_all(
            "CRM Entity Sync", filters={"crm_entity_name": args.get("module_name")}
        ):
            frappe.get_doc("CRM Entity Sync", sync.name).run_sync(
                entity_id=args.get("id")
            )
