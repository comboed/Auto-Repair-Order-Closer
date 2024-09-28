import helper
import json
import file
import api

class Bot:
    def __init__(self, session: api.API, filename):
        self.session = session
        self.filename = filename
        self.reader = file.read_csv("./data/" + filename)[1:]
        self.opcodes = json.load(open("./data/opcodes/opcodes.json"))

    def update_jobs(self, invoice_id, jobs):
        warranty = False
        for job in jobs.values():
            body = helper.create_update_body(job, self.opcodes)

            if not body:
                return False, False

            if body == "SKIP":
                continue

            if body == "WARRANTY":
                warranty = True
                continue

            if not self.session.update_job(invoice_id, job["jobId"], body):
                return None, False

        return True, warranty

    def process_invoice(self, invoice, index, repair_order):
        invoice_id = invoice["invoice_id"]

        if not self.session.reopen_invoice(invoice_id):
            print("Failed to reopen invoice (ranking #: {})".format(index + 1))
            self.session.send_invoice(invoice_id)
            return

        self.session.append_jobs(invoice)
        updated, warranty = self.update_jobs(invoice_id, invoice["jobs"])

        if updated is None:
            print("Invoice has already been closed")
            self.session.send_invoice(invoice_id)
            return

        if not updated:
            print("Failed to update all jobs (ranking #: {})".format(index + 1))
            self.session.send_invoice(invoice_id)
            return

        if not self.session.send_invoice(invoice_id):
            print("Failed to send invoice (ranking #: {})".format(index + 1))
            return

        if not warranty and self.session.close_repair_order(invoice_id):
            print("Successfully closed invoice (ranking #: {})".format(index + 1))
            file.write_entry(self.filename, repair_order, 1)

        elif warranty and self.session.close_internals(invoice_id):
            print("Successfully closed internals (ranking #: {})".format(index + 1))
            file.write_entry(self.filename, repair_order, "1(W)")

        else:
            print("Failed to close invoice (ranking #: {})".format(index + 1))

    def run(self, start_repair_order = None):
        for line in self.reader:
            if self.session.location in line[0].lower():
                repair_order = line[1]

                if start_repair_order is None or start_repair_order == repair_order:
                    start_repair_order = None

                    if line[2] not in []:
                        print("Repair order #: {}".format(repair_order))
                        invoices = self.session.lookup_repair_order(line[3])
                        if invoices:
                            for index, invoice in enumerate(invoices.values()):
                                print("Invoice ID: {}".format(invoice['invoice_id']))
                                self.process_invoice(invoice, index, repair_order)
                        else:
                            print("Repair order does not exist")
                        print("-------------------------------------------------------------------------------------------------- \n")
