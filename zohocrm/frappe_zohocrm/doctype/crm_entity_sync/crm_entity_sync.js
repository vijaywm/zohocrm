// Copyright (c) 2022, Biztech and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Entity Sync", {
  // refresh: function(frm) {

  // }

  run_sync: function (frm) {
    console.log("hit");
    frappe.call({
      method: "run_sync",
      doc: cur_frm.doc,
      callback: function (r) {},
    });
  },
});
