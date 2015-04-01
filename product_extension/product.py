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
from openerp.osv import osv, orm, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import psycopg2
from openerp import tools


#----------------------------------------------------------
# Product Attributes
#----------------------------------------------------------
class ProductAttribute(orm.Model):
    _name = "product.attribute"
    _description = "Product Attribute"
    _columns = {
        'name': fields.char('Name', translate=True, required=True),
        'value_ids': fields.one2many(
            'product.attribute.value', 'attribute_id', 'Values', copy=True),
        'magento_attribute_id': fields.many2one(
            'magento.product.attribute', 'Magento Attribute'),
        'set_id': fields.many2one(
            'magento.attribute.set', 'Magento Attribute Set'),
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(
            ProductAttribute, self).create(cr, uid, vals, context=context)
        backend_ids = self.pool.get(
            'magento.backend').search(cr, uid, [])
        magento_attribute_vals = {
            'frontend_label': vals['name'],
            'attribute_code': 'x_' + vals['name'].lower(),
            'set_id': vals['set_id'],
            'scope': 'global',
            'fontend_input': 'select',
            'is_global': True,
            'is_configurable': True,
            'is_visible': True,
            'is_required': True,
            'backend_id': backend_ids[0] if backend_ids else False,
        }

        attribute_vals = {
            'field_description': vals['name'],
            'name': 'x_' + vals['name'].lower(),
            'attribute_type': 'select',
            'magento_bind_ids': [(0, 0, magento_attribute_vals)]
        }

        attribute_id = self.pool.get(
            'attribute.attribute').create(
            cr, uid, attribute_vals, context=context)

        odoo_attribute = self.pool.get(
            'attribute.attribute').browse(cr, uid, attribute_id)

        magento_attribute_id = odoo_attribute.magento_bind_ids[0].id

        self.write(
            cr, uid, res_id, {'magento_attribute_id': magento_attribute_id})
        return res_id


class ProductAttributeValue(orm.Model):
    _name = "product.attribute.value"
    _order = 'sequence'

    def _get_price_extra(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, 0)
        if not context.get('active_id'):
            return result

        for obj in self.browse(cr, uid, ids, context=context):
            for price_id in obj.price_ids:
                if price_id.product_tmpl_id.id == context.get('active_id'):
                    result[obj.id] = price_id.price_extra
                    break
        return result

    def _set_price_extra(self, cr, uid, id, name, value, args, context=None):
        if context is None:
            context = {}
        if 'active_id' not in context:
            return None
        p_obj = self.pool['product.attribute.price']
        p_ids = p_obj.search(
            cr, uid,
            [('value_id', '=', id),
             ('product_tmpl_id', '=', context['active_id'])],
            context=context)
        if p_ids:
            p_obj.write(
                cr, uid, p_ids, {'price_extra': value}, context=context)
        else:
            p_obj.create(
                cr, uid, {
                    'product_tmpl_id': context['active_id'],
                    'value_id': id,
                    'price_extra': value,
                }, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if context and not context.get('show_attribute', True):
            return super(
                ProductAttributeValue, self).name_get(
                cr, uid, ids, context=context)
        res = []
        for value in self.browse(cr, uid, ids, context=context):
            res.append(
                [value.id, "%s: %s" % (value.attribute_id.name, value.name)])
        return res

    _columns = {
        'sequence': fields.integer(
            'Sequence', help="Determine the display order"),
        'name': fields.char('Value', translate=True, required=True),
        'attribute_id': fields.many2one(
            'product.attribute', 'Attribute',
            required=True, ondelete='cascade'),
        'product_ids': fields.many2many(
            'product.product', id1='att_id',
            id2='prod_id', string='Variants', readonly=True),
        'price_extra': fields.function(
            _get_price_extra, type='float', string='Attribute Price Extra',
            fnct_inv=_set_price_extra,
            digits_compute=dp.get_precision('Product Price'),
            help="Price Extra: Extra price for the variant\
            with this attribute value on sale price.\
            eg. 200 price extra, 1000 + 200 = 1200."),
        'price_ids': fields.one2many(
            'product.attribute.price', 'value_id',
            string='Attribute Prices', readonly=True),
        'option_id': fields.many2one('magento.attribute.option', 'Option'),
    }
    _sql_constraints = [
        ('value_company_uniq', 'unique (name,attribute_id)',
         'This attribute value already exists !')
    ]
    _defaults = {
        'price_extra': 0.0,
    }

    def unlink(self, cr, uid, ids, context=None):
        ctx = dict(context or {}, active_test=False)
        product_ids = self.pool['product.product'].search(
            cr, uid, [('attribute_value_ids', 'in', ids)], context=ctx)
        if product_ids:
            raise osv.except_osv(
                _('Integrity Error!'), _('The operation cannot\
                be completed:\nYou trying to delete an attribute value\
                with a reference on a product variant.'))
        return super(ProductAttributeValue, self).unlink(
            cr, uid, ids, context=context)

    def create(self, cr, uid, vals, context=None):
        res_id = super(
            ProductAttributeValue, self).create(cr, uid, vals, context=context)
        attribute_code = self.browse(
            cr, uid, res_id).attribute_id.magento_attribute_id.attribute_code
        backend_ids = self.pool.get('magento.backend').search(cr, uid, [])
        backend_id = backend_ids[0] if backend_ids else False
        magento_attribute_id = self.browse(
            cr, uid, res_id).attribute_id.magento_attribute_id.id
        option_vals = {
            'name': vals['name'],
            'magento_attribute_code': attribute_code,
            'backend_id': backend_id,
            'magento_attribute_id': magento_attribute_id,
            'value': vals['name'],
        }

        option_id = self.pool.get(
            'magento.attribute.option').create(
            cr, uid, option_vals, context=context)

        self.write(cr, uid, res_id, {'option_id': option_id})

        return res_id


class ProductAttributePrice(orm.Model):
    _name = "product.attribute.price"
    _columns = {
        'product_tmpl_id': fields.many2one(
            'product.template', 'Product Template',
            required=True, ondelete='cascade'),
        'value_id': fields.many2one(
            'product.attribute.value', 'Product Attribute Value',
            required=True, ondelete='cascade'),
        'price_extra': fields.float(
            'Price Extra', digits_compute=dp.get_precision('Product Price')),
    }


class ProductAttributeLine(orm.Model):
    _name = "product.attribute.line"
    _rec_name = 'attribute_id'
    _columns = {
        'product_tmpl_id': fields.many2one(
            'product.template', 'Product Template',
            required=True, ondelete='cascade'),
        'attribute_id': fields.many2one(
            'product.attribute', 'Attribute',
            required=True, ondelete='restrict'),
        'value_ids': fields.many2many(
            'product.attribute.value', id1='line_id',
            id2='val_id', string='Product Attribute Value'),
    }


class ProductTemplate(orm.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'mail.thread']

    def _is_product_variant(self, cr, uid, ids, name, arg, context=None):
        return self._is_product_variant_impl(
            cr, uid, ids, name, arg, context=context)

    def _is_product_variant_impl(self, cr, uid, ids, name, arg, context=None):
        return dict.fromkeys(ids, False)

    def _set_standard_price(
            self, cr, uid, product_tmpl_id, value, context=None):
        """
            Store the standard price change in order to be able to
            retrieve the cost of a product template for a given date
        """
        if context is None:
            context = {}
        price_history_obj = self.pool['product.price.history']
        user_company = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        company_id = context.get('force_company', user_company)
        price_history_obj.create(cr, uid, {
            'product_template_id': product_tmpl_id,
            'cost': value,
            'company_id': company_id,
        }, context=context)

    def _get_product_variant_count(
            self, cr, uid, ids, name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids):
            res[product.id] = len(product.product_variant_ids)
        return res

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(
                obj.image, avoid_resize_medium=True)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(
            cr, uid, [id],
            {'image': tools.image_resize_image_big(value)}, context=context)

    _columns = {
        'image': fields.binary(
            "Image",
            help="This field holds the image used as image for the product,\
                limited to 1024x1024px."),
        'image_medium': fields.function(
            _get_image, fnct_inv=_set_image,
            string="Medium-sized image",
            type="binary",
            multi="_get_image",
            store={
                'product.template': (
                    lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of the product. It is automatically \
                 resized as a 128x128px image, with aspect ratio preserved,\
                 only when the image exceeds one of those sizes. Use this \
                 field in form views or some kanban views."),
        'image_small': fields.function(
            _get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'product.template': (
                    lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of the product. It is automatically \
                 resized as a 64x64px image, with aspect ratio preserved.\
                 Use this field anywhere a small image is required."),
        # 'packaging_ids': fields.one2many(
        #     'product.packaging', 'product_tmpl_id', 'Logistical Units',
        #     help="Gives the different ways to package the same product.
        #           "This has no impact on "
        #         the picking order and is mainly used
        #         if you use the EDI module."),
        'lst_price': fields.related(
            'list_price', type="float",
            string='Public Price',
            digits_compute=dp.get_precision('Product Price')),
        'is_product_variant': fields.function(
            _is_product_variant, type='boolean', string='Is product variant'),
        'attribute_line_ids': fields.one2many(
            'product.attribute.line', 'product_tmpl_id', 'Product Attributes'),
        'product_variant_ids': fields.one2many(
            'product.product', 'product_tmpl_id', 'Products', required=True),
        'pricelist_id': fields.dummy(
            string='Pricelist', relation='product.pricelist', type='many2one'),
        'active': fields.boolean(
            'Active', help="If unchecked, it will allow you to hide the\
             product without removing it."),
        'product_variant_count': fields.function(
            _get_product_variant_count, type='integer',
            string='# of Product Variants'),
        'ean13': fields.related(
            'product_variant_ids', 'ean13',
            type='char', string='EAN13 Barcode'),
        'default_code': fields.related(
            'product_variant_ids', 'default_code',
            type='char', string='Internal Reference'),
    }

    _defaults = {
        'active': True
    }

    def create_variant_ids(self, cr, uid, ids, context=None):
        product_obj = self.pool.get("product.product")
        ctx = context and context.copy() or {}

        if ctx.get("create_product_variant"):
            return None

        ctx.update(active_test=False, create_product_variant=True)

        tmpl_ids = self.browse(cr, uid, ids, context=ctx)
        for tmpl_id in tmpl_ids:

            # list of values combination
            variant_alone = []
            all_variants = [[]]
            for variant_id in tmpl_id.attribute_line_ids:
                if len(variant_id.value_ids) == 1:
                    variant_alone.append(variant_id.value_ids[0])
                temp_variants = []
                for variant in all_variants:
                    for value_id in variant_id.value_ids:
                        temp_variants.append(variant + [int(value_id)])
                all_variants = temp_variants

            # adding an attribute with only
            #one value should not recreate product
            # write this attribute on every product to make
            # sure we don't lose them
            for variant_id in variant_alone:
                product_ids = []
                for product_id in tmpl_id.product_variant_ids:
                    if variant_id.id not in \
                            map(int, product_id.attribute_value_ids):
                        product_ids.append(product_id.id)
                product_obj.write(
                    cr, uid, product_ids,
                    {'attribute_value_ids': [(4, variant_id.id)]}, context=ctx)

            # check product
            variant_ids_to_active = []
            variants_active_ids = []
            variants_inactive = []
            for product_id in tmpl_id.product_variant_ids:
                variants = map(int, product_id.attribute_value_ids)
                if variants in all_variants:
                    variants_active_ids.append(product_id.id)
                    all_variants.pop(all_variants.index(variants))
                    if not product_id.active:
                        variant_ids_to_active.append(product_id.id)
                else:
                    variants_inactive.append(product_id)
            if variant_ids_to_active:
                product_obj.write(
                    cr, uid, variant_ids_to_active,
                    {'active': True}, context=ctx)

            # create new product
            for variant_ids in all_variants:
                values = {
                    'product_tmpl_id': tmpl_id.id,
                    'attribute_value_ids': [(6, 0, variant_ids)]
                }
                id = product_obj.create(cr, uid, values, context=ctx)
                variants_active_ids.append(id)

            # unlink or inactive product
            for variant_id in map(int, variants_inactive):
                try:
                    product_obj.unlink(cr, uid, [variant_id], context=ctx)
                except (psycopg2.Error, osv.except_osv):
                    product_obj.write(
                        cr, uid, [variant_id], {'active': False}, context=ctx)
                    pass
        return True

    def create(self, cr, uid, vals, context=None):
        """
            Store the initial standard price in order to be able
            to retrieve the cost of a product template for a given date
        """
        product_template_id = super(ProductTemplate, self).create(
            cr, uid, vals, context=context)
        if not context or "create_product_product" not in context:
            self.create_variant_ids(
                cr, uid, [product_template_id], context=context)
        self._set_standard_price(
            cr, uid, product_template_id,
            vals.get('standard_price', 0.0), context=context)

        # TODO: this is needed to set given values
        # to first variant after creation
        # these fields should be moved to product as lead to confusion
        related_vals = {}
        if vals.get('ean13'):
            related_vals['ean13'] = vals['ean13']
        if vals.get('default_code'):
            related_vals['default_code'] = vals['default_code']
        if related_vals:
            self.write(
                cr, uid, product_template_id, related_vals, context=context)

        return product_template_id

    def write(self, cr, uid, ids, vals, context=None):
        """
            Store the standard price change in order to be able to retrieve the
            cost of a product template for a given date
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(ProductTemplate, self).write(
            cr, uid, ids, vals, context=context)
        if 'attribute_line_ids' in vals or vals.get('active'):
            self.create_variant_ids(cr, uid, ids, context=context)
        if 'active' in vals and not vals.get('active'):
            ctx = context and context.copy() or {}
            ctx.update(active_test=False)
            product_ids = []
            for product in self.browse(cr, uid, ids, context=ctx):
                product_ids = map(int, product.product_variant_ids)
            self.pool.get("product.product").write(
                cr, uid, product_ids,
                {'active': vals.get('active')}, context=ctx)
        return res


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _is_product_variant_impl(self, cr, uid, ids, name, arg, context=None):
        return dict.fromkeys(ids, True)

    def _get_price_extra(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context=context):
            price_extra = 0.0
            for variant_id in product.attribute_value_ids:
                for price_id in variant_id.price_ids:
                    if price_id.product_tmpl_id.id == product.product_tmpl_id.id:
                        price_extra += price_id.price_extra
            result[product.id] = price_extra
        return result

    _columns = {
        'attribute_value_ids': fields.many2many(
            'product.attribute.value', id1='prod_id', id2='att_id',
            string='Attributes', readonly=True, ondelete='restrict'),
        'is_product_variant': fields.function(
            _is_product_variant_impl,
            type='boolean', string='Is product variant'),
        'price_extra': fields.function(
            _get_price_extra, type='float',
            string='Variant Extra Price',
            help="This is the sum of the extra price of all attributes"),
    }

    def write(self, cr, uid, ids, vals, context=None):
        result = super(
            ProductProduct, self).write(cr, uid, ids, vals, context=context)

        return result


class ProducePriceHistory(orm.Model):
    """
    Keep track of the ``product.template`` standard prices as they are changed.
    """

    _name = 'product.price.history'
    _rec_name = 'datetime'
    _order = 'datetime desc'

    _columns = {
        'company_id': fields.many2one('res.company', required=True),
        'product_template_id': fields.many2one(
            'product.template', 'Product Template',
            required=True, ondelete='cascade'),
        'datetime': fields.datetime('Historization Time'),
        'cost': fields.float('Historized Cost'),
    }

    def _get_default_company(self, cr, uid, context=None):
        if 'force_company' in context:
            return context['force_company']
        else:
            company = self.pool['res.users'].browse(
                cr, uid, uid,
                context=context).company_id
            return company.id if company else False

    _defaults = {
        'datetime': fields.datetime.now,
        'company_id': _get_default_company,
    }
