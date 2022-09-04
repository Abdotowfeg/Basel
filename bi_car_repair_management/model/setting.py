# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class res_company(models.Model):
	_inherit = 'res.company'

	consume_parts = fields.Boolean(string="Consume Parts from Stock")
	location_id = fields.Many2one('stock.location',string="Inventory Location")
	location_dest_id = fields.Many2one('stock.location',string="Consumed Part Location")


class ConsumePartsSetting(models.TransientModel):

	_inherit = 'res.config.settings'

	consume_parts = fields.Boolean(string="Consume Parts from Stock",related='company_id.consume_parts',readonly=False)

	location_id = fields.Many2one('stock.location',string="Inventory Location",related='company_id.location_id',readonly=False)

	location_dest_id = fields.Many2one('stock.location',string="Consumed Part Location",related='company_id.location_dest_id',readonly=False)