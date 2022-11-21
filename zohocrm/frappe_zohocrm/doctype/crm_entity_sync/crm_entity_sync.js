// Copyright (c) 2022, Biztech and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Entity Sync", {
  // refresh: function(frm) {

  // }

  run_sync: function (frm) {
    frappe.msgprint(
      `Enqueuing syncing for ${frm.doc.crm_entity_name}. Please check after a few minutes.`
    );
    frappe.call({
      method: "run_sync",
      doc: frm.doc,
      callback: function (r) {
        frappe.show_alert(`Syncing for ${frm.doc.crm_entity_name} finished.`);
      },
    });
  },
});
