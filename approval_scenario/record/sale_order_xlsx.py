from odoo import models


class SaleOrderXlsx(models.AbstractModel):
    _name = 'report.sale.report_sale_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('patient')
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcentre', 'bold': True})
        format2 = workbook.add_format({'font_size': 10, 'align': 'vcentre', 'bold': False})
        format3 = workbook.add_format({'font_size': 15, 'align': 'vcentre', 'bold': False})
        sheet.write(2, 0, 'invoicing address', format1)
        sheet.write(3, 1, lines.partner_invoice_id.name, format2)
        sheet.write(5, 0, 'shipping address', format1)
        sheet.write(6, 1, lines.partner_shipping_id.name, format2)
        sheet.write(10, 0, 'Order#', format3)
        sheet.write(10, 1, lines.name, format3)
        sheet.write(11, 0, 'Order Date', format1)
        sheet.write(11, 2, 'Sales Person', format1)
        sheet.write(11, 4, 'Approval Limit', format1)
        sheet.write(11, 6, 'Manager', format1)
        sheet.write(12, 0, lines.date_order, format2)
        sheet.write(12, 2, lines.create_uid.name, format2)
        sheet.write(12, 4, lines.limit, format2)
        sheet.write(12, 6, lines.manager_id.name, format2)
        sheet.write(14, 0, 'Description', format1)
        sheet.write(14, 2, 'Quantity', format1)
        sheet.write(14, 3, 'Unit Price', format1)
        sheet.write(14, 4, 'Taxes', format1)
        sheet.write(14, 5, 'Amount', format1)
        data = self.env['sale.order.line'].search([('order_id', 'in', lines.ids)])
        row = 15
        for rec in data:
            if rec:
                sheet.write(row, 0, rec.product_id.name, format2)
                sheet.write(row, 2, rec.product_uom_qty, format2)
                sheet.write(row, 3, rec.price_unit, format2)
                sheet.write(row, 4, rec.tax_id.name, format2)
                sheet.write(row, 5, rec.price_subtotal, format2)
                row += 1

        row += 1
        sheet.write(row, 3, 'Total', format1)
        sheet.write(row, 5, lines.amount_total, format2)
        sheet.write(row+2, 0, 'Payment Terms:', format1)
        sheet.write(row+2, 2, lines.payment_term_id.name, format2)








