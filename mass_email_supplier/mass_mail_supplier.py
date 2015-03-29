# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2014 Elico Corp. All Rights Reserved.
#    Qing Wang <qing.wang@elico-corp.com> &Kevin Lee
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

from openerp.osv import orm, osv, fields
import logging
from datetime import datetime, timedelta
from openerp import netsvc
import xmlrpclib
from openerp.tools.translate import _
from openerp.http import request


_logger = logging.getLogger(__name__)

# ORDER_STATUS_MAPPING = {
#     'canceled': 'cancel',
#    }
TRANSPORT_COMPANY_CARRIER_CODE_MAPPING = {
    'tablerate_bestway': 'EMS'
}


# 全球采购商品/定价商品  521
# 食品    522
# 定制商品  523

MAGENTO_WKF_CAGETORY = {
    '522': 'food',
    '523': 'customized',
    '521': 'gloable_priced',
}
# @magento_lifemall
# class LMSaleOrderImport(SaleOrderImport):
class mass_mail_supplier:
    def send_email_to_supplier(self, order_id, email_template, context=None):
        if context is None:
            context = {'active_model': 'sale.order', 'active_id': order_id}
        cr = self.session.cr
        uid = self.session.uid
        pool = self.session.pool
        ir_model_data = pool.get('ir.model.data')
        res_id = ir_model_data.get_object_reference(
            cr, uid, 'magento_lifemall', email_template)[1]
        action_pool = pool.get('ir.actions.server')

        try:
            action_pool.run(cr, uid, [res_id], context=context)
        except Exception, e:
            pass

    def add_message_followers(self, sale_order):
        """
            add orderline supplier to sale order message followers
        """
        for item in sale_order.order_line:
            if item.product_id.seller_ids:
                self.session.create(
                    'mail.followers',
                    {
                        'res_model': 'sale.order',
                        'res_id': sale_order.id,
                        'partner_id': item.product_id.seller_ids[0].name.id
                    })

    def _filter_data(self, data):
        if data.get('order_line', False):
            data.pop('order_line')
        return data

    def _after_create(self, binding_id):
        """
            after sale order create we need to some extra operation
        """
        binder = self.session.browse(
            self.model._name, binding_id)
        self.add_message_followers(binder.openerp_id)
        if binder.openerp_id.message_follower_ids:
            self.send_email_to_supplier(
                binder.openerp_id.id,
                'ir_actions_server_send_email_when_quotation_create')

    def _after_update(self, binding_id):
        binder = self.session.browse(
            self.model._name, binding_id)

        if binder.payment_timeout and binder.openerp_id.message_follower_ids:
            self.send_email_to_supplier(
                binder.openerp_id.id,
                'ir_actions_server_send_email_when_payment_timeout')

        if binder.customer_canceled and binder.openerp_id.message_follower_ids:
            self.send_email_to_supplier(
                binder.openerp_id.id,
                'ir_actions_server_send_email_when_customer_cancel')
