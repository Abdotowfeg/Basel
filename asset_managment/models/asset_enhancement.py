# -*- coding: utf-8 -*-

from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAssetEnhancement(models.Model):
    _name = 'account.asset.enhancement'
    _description = 'Asset Enhancement'

    enhancement_name = fields.Char(compute="get_enhancement_name")
    asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True)
    enhancement_date = fields.Datetime('Enhancement Date', required=True, default=datetime.today())
    enhancement_description = fields.Char(string='Enhancement Description')

    gross_cost = fields.Float(related='asset_id.value', string='Gross Value', readonly=True)
    depreciated_cost = fields.Float(compute='set_depreciated_cost', string='Depreciated Cost',
                                    readonly=True)
    past_year_dep = fields.Float(compute='set_depreciated_cost')
    current_value = fields.Float(string="Current Value", compute="set_current_value")
    revalued_value = fields.Float(string="Revalued Value", required=True)
    move_id = fields.Many2one('account.move', string="Entry", readonly=True)

    def get_enhancement_name(self):
        for rec in self:
            rec.enhancement_name = str(rec.enhancement_date)+"/"+(rec.asset_id.name)

    @api.constrains('revaluation_date')
    def check_enhancement_date(self):
        for rec in self:
            if rec.enhancement_date.date() < rec.asset_id.date:
                raise ValidationError(_("Invalid Input for revaluation date\n must be greater than asset date"))

    @api.constrains('revalued_value')
    def check_revalued_value(self):
        for rec in self:
            if rec.revalued_value <= rec.current_value:
                raise ValidationError(_("Invalid Input for Revalued value\n must be greater than Current value"))

    @api.depends('asset_id', 'enhancement_date')
    def set_depreciated_cost(self):
        for rec in self:

            line = rec.asset_id.depreciation_line_ids.filtered(
                lambda d: d.depreciation_date < rec.enhancement_date.date())

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

    def create_move(self):
        move_line_1 = {
            'account_id': self.asset_id.account_asset_id.id,
            'debit': abs(self.asset_id.value - self.revalued_value),
            'credit': 0.0
        }
        move_line_2 = {
            'account_id': self.asset_id.account_enhancement_id.id,
            'debit': 0.0,
            'credit': abs(self.asset_id.value - self.revalued_value),

        }
        move_vals = {
            'ref': self.enhancement_name,
            'date': self.enhancement_date,
            'journal_id': self.asset_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        return self.env['account.move'].create(move_vals)

    @api.model
    def create(self, vals):
        res = super(AccountAssetEnhancement, self).create(vals)
        res.move_id = res.create_move()
        res.asset_id.compute_depreciation_board()
        return res

    def unlink(self):
        for rec in self:
            move_id = self.env['account.move'].search([('id', '=', rec.move_id.id), ('ref', '=', rec.enhancement_name)])
            move_id.unlink()
        return super(AccountAssetEnhancement, self).unlink()

    def write(self, vals):
        res = super(AccountAssetEnhancement, self).write(vals)
        for rec in self:
            rec.asset_id.compute_depreciation_board()
        return res

    def open_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.move_id.id), ('ref', '=', self.enhancement_name)],
        }