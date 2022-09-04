# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


import werkzeug
import json
import base64

import odoo.http as http
from odoo.http import request
from odoo import SUPERUSER_ID, _
from datetime import datetime, timedelta, time
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import odoo.http as http

class WebsiteCarRepair(CustomerPortal):

    @http.route('/car_repair', type="http", auth="public", website=True)
    def car_repair_request(self, **kw):
        """Let's public and registered user submit a Car Repair Request"""
        name = ""
        if http.request.env.user.name != "Public user":
            name = http.request.env.user.name
            
        email = http.request.env.user.partner_id.email
        phone = http.request.env.user.partner_id.phone
        values = {'user_ids': name,'email':email,'phone':phone}
        
        return http.request.render('bi_car_repair_management.bi_create_car_repair', values)

    @http.route('/car_repair/thankyou', type="http", auth="public", website=True)
    def car_repair_thankyou(self, **post):
        """Displays a thank you page after the user submit a Car Repair Request"""
        if post.get('debug'):
            return request.render("bi_car_repair_management.car_repair_request_thank_you")

        user_brw = request.env['res.users'].sudo().browse(request._uid)
        
        Attachments = request.env['ir.attachment']
        upload_file = post['upload']
        
        
        car_repair_technician_id = request.env['ir.model.data'].sudo().\
        get_object_reference('bi_car_repair_management','group_car_repair_technician')[1]
        group_manager = request.env['res.groups'].sudo().browse(car_repair_technician_id)
        if group_manager.users:
            technician_id = group_manager.users[0].id
        else:
            technician_id = False
        vals = {
                    'name' : post['name'],
                    'technician_id' : technician_id,
                    'partner_id' : user_brw.partner_id.id,
                    'client_email' : post['email_from'],
                    'client_phone' : post['phone'],
                    'company_id' : user_brw.company_id.id or False,
                    'repair_request_date' : datetime.now(),
                    'priority' : post['priority'],
                    'year' : post['year'],
                    'damage' : post['damage'],
                    'stage' : "new",
                    'problem' : post['problem'],     
            }
        if (post['product_id'] != ''):
            vals.update({
                'fleet_id' : int(post['product_id']),
                })
        if (post['brand'] != ''):
            vals.update({
                'brand' : int(post['brand']),
                })  
        if (post['model'] != ''):
            vals.update({
                'model' : int(post['model']),
                })
        if (post['car_services_id'] != ''):
            vals.update({
                'car_services_id' : int(post['car_services_id']),
                })             

        car_repair_obj = request.env['car.repair'].sudo().create(vals)
        
        if upload_file:
            attachment_id = Attachments.sudo().create({
                'name': upload_file.filename,
                'type': 'binary',
                'datas': base64.encodestring(upload_file.read()),
                'public': True,
                'res_model': 'ir.ui.view',
                'car_repair_id' : car_repair_obj.id,
            }) 

        return request.render("bi_car_repair_management.car_repair_request_thank_you")  

    def _prepare_portal_layout_values(self):
        values = super(WebsiteCarRepair, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        car_repair = request.env['car.repair']
        partner_car_repair_count = car_repair.sudo().search([('partner_id','=',partner.id)])
        repair_count = car_repair.sudo().search_count([('partner_id','=',partner.id)])

        values.update({
            'repair_count': repair_count,
        })
        return values  
        
    @http.route(['/my/car_repair', '/my/car_repair/page/<int:page>'], type='http', auth="public", website=True)
    def portal_my_car_repair(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        car_repair = request.env['car.repair']
        domain = []
        # count for pager
        repair_count = car_repair.sudo().search_count(domain)
        # make pager
        pager = request.website.sudo().pager(
            url="/my/car_repair",
            total=repair_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        partner = request.env.user.partner_id
        car = car_repair.sudo().search([('partner_id','=',partner.id)], limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'car': car.sudo(),
            'page_name': 'car_repair',
            'pager': pager,
            'default_url': '/my/car_repair',
        })
        
        return request.render("bi_car_repair_management.portal_my_car_repair", values)

    @http.route(['/car/view/detail/<int:car>'],type='http',auth="public",website=True)
    def car_view(self, car, category='', search='', **kwargs):
        
        context = dict(request.env.context or {})
        car_obj = request.env['car.repair'].sudo()
        context.update(active_id=car)
        car_data_list = []
        car_data = car_obj.sudo().browse(int(car))
        
        for items in car_data:
            car_data_list.append(items)
            
        return http.request.render('bi_car_repair_management.car_repair_request_view',{
            'car_data_list': car_data_list
        }) 


    @http.route(['/car_repair/message'],type='http',auth="public",website=True)
    def car_message(self, **post):
        Attachments = request.env['ir.attachment']
        upload_file = post['upload']
        
        if ',' in post.get('car_id'):
            bcd = post.get('car_id').split(',')
        else : 
            bcd = [post.get('car_id')]
            
        car_repair_obj = request.env['car.repair'].sudo().search([('id','in',bcd)])
            
        if upload_file:
            attachment_id = Attachments.sudo().create({
                'name': upload_file.filename,
                'type': 'binary',
                'datas': base64.encodestring(upload_file.read()),
                'public': True,
                'res_model': 'ir.ui.view',
                'car_repair_id' : car_repair_obj.id,
            })

        context = dict(request.env.context or {})

        if post.get( 'message' ):
            message_id1 = car_repair_obj.sudo().message_post(
                type='comment',
                subtype='mt_comment')
                
            message_id1.body = post.get( 'message' )
            message_id1.type = 'comment'
            message_id1.subtype = 'mt_comment'
            message_id1.model = 'car.repair'
            message_id1.res_id = post.get( 'car_id' )
                    
        return http.request.render('bi_car_repair_management.car_repair_request_thank_you') 


    @http.route(['/car/comment/<int:car>'],type='http',auth="public",website=True)
    def car_comment_page(self, car,**post):  
        car_id = request.env['car.repair'].sudo().browse(int(car))
        return http.request.render('bi_car_repair_management.car_repair_comment',{'car': car_id}) 
     
    @http.route(['/car_repair/comment/send'],type='http',auth="public",website=True)
    def car_repair_comment(self, **post):
        if post.get('debug'):
            return http.request.render('bi_car_repair_management.car_repair_rating_thank_you')
        context = dict(request.env.context or {})
        car_repair_obj = request.env['car.repair'].sudo().browse(int(post['car_id']))
        car_repair_obj.update({
                'customer_rating' : post.get('customer_rating'),            
                'comment' : post.get('comment'),
        })
        return http.request.render('bi_car_repair_management.car_repair_rating_thank_you') 


    @http.route('/action/send', type='json', auth='public')
    def car_request_data(self, **post):
        if post['car_id']:
            car = request.env['fleet.vehicle'].sudo().browse(int(post['car_id']))
            temp = {
                    "model_id": car.model_id.id,
                    "brand_id": car.model_id.brand_id.id,
                    "year": car.model_year,
                    }
        else:
            temp = {
                    "model_id": '',
                    "brand_id": '',
                    "year": '',
                    }
        
        data = json.dumps(temp)
        return data         
              	
    	       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
