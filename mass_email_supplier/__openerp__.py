# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2013 Elico Corp. All Rights Reserved.
#    Kevin Lee <kevin.lee@elico-corp.com>
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

{
    'name': 'Automatically send Email to vendors',
    'version': '1.0.0',
    'category': 'Product',
    'author': 'Elico Corp',
    'website': 'http://www.elico-corp.com',
    'summary': '',
    'description': """
        Automatically send Email to vendor for the canceled order,
        Automatically send email to vendor for confirmed quotation
        """,
    'sequence': 10,
    'depends': [
        'base_setup',
        'mail',
        'email_template',
        'sale'],
    'data': [
        'security/server_action_view.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
}
