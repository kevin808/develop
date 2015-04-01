# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2014 Elico Corp. All Rights Reserved.
#    Qing Wang <wang.qing@elico-corp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields


class StockProduct(orm.Model):
    _inherit = 'product.template'

    def _product_available(self, cr, uid, ids, name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                "qty_available": sum(
                    [p.qty_available for p in product.product_variant_ids]),
                "virtual_available": sum(
                    [p.virtual_available for p in product.product_variant_ids]
                ),
                "incoming_qty": sum(
                    [p.incoming_qty for p in product.product_variant_ids]),
                "outgoing_qty": sum(
                    [p.outgoing_qty for p in product.product_variant_ids]),
            }
        return res

    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        prod = self.pool.get("product.product")
        res = []
        for field, operator, value in domain:
            #to prevent sql injections
            assert field in (
                'qty_available',
                'virtual_available',
                'incoming_qty',
                'outgoing_qty'), 'Invalid domain left operand'
            assert operator in (
                '<', '>', '=', '!=', '<=', '>='), 'Invalid domain operator'
            assert isinstance(
                value, (float, int)), 'Invalid domain right operand'

            if operator == '=':
                operator = '=='

            product_ids = prod.search(cr, uid, [], context=context)
            ids = []
            if product_ids:
                #TODO: use a query instead of this browse record which is
                # probably making the too much requests, but don't forget
                #the context that can be set with a location, an owner...
                for element in prod.browse(
                        cr, uid, product_ids, context=context):
                    if eval(str(element[field]) + operator + str(value)):
                        ids.append(element.id)
            res.append(('product_variant_ids', 'in', ids))
        return res

    _columns = {
        'qty_available': fields.function(
            _product_available, multi='qty_available',
            fnct_search=_search_product_quantity,
            type='float', string='Quantity On Hand'),
        'virtual_available': fields.function(
            _product_available, multi='qty_available',
            fnct_search=_search_product_quantity,
            type='float', string='Quantity Available'),
        'track_all': fields.boolean(
            'Full Lots Traceability',
            help="Forces to specify a Serial Number\
            on each and every operation related to this product"),
        'track_incoming': fields.boolean(
            'Track Incoming Lots',
            help="Forces to specify a Serial Number\
            for all moves containing this product\
            and coming from a Supplier Location"),
        'track_outgoing': fields.boolean(
            'Track Outgoing Lots',
            help="Forces to specify a Serial Number\
            for all moves containing this product and\
            going to a Customer Location"),
        'incoming_qty': fields.function(
            _product_available, multi='qty_available',
            fnct_search=_search_product_quantity,
            type='float', string='Incoming'),
        'outgoing_qty': fields.function(
            _product_available, multi='qty_available',
            fnct_search=_search_product_quantity,
            type='float', string='Outgoing'),
    }
