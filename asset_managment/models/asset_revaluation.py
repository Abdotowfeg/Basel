# -*- coding: utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAssetRevaluation(models.Model):
    _name = 'account.asset.revaluation'
    _description = 'Asset Revaluation'

    asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True)
    revaluation_date = fields.Datetime('Revaluation Date', required=True, default=datetime.today())
    revaluation_type = fields.Selection([('upward', 'Upward'),
                                         ('downward', 'Downward')], 'Revaluation type', required=True,)

    gross_cost = fields.Float(related='asset_id.value', string='Gross Value', readonly=True)
    depreciated_cost = fields.Float(compute='set_depreciated_cost', string='Depreciated Cost',
                                    readonly=True)
    past_year_dep = fields.Float(compute='set_depreciated_cost')
    current_value = fields.Float(string="Current Value", compute="set_current_value")
    revalued_value = fields.Float(string="Revalued Value", required=True)
    state = fields.Selection([('draft', 'draft'), ('confirm', 'Confirm')], default="draft",
                             string="State")

    @api.constrains('revaluation_date')
    def check_revaluation_date(self):
        for rec in self:
            if rec.revaluation_date.date() < rec.asset_id.date:
                raise ValidationError(_("Invalid Input for revaluation date\n must be greater than asset date"))

    @api.constrains('revalued_value')
    def check_revalued_value(self):
        for rec in self:
            if rec.revalued_value <= rec.current_value and rec.revaluation_type == "upward":
                raise ValidationError(_("Invalid Input for Revalued value\n must be greater than Current value when"
                                        " Revaluation type is up word"))
            if rec.revalued_value >= rec.current_value and rec.revaluation_type == "downward":
                raise ValidationError(_("Invalid Input for Revalued value\n must be less than Current value"
                                        " Revaluation type is down word"))

    @api.depends('asset_id', 'revaluation_date')
    def set_depreciated_cost(self):

        for rec in self:
            line = rec.asset_id.depreciation_line_ids.filtered(lambda d: d.depreciation_date < rec.revaluation_date.date())

            if not line:
                rec.depreciated_cost = rec.past_year_dep = 0
            if len(line) == 1:
                rec.depreciated_cost = line[-1].depreciated_value
                rec.past_year_dep = 0
            if len(line) > 1:
                rec.depreciated_cost = line[-1].depreciated_value
                rec.past_year_dep = line[-2].depreciated_value

    @api.depends('gross_cost', 'depreciated_cost')
    def set_current_value(self):
        for rec in self:
            rec.current_value = rec.gross_cost - rec.depreciated_cost - rec.asset_id.salvage_value

    def set_to_confirm(self):
        for rec in self:
            rec.asset_id.compute_depreciation_board()
            if rec.revaluation_type == "upward":
                rec.create_upward_move()
            if rec.revaluation_type == "downward":
                rec.create_downward_move()
            rec.state = 'confirm'

    def create_upward_move(self):
        move_line_1 = {
            'account_id': self.asset_id.account_depreciation_id.id,
            'debit': abs(self.asset_id.value - self.revalued_value),
            'credit': 0.0
        }
        move_line_2 = {
            'account_id': self.asset_id.account_revaluation_id.id,
            'debit': 0.0,
            'credit': abs(self.asset_id.value - self.revalued_value),

        }
        move_vals = {
            'ref': self.asset_id.name,
            'date': self.revaluation_date,
            'journal_id': self.asset_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()

    def create_downward_move(self):
        move_line_1 = {
            'account_id': self.asset_id.account_depreciation_id.id,
            'debit': 0.0,
            'credit': abs(self.asset_id.value - self.revalued_value)
        }
        move_line_2 = {
            'account_id': self.asset_id.account_revaluation_id.id,
            'debit': abs(self.asset_id.value - self.revalued_value),
            'credit': 0.0,
        }
        move_vals = {
            'ref': self.asset_id.name,
            'date': self.revaluation_date,
            'journal_id': self.asset_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        if not self.asset_id.account_depreciation_id or not self.asset_id.account_revaluation_id \
            or not self.asset_id.journal_id:
            raise ValidationError(_("Please make sure that all asset accounting information set properly"))
        move = self.env['account.move'].create(move_vals)
        move.action_post()