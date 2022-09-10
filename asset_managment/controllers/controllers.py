# -*- coding: utf-8 -*-
# from odoo import http


# class AssetManagment(http.Controller):
#     @http.route('/asset_managment/asset_managment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/asset_managment/asset_managment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('asset_managment.listing', {
#             'root': '/asset_managment/asset_managment',
#             'objects': http.request.env['asset_managment.asset_managment'].search([]),
#         })

#     @http.route('/asset_managment/asset_managment/objects/<model("asset_managment.asset_managment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('asset_managment.object', {
#             'object': obj
#         })
