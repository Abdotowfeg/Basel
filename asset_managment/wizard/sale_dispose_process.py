# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SellDisposeProcess(models.TransientModel):
    _name = 'sell.dispose.wizard'
    _description = 'Sell/Dispose'

    action = fields.Selection([('sell', 'Sell'), ('dispose', 'Dispose')],
                              required=True, default="sell", string="Action")
    needed_account = fields.Selection([('gain', 'Gain Account'), ('loss', 'Loss Account'), ('non', 'Non')],
                                      default="non", string="Needed Account")
    account_move_id = fields.Many2one("account.move", string='Customer Invoice',
                                      domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')])
    loss_account = fields.Many2one("account.account", string='Loss Account')
    gain_account = fields.Many2one("account.account", string='Gain Account')

    @api.onchange('account_move_id', 'action')
    def show_needed_account(self):
        self.needed_account = "non"

        active_id = self.env.context.get('active_id')
        res_id = self.env[self.env.context.get('active_model')].search([('id', '=', active_id),
                                                                        ('state', '!=', 'depreciated')])
        invoice_line = self.account_move_id.invoice_line_ids.filtered(lambda l: l.asset_category_id == res_id.category_id)
        if self.account_move_id and not invoice_line:
            raise ValidationError("invalid input\n selected invoice has no product with this asset category")
        asset_invoice_line_amount = \
            sum(invoice_line.mapped('price_subtotal'))
        if self.account_move_id and asset_invoice_line_amount < res_id.value_residual:
        # if self.account_move_id and self.account_move_id.amount_total < res_id.value_residual:
            self.needed_account = "loss"
            self.gain_account = False

        if self.account_move_id and asset_invoice_line_amount >= res_id.value_residual:
        # if self.account_move_id and self.account_move_id.amount_total >= res_id.value_residual:
            self.needed_account = "gain"
            self.loss_account = False

        if self.action and self.action == 'dispose':
            self.needed_account = "loss"
            self.account_move_id = False
            self.gain_account = False

    def sell_dispose_action(self):
        if self.action == 'sell':
            self.sell_action()
        if self.action == 'dispose':
            self.dispose_action()

    def check_category_account(self):
        active_id = self.env.context.get('active_id')
        res_id = self.env[self.env.context.get('active_model')].search([('id', '=', active_id),
                                                                        ('state', '!=', 'depreciated')])
        if not res_id.category_id.account_asset_id:
            raise ValidationError(_("Transaction cant be completed asset,s category has asset account"))

        return active_id, res_id

    def sell_action(self):

        active_id, res_id = self.check_category_account()
        move_line_1 = {
            'account_id': self.account_move_id.invoice_line_ids[0].account_id.id,
            'debit': self.account_move_id.amount_residual,
            'credit': 0.0,
        }

        move_line_3 = {
            'account_id': res_id.category_id.account_asset_id.id,
            'debit': 0.0,
            'credit': res_id.value_residual,
        }

        lines_list = [(0, 0, move_line_1)]
        if self.needed_account == 'loss':
            move_line_2 = {
                'account_id': self.loss_account.id,
                'debit': abs(res_id.value_residual - self.account_move_id.amount_residual),
                'credit': 0.0,
            }
            lines_list.append((0, 0, move_line_2))
        lines_list.append((0, 0, move_line_3))
        if self.needed_account == 'gain':
            move_line_4 = {
                'account_id': self.gain_account.id,
                'debit': 0.0,
                'credit': abs(res_id.value_residual - self.account_move_id.amount_residual),
            }
            lines_list.append((0, 0, move_line_4))

        move_vals = {
            'ref': res_id.name,
            'date': res_id.date,
            'journal_id': res_id.category_id.journal_id.id,
            'line_ids': lines_list,
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        res_id.state = 'sold_disposed'

    def dispose_action(self):
        active_id, res_id = self.check_category_account()
        move_line_1 = {
            'account_id': self.loss_account.id,
            'debit': res_id.value_residual,
            'credit': 0.0,
        }

        move_line_2 = {
            'account_id': res_id.category_id.account_asset_id.id,
            'debit': 0.0,
            'credit': res_id.value_residual,
        }

        move_vals = {
            'ref': res_id.name,
            'date': res_id.date,
            'journal_id': res_id.category_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        res_id.state = 'sold_disposed'