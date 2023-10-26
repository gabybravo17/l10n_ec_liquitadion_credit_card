import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_liquidation_tc = env["account.credit.card.liquidation"].search([])
    company = all_liquidation_tc.mapped("company_id")
    current_fiscal_lock_date = company.fiscalyear_lock_date
    current_tax_lock_date = company.tax_lock_date
    if current_fiscal_lock_date:
        company.fiscalyear_lock_date = None
    if current_tax_lock_date:
        company.tax_lock_date = None
    for liquidation in all_liquidation_tc:
        name_recap = " Recaps " + " - ".join(
            str(e) for e in liquidation.line_ids.mapped("recap_id").mapped("name")
        )
        for line in liquidation.move_ids:
            try:
                line.write(
                    {
                        "name": line.name + name_recap,
                        "partner_id": liquidation.partner_id.id,
                    }
                )
            except Exception as e:
                _logger.exception(e)
    company.fiscalyear_lock_date = current_fiscal_lock_date
    company.tax_lock_date = current_tax_lock_date
