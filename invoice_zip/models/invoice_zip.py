import io
import zipfile
import base64
import re
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class InvoiceZipDownload(models.TransientModel):
    _name = 'invoice.zip.download'
    _description = 'Generate ZIP of Invoices'

    zip_file = fields.Binary('ZIP File')
    filename = fields.Char('Filename')

    @api.model
    def generate_zip(self, invoice_ids):
        from odoo.tools.translate import _ 

        # Filter customer invoices
        invoices = self.env['account.move'].browse(invoice_ids).filtered(lambda m: m.move_type == 'out_invoice')
        if not invoices:
            raise UserError(_('No customer invoices selected.'))

        report = self.env['ir.actions.report'].search([('report_name', '=', 'account.report_invoice')], limit=1)
        if not report:
            raise UserError(_('Invoice report not found. Please ensure the account module is installed.'))

        if len(invoices) > 100:
            raise UserError(_('Too many invoices selected. Please select up to 100 invoices.'))

        zip_buffer = io.BytesIO()
        failed_invoices = []

        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            for invoice in invoices:
                try:
                    _logger.info(f"Generating PDF for invoice: {invoice.name} ({invoice.id})")
                    pdf_content, _format = report._render_qweb_pdf('account.report_invoice', res_ids=[invoice.id])
                    if not pdf_content:
                        raise Exception("Empty PDF content returned")
                    filename = re.sub(r'[^\w\-_\. ]', '_', invoice.name or f'invoice_{invoice.id}') + f'_{invoice.id}.pdf'
                    zip_file.writestr(filename, pdf_content)
                except Exception as e:
                    _logger.error(f"PDF generation failed for Invoice {invoice.name or invoice.id}: {str(e)}")
                    failed_invoices.append(invoice.name or f'ID_{invoice.id}')


        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

        if not zip_data or (len(failed_invoices) == len(invoices)):
            msg = _('No PDFs were generated.')
            if failed_invoices:
                msg += _(' Failed invoices: %s') % ', '.join(failed_invoices)
            raise UserError(msg)

        record = self.create({
            'zip_file': base64.b64encode(zip_data),
            'filename': 'invoices.zip',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{record._name}/{record.id}/zip_file/{record.filename}?download=true",
            'target': 'self',
        }