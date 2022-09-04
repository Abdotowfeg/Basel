# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, SUPERUSER_ID,  _

class CarRepairTeams(models.Model):
	_name = 'car.repair.team'
	
	name = fields.Char(string="Name")
	leader_id = fields.Many2one('res.users',string='Leader')
	is_default_team = fields.Boolean(string='Is Default Team',default=False)
	team_member_ids = fields.Many2many('res.users','res_user_rel1','car_team_id','user_id',string="Team Member")
	
class CarServices(models.Model):
	_name = 'car.services'    
	
	name = fields.Char(string='Car Service')
	
class CarServiceType(models.Model):
	_name = 'car.service.type'    
	
	name = fields.Char(string='Name')
	code = fields.Char(string='Code')
	product_id = fields.Many2one('product.product',string="Product")
	cost = fields.Float(string="Cost", related="product_id.lst_price" ,readonly=False)
	
class ProductProduct(models.Model):
	_inherit = 'product.product'    
	
	is_car_parts = fields.Boolean(string='Car Parts',default=False)  
	
class CarRepair(models.Model):      
	_name = 'car.repair'
	_description = 'Car Repair'
	_inherit = ['mail.thread','portal.mixin']
	_rec_name = 'sequence'
	
	name = fields.Char(string='Name', required=True)
	sequence = fields.Char(string='Sequence', readonly=True)
	technician_id = fields.Many2one('res.users', string='Technician')
	partner_id = fields.Many2one('res.partner', string='Customer')
	client_email = fields.Char(string='Email')
	client_phone = fields.Char(string='Phone')
	company_id = fields.Many2one('res.company', string='Company')
	project_id = fields.Many2one('project.project', string='Project')
	car_repair_team_id = fields.Many2one('car.repair.team',string='Car Repair Team')
	team_leader_id = fields.Many2one('res.users', string='Team Leader')
	priority = fields.Selection([('0','False'),('1','Low'),('2','Normal'),('3','High')],string='Priority')
	repair_request_date = fields.Datetime(string='Repair Request Date',default=datetime.now())
	close_date = fields.Datetime(string='Close Date',readonly=True)
	is_repaired = fields.Boolean(string='Is Repaired',default=False)
	repairing_duration = fields.Float(string='Repairing Duration',default=0.0)
	is_warranty = fields.Boolean(string='Warranty',default=False)
	fleet_id = fields.Many2one('fleet.vehicle',onchange='onchange_fleet_id',string='Fleet')
	brand = fields.Many2one('fleet.vehicle.model.brand',string='Brand',related="fleet_id.model_id.brand_id",readonly=False)
	model = fields.Many2one('fleet.vehicle.model',string='Model',related="fleet_id.model_id",readonly=False)
	license_plate = fields.Char(string='License Plate',related="fleet_id.license_plate",readonly=False)
	chassis_number = fields.Char(string='Chassis Number',related="fleet_id.vin_sn",readonly=False)
	seats = fields.Integer(string='Seats',related="fleet_id.seats",readonly=False)
	doors = fields.Integer(string='Doors',related="fleet_id.doors",readonly=False)
	color = fields.Char(string='Color',related="fleet_id.color",readonly=False)
	year = fields.Char(string='Model Year',related="fleet_id.model_year",readonly=False)
	damage = fields.Text(string='Damage')
	accompanying_item = fields.Text(string='Accompanying Items')
	description = fields.Text(string='Description')
	stage = fields.Selection([('new','New'),('assigned','Assigned'),('work_in_progress','Work In Progress'),('needs_reply','Needs Reply'),('reopen','Reopened'),('solution_suggested','Solution Suggested'),('closed','Closed')],string="Stage" ,default="new", index=True)#,('need_more_info','Needs More Info')
	is_car_closed = fields.Boolean(string="Is Car Closed")
	timesheet_ids = fields.One2many('account.analytic.line','car_repair_timesheet_id',string="Timesheet")
	car_services_id = fields.Many2one('car.services',string="Car Services")
	car_service_type_id = fields.Many2many('car.service.type',string="Repair Type")
	problem = fields.Text(string="Problem")
	car_consume_ids = fields.One2many('car.repair.estimate','product_consume_id',string="Product Consume Parts")
	car_diagnosys_count = fields.Integer('Car Diagnosis', compute='_get_car_diagnosys_count')
	car_workorder_count = fields.Integer('Car Work Order', compute='_get_car_workorder_count')
	images_ids = fields.One2many('ir.attachment','car_repair_id','Images')
	customer_rating = fields.Selection([('0','False'),('1','Poor'), ('2','Average'), ('3','Good'),('4','Excellent')], 'Customer Rating')
	comment = fields.Text(string="Comment")
	attachment_count  =  fields.Integer('Attachments', compute='_get_attachment_count')
	
	
	@api.onchange('partner_id')
	def onchange_partner_id(self):
		res = {}
		if not self.partner_id:
			return res
		self.client_email = self.partner_id.email
		self.client_phone = self.partner_id.phone
		
	
	def _get_car_diagnosys_count(self):
		for diagnosys in self:
			diagnosys_ids = self.env['car.diagnosys'].search([('car_repair_id','=',diagnosys.id)])
			diagnosys.car_diagnosys_count = len(diagnosys_ids)
			
	
	def car_diagnosys_button(self):
		self.ensure_one()
		return {
			'name': 'Car Diagnosis',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'car.diagnosys',
			'domain': [('car_repair_id', '=', self.id)],
		}
		
	
	def _get_car_workorder_count(self):
		for workorder in self:
			workorder_ids = self.env['car.workorder'].search([('car_repair_id','=',workorder.id)])
			workorder.car_workorder_count = len(workorder_ids)

	
	def car_workorder_button(self):
		self.ensure_one()
		return {
			'name': 'Car Workorder',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'car.workorder',
			'domain': [('car_repair_id', '=', self.id)],
		}        
		
	@api.model
	def create(self, vals):
		vals['sequence'] = self.env['ir.sequence'].next_by_code('car.repair.seq') or 'RO-000'
		result = super(CarRepair, self).create(vals)
		return result

	
	def set_to_close(self):
		res = self.write({'stage':'closed','is_car_closed':True,'close_date':datetime.now()})
		super_user = self.env['res.users'].browse(SUPERUSER_ID)
		if not self.partner_id.email:
			raise UserError(_('%s customer has no email id please enter email address')
					% (self.partner_id.name)) 
		else:
			car_repair_manager_id = self.env['ir.model.data'].sudo().\
			get_object_reference('bi_car_repair_management','group_car_repair_manager')[1]
			group_manager = self.env['res.groups'].sudo().browse(car_repair_manager_id)
			if group_manager.users:
				for group_manager in group_manager.users:
					template_id = self.env['ir.model.data'].get_object_reference(
												  'bi_car_repair_management',
												  'email_template_car_repair')[1]

					email_template_obj = self.env['mail.template'].browse(template_id)
					if template_id:
						values = email_template_obj.generate_email(self.id, fields=['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
						values['email_from'] = group_manager.partner_id.email
						values['email_to'] = self.partner_id.email
						values['author_id'] = group_manager.partner_id.id
						mail_mail_obj = self.env['mail.mail']
						
						msg_id = mail_mail_obj.sudo().create(values)
						
						if msg_id:
							mail_mail_obj.send([msg_id])
		return res 
		

	def create_car_diagnosys(self):
		diagnosis_obj = self.env['car.diagnosys']
		list_of_timesheet = []
		list_of_consumed_product = []
		car_repair_obj = self.env['car.repair'].browse(self.ids[0])
		
		for timesheet in car_repair_obj.timesheet_ids:
			list_of_timesheet.append(timesheet.id) 
			
		for car_consume in car_repair_obj.car_consume_ids:
			list_of_consumed_product.append(car_consume.id)             

		diagnosys_name = car_repair_obj.name + " (" + car_repair_obj.sequence + ")"
		vals = {
				'priority' : car_repair_obj.priority,
				'name' : diagnosys_name,
				'project_id' : car_repair_obj.project_id.id,
				'assigned_to' : car_repair_obj.technician_id.id,
				'description' : car_repair_obj.accompanying_item,
				'car_repair_id' : car_repair_obj.id,
				'timesheet_ids' : [(6,0,list_of_timesheet)],
				'car_repair_estimation_ids' : [(6,0,list_of_consumed_product)],
				'partner_id' : car_repair_obj.partner_id.id,
				'initially_planned_hour' : car_repair_obj.repairing_duration,
				'fleet_id' : car_repair_obj.fleet_id.id,
		}
		diagnosys_id = self.env['car.diagnosys'].create(vals)
		return True 

	
	def create_car_workorder(self):
		workorder_obj = self.env['car.workorder']
		list_of_timesheet = []
		list_of_consumed_product = []
		car_repair_obj = self.env['car.repair'].browse(self.ids[0])
		
		for timesheet in car_repair_obj.timesheet_ids:
			list_of_timesheet.append(timesheet.id) 
			
		workorder_name = car_repair_obj.name + " (" + car_repair_obj.sequence + ")"
		vals = {
				'priority' : car_repair_obj.priority,
				'name' : workorder_name,
				'project_id' : car_repair_obj.project_id.id,
				'assigned_to' : car_repair_obj.technician_id.id,
				'description' : car_repair_obj.accompanying_item,
				'car_repair_id' : car_repair_obj.id,
				'workorder_timesheet_ids' : [(6,0,list_of_timesheet)],
				'partner_id' : car_repair_obj.partner_id.id,
				'initially_planned_hour' : car_repair_obj.repairing_duration,
				'fleet_id' : car_repair_obj.fleet_id.id,
		}
		workorder_id = self.env['car.workorder'].create(vals)
		return True

	
	def _get_attachment_count(self):
		for car in self:
			attachment_ids = self.env['ir.attachment'].search([('car_repair_id','=',car.id)])
			car.attachment_count = len(attachment_ids)
		
	
	def attachment_on_car_repair_button(self):
		self.ensure_one()
		return {
			'name': 'Attachment.Details',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'ir.attachment',
			'domain': [('car_repair_id', '=', self.id)],
		}

class CarDiagnosys(models.Model):      
	_name = 'car.diagnosys'
	
	name = fields.Char(string="Name")
	project_id = fields.Many2one('project.project',string="Project")
	assigned_to = fields.Many2one('res.users',string="Assigned To")
	initially_planned_hour = fields.Float(string="Initially Planned Hour",default=0.0)
	deadline_date = fields.Datetime(string="Deadline")
	tag_ids = fields.Many2one('project.tags',string="Tags")
	description = fields.Text(string="Description")
	timesheet_ids = fields.One2many('account.analytic.line','timesheet_id',String="Timesheet")
	car_repair_estimation_ids = fields.One2many('car.repair.estimate','diagnosys_id',string="Car Repair Estimation")
	hours_spent = fields.Float(compute='_get_total_hours',string="Hours Spent",defalut=0.0)
	remaining_hours = fields.Float(compute='_get_total_hours',string="Remaining Hours",defalut=0.0)
	partner_id = fields.Many2one('res.partner',string="Customer")
	car_repair_id = fields.Many2one('car.repair',string="Car Repair")
	type_id = fields.Many2one('car.service.type',string="Type")
	quotation_count = fields.Float(compute='_get_quotation_count',string="Quotation")
	picking_count = fields.Float(compute='_get_picking_count',string="Picking")
	active = fields.Boolean(default=True)
	priority = fields.Selection([('0','False'),('1','Low'), ('2','Normal'), ('3','High')], 'Priority')
	sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False)
	
	fleet_id = fields.Many2one('fleet.vehicle',string='Fleet')
	license_plate = fields.Char(string='License Plate',related="fleet_id.license_plate")

	def _get_quotation_count(self):
		for quotation in self:
			quotation_ids = self.env['sale.order'].search([('diagnose_id','=',quotation.id)])
			quotation.quotation_count = len(quotation_ids)
	
	def _get_picking_count(self):
		for picking in self:
			picking_ids = self.env['stock.picking'].search([('origin', '=', self.name)])
			picking.picking_count = len(picking_ids)		
	
	def quotation_button(self):
		self.ensure_one()
		return {
			'name': 'Diagnosis Quotataion',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'sale.order',
			'domain': [('diagnose_id', '=', self.id)],
		}

	def picking_button(self):
		self.ensure_one()
		return {
			'name': 'Consume Parts Picking',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'stock.picking',
			'domain': [('origin', '=', self.name)],
		}
		
	
	def _get_total_hours(self):
		spent_hours = 0.0
		rem_hours = 0.0
		
		for hours in self.timesheet_ids:
			spent_hours += hours.unit_amount
			
		rem_hours = self.initially_planned_hour - spent_hours
		
		self.hours_spent = spent_hours
		self.remaining_hours = rem_hours
		return True 
		
	
	def create_quotation(self):
		res = {}
		diagnose_obj = self.env['car.diagnosys'].browse(self.ids[0])
		car_repair_obj = self.env['car.repair']
		product_obj = self.env['product.product']
		
		sale_order_vals = {
				'partner_id': diagnose_obj.partner_id.id or False,
				'state': 'draft',
				'date_order' : datetime.now(),
				'user_id' : diagnose_obj.assigned_to.id,
				'client_order_ref': diagnose_obj.name,
				'diagnose_id': diagnose_obj.id,
				}
		sale_order_id = self.env['sale.order'].create(sale_order_vals)                
		
		for car_line in diagnose_obj.car_repair_estimation_ids:
			sale_order_line_vals = {
								'product_id': car_line.product_id.id,
								'name': car_line.product_id.name,
								'product_uom_qty': car_line.quantity,
								'product_uom': car_line.product_id.uom_id.id,
								'price_unit' : car_line.price,
								'order_id': sale_order_id.id,
							}
			sale_order_line_id = self.env['sale.order.line'].create(sale_order_line_vals)

		for timesheet in diagnose_obj.timesheet_ids:
			sale_order_line_vals = {
								'name': timesheet.name,
								'product_id' : timesheet.type_id.product_id.id,
								'price_unit' : timesheet.total_cost,
								'order_id': sale_order_id.id,
							}
			sale_order_line_id = self.env['sale.order.line'].create(sale_order_line_vals)

		return res          
	
	def consume_car_parts(self):
		
		if self.env.user.company_id.consume_parts:
			picking_type_id = self.env['stock.picking.type'].search([['code','=','internal'],['warehouse_id.company_id','=',self.env.user.company_id.id]],limit=1)
			if not picking_type_id :

				warehouse = self.env['stock.warehouse'].search([('company_id', '=',self.env.user.company_id.id)], limit=1)

				picking_type_id = self.env['stock.picking.type'].create({
					'name' : 'Consume Parts',
					'code' : 'internal',
					'sequence_code': 'INT',
					'warehouse_id' : warehouse.id or False,
					'company_id' : self.env.user.company_id.id,
					'default_location_src_id': self.env.user.company_id.location_id.id,
					'default_location_dest_id' : self.env.user.company_id.location_dest_id.id,
					})

			picking = self.env['stock.picking'].create({
					'partner_id' : self.assigned_to.partner_id.id, 
					'picking_type_id' : picking_type_id.id,
					'picking_type_code': 'internal',
					'location_id' : self.env.user.company_id.location_id.id,
					'location_dest_id' : self.env.user.company_id.location_dest_id.id,
					'origin': self.name,
					})
			for estitmate in self.car_repair_estimation_ids:
				move = self.env['stock.move'].create({
					'picking_id': picking.id,
					'name': estitmate.product_id.name,
					'product_uom' : estitmate.product_id.uom_id.id,
					'product_id': estitmate.product_id.id,
					'product_uom_qty' : estitmate.quantity,
					'location_id' : self.env.user.company_id.location_id.id,
					'location_dest_id' : self.env.user.company_id.location_dest_id.id,
					'origin': self.name,
					})
		else:
			raise UserError(_("Please select the Consume Parts option in Inventory Settings to consume Car Parts"))

class CarRepairEstimate(models.Model):      
	_name = 'car.repair.estimate'    

	diagnosys_id = fields.Many2one('car.diagnosys',string="car Repair Estimate")
	workorder_id = fields.Many2one('car.workorder',string="Car Work Order") 
	product_consume_id = fields.Many2one('car.repair',string="Product Consume")       
	product_id = fields.Many2one('product.product',string="Product")
	quantity = fields.Float(string="Quantity")
	uom_id = fields.Many2one('uom.uom',string="Unit Of Measure")
	price = fields.Float(string="Price")
	notes = fields.Char(string="Notes")
	
	
	@api.onchange('product_id')
	def onchange_product_id(self):
		res = {}
		if not self.product_id:
			return res
		self.price = self.product_id.list_price

class CarWorkOrder(models.Model):      
	_name = 'car.workorder'
	
	name = fields.Char(string="Name")
	project_id = fields.Many2one('project.project',string="Project")
	assigned_to = fields.Many2one('res.users',string="Assigned To")
	initially_planned_hour = fields.Float(string="Initially Planned Hour",default=0.0)
	deadline_date = fields.Datetime(string="Deadline")
	tag_ids = fields.Many2one('project.tags',string="Tags")
	description = fields.Text(string="Description")
	workorder_timesheet_ids = fields.One2many('account.analytic.line','car_workorder_id',String="Timesheet")
	car_repair_estimation_ids = fields.One2many('car.repair.estimate','workorder_id',string="Car Repair Estimation")
	hours_spent = fields.Float(compute='_get_total_hours',string="Hours Spent",default=0.0)
	remaining_hours = fields.Float(compute='_get_total_hours',string="Remaining Hours",default=0.0)
	partner_id = fields.Many2one('res.partner',string="Customer")
	car_repair_id = fields.Many2one('car.repair',string="Car Repair")
	type_id = fields.Many2one('car.service.type',string="Type")
	active = fields.Boolean(default=True)
	priority = fields.Selection([('0','False'),('1','Low'), ('2','Normal'), ('3','High')], 'Priority')
	
	fleet_id = fields.Many2one('fleet.vehicle',string='Fleet')
	license_plate = fields.Char(string='License Plate',related="fleet_id.license_plate")
	
	def _get_total_hours(self):
		spent_hours = 0.0
		rem_hours = 0.0
		
		for hours in self.workorder_timesheet_ids:
			spent_hours += hours.unit_amount
			
		rem_hours = self.initially_planned_hour - spent_hours
		
		self.hours_spent = spent_hours
		self.remaining_hours = rem_hours
		return True 
		
class AccountAnalyticLine(models.Model):      
	_inherit = 'account.analytic.line'
	
	car_workorder_id = fields.Many2one('car.workorder',string="Car Workorder")
	timesheet_id = fields.Many2one('car.diagnosys',string="Car Diagnosys")
	type_id = fields.Many2one('car.service.type',string="Service Type")
	car_repair_timesheet_id = fields.Many2one('car.repair',string="Car Repair Timesheet")
	total_cost = fields.Float(string='Cost',compute="_cal_total_cost")

	@api.model
	def create(self, values):
		result = super(AccountAnalyticLine, self).create(values)
		car_repair_id = values.get('car_repair_timesheet_id')
		timesheet_id = values.get('timesheet_id') or self.env['car.diagnosys'].search([['car_repair_id','=',car_repair_id]],limit=1)
		car_workorder_id = values.get('car_workorder_id') or self.env['car.workorder'].search([['car_repair_id','=',car_repair_id]],limit=1)

		if car_repair_id:
			timesheets = self.env['account.analytic.line'].search([['car_repair_timesheet_id','=',values.get('car_repair_timesheet_id')]])
			if timesheet_id:
				timesheets.write({'timesheet_id':timesheet_id})
			if car_workorder_id:
				timesheets.write({'car_workorder_id':car_workorder_id})
		return result

	@api.depends('type_id','unit_amount')
	def _cal_total_cost(self):
		for timesheet in self:
			if timesheet.type_id and (timesheet.unit_amount > 0):
				timesheet.total_cost = timesheet.type_id.cost * timesheet.unit_amount
			else:
				timesheet.total_cost = 0.0

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	diagnose_id = fields.Many2one('car.diagnosys', string='Car Diagnosis')    

class ir_attachment(models.Model):
	_inherit='ir.attachment'

	car_repair_id  =  fields.Many2one('car.repair', 'Car Repair')    

class Website(models.Model):

	_inherit = "website"
	
	def get_car_repair_services_list(self):            
		car_services_ids=self.env['car.services'].sudo().search([])
		return car_services_ids

	def get_car_list(self):            
		car_ids=self.env['fleet.vehicle'].sudo().search([])
		return car_ids

	def get_brand_list(self):
		brand_ids = self.env['fleet.vehicle.model.brand'].sudo().search([])
		return brand_ids

	def get_model_list(self):        
		model_ids=self.env['fleet.vehicle.model'].sudo().search([])
		return model_ids
		

