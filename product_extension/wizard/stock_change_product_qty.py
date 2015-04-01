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
from openerp.osv import osv, orm
from openerp.tools.translate import _


class StockChangeProductQty(osv.osv_memory):
    _inherit = 'stock.change.product.qty'

    def default_get(self, cr, uid, fields, context):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        res = super(
            StockChangeProductQty, self).default_get(
            cr, uid, fields, context=context)
        if context.get('active_model') == 'product.template':
            product_ids = self.pool.get('product.product').search(
                cr, uid, [('product_tmpl_id', '=', context.get('active_id'))],
                context=context)
            if len(product_ids) == 1:
                res['product_id'] = product_ids[0]
            else:
                raise orm.except_orm(
                    _('Warning'),
                    _('Please use the Product Variant view\
                    to update the product quantity.'))
        return res
