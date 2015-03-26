# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Sébastien BEAU
#    Copyright 2011-2013 Akretion
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

from openerp import tools
from openerp.osv import osv, fields, expression

class product_template(osv.osv):
    _name = "product.template"
    _inherit = 'product.template'

    _columns = {
        'default_code': fields.related('product_variant_ids', 'default_code', type='char', string='Internal Reference'),
    }

    _defaults = {
        'default_code': lambda s,cr,uid,c: s.pool.get('ir.sequence').get(cr, uid, 'product.sequence',context=c), 

    }