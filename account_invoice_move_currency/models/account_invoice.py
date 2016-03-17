# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    move_currency_id = fields.Many2one(
        'res.currency',
        'Account Move Secondary Currency',
        help='If you set a currency here, then this invoice values will be '
        'also stored in the related Account Move',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    # TODO implement this
    # move_currency_rate = fields.Float(
    move_inverse_currency_rate = fields.Float(
        copy=False,
        digits=(16, 4),
        string='Account Move Secondary Currency Rate',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )

    @api.onchange('move_currency_id')
    def change_move_currency(self):
        if not self.move_currency_id:
            self.move_inverse_currency_rate = False
        self.move_inverse_currency_rate = self.env[
            'res.currency']._get_conversion_rate(
            self.move_currency_id, self.company_id.currency_id)

    @api.constrains('move_currency_id', 'currency_id')
    def check_move_currency(self):
        if self.move_currency_id and self.move_currency_id == self.currency_id:
            raise Warning(_(
                'Move Currency Can not be the same as Invoice Currency'))

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Odoo Hook method to be overridden in additional modules to verify
            and possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines
                (as for create())
            :return: the (possibly updated) final move_lines to create for this
                invoice
        """
        move_lines = super(
            AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        if self.move_currency_id:
            # company_currency = self.company_id.currency_id
            for a, b, line in move_lines:
                # move_currency = self.move_currency_id.with_context(
                #     date=self.date_invoice or fields.Date.context_today(
                #     self))
                if not self.move_inverse_currency_rate:
                    raise Warning(_(
                        'If Move Secondary Currency Select you must set rate'))
                if line['debit']:
                    amount = line['debit']
                    sign = 1.0
                else:
                    amount = line['credit']
                    sign = -1.0
                line['currency_id'] = self.move_currency_id.id
                line['amount_currency'] = sign * self.move_currency_id.round(
                    amount / self.move_inverse_currency_rate)
                # line['amount_currency'] = sign * company_currency.compute(
                #     amount, move_currency)
        return move_lines