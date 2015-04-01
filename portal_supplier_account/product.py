# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2014 Elico Corp. All Rights Reserved.
#    Qing Wang <qing.wang@elico-corp.com>
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


class product_product(orm.Model):
    _inherit = 'product.product'

    _defaults = {
        'procure_method': 'make_to_order',
        'supply_method': 'buy',
        'type': 'product',
    }

    _columns = {
        'supplier_stock_count': fields.integer('Stock Count'),
    }


class ProductTemplate(orm.Model):
    _inherit = 'product.template'

    def _check_user_is_supplier(self, cr, uid, context=None):
        """
            Check if current user in Portal Supplier Account Group
        """
        group_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid,
            'portal_supplier_account',
            'res_portal_supplier_account')[1]

        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        res_group = self.pool.get(
            'res.groups').browse(cr, uid, group_id, context=context)
        return bool(user) if user in res_group.users else False

    def _add_supplier_info(self, cr, uid, product_id, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        supplier_info = {
            'return_instructions': False,
            'name': user.partner_id.id,
            'sequence': 1,
            'company_id': 1,
            'delay': 1,
            'warranty_return_other_address_id': False,
            'warranty_duration': 0,
            'pricelist_ids': [],
            'warranty_return_partner': 'company',
            'min_qty': 0,
            'product_code': False,
            'product_name': False,
            'active_supplier': False,
            'direct_delivery_flag': True,
            'product_id': product_id,
        }

        self.pool.get(
            'product.supplierinfo').create(
            cr, uid, supplier_info, context=context)

    def create(self, cr, uid, vals, context=None):
        product_id = super(
            ProductTemplate, self).create(cr, uid, vals, context=context)

        check_result = self._check_user_is_supplier(
            cr, uid, context=context)
        if check_result and not self.browse(cr, uid, product_id).seller_ids:
            self._add_supplier_info(cr, uid, product_id, context=context)

        return product_id


class ProductAttribute(orm.Model):
    _inherit = 'product.attribute'

    def _check_user_is_supplier(self, cr, uid, context=None):
        """
            Check if current user in Portal Supplier Account Group
        """
        group_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid,
            'portal_supplier_account',
            'res_portal_supplier_account')[1]

        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        res_group = self.pool.get(
            'res.groups').browse(cr, uid, group_id, context=context)
        return bool(user) if user in res_group.users else False

    def create(self, cr, uid, vals, context=None):
        check = self._check_user_is_supplier(
            cr, uid, context=context)

        if check:
            vals.update({'user_id': uid})

        return super(ProductAttribute, self).create(
            cr, uid, vals, context=context)

    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
    }


class ProductAttributeValue(orm.Model):
    _inherit = 'product.attribute.value'

    def _check_user_is_supplier(self, cr, uid, context=None):
        """
            Check if current user in Portal Supplier Account Group
        """
        group_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid,
            'portal_supplier_account',
            'res_portal_supplier_account')[1]

        user = self.pool.get('res.users').browse(
            cr, uid, uid, context=context)
        res_group = self.pool.get(
            'res.groups').browse(cr, uid, group_id, context=context)
        return bool(user) if user in res_group.users else False

    def search(
        self, cr, user,
            args, offset=0, limit=None,
            order=None, context=None, count=False):

        supplier = self._check_user_is_supplier(cr, user, context=context)
        # partner_id = self.pool['res.users'].browse(cr, user, user).partner_id
        if supplier:
            args.extend(
                [('attribute_id.user_id', '!=', False),
                 ('attribute_id.user_id', '=', user)])

        return super(ProductAttributeValue, self).search(
            cr, user, args, offset=offset,
            limit=limit, order=order, context=context, count=count)
