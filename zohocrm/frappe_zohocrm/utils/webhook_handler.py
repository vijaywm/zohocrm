# Copyright (c) 2022, Biztech and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist(allow_guest=True)
def update_record(**args):
    print(args)
    if args.get("module_name") and args.get("id"):
        sync = frappe.db.get_value(
            "CRM Entity Sync", filters={"crm_entity_name": args.get("module_name")}
        )
        if sync:
            frappe.set_user("Administrator")
            sync = frappe.get_doc("CRM Entity Sync", sync).run_sync(
                entity_id=args.get("id")
            )
