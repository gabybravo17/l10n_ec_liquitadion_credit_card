from odoo import _, fields, models


class L10nEcWithhold(models.Model):
    _inherit = "l10n_ec.withhold"

    l10n_ec_credit_card_liquidation_id = fields.Many2one(
        "account.credit.card.liquidation",
        string="Credit Card Liquidation",
        readonly=True,
    )

    def get_destination_account(self):
        if self.type == "credit_card":
            return self.l10n_ec_credit_card_account_id
        return super(L10nEcWithhold, self).get_destination_account()

    def _prepare_move_line(self, move, line, destination_account):
        debit_vals, credit_vals = super(L10nEcWithhold, self)._prepare_move_line(
            move, line, destination_account
        )
        if self.l10n_ec_credit_card_liquidation_id:
            name_recap = " Recaps " + " - ".join(
                str(e)
                for e in self.l10n_ec_credit_card_liquidation_id.line_ids.mapped(
                    "recap_id"
                ).mapped("name")
            )
            debit_vals["name"] += (
                _(" LIQ: %s" % self.l10n_ec_credit_card_liquidation_id.number)
                + name_recap
            )
            credit_vals["name"] += (
                _(" LIQ: %s" % self.l10n_ec_credit_card_liquidation_id.number)
                + name_recap
            )
        return debit_vals, credit_vals
