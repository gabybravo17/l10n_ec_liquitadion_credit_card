from odoo import api, models


class AccountReconciliationWidget(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _get_reconcile_lines_for_credit_card(
        self,
        st_line,
        partner_id=None,
        excluded_ids=None,
        search_str=False,
        offset=0,
        limit=None,
        mode=None,
        strict_date=False,
        strict_amount=False,
    ):
        """
        Find credit card liquidation that might be candidates
        for matching a statement line.
        Return lines to reconcile our statement line with.
        """
        aml_obj = self.env["account.move.line"]
        aml_accounts = [
            st_line.journal_id.default_credit_account_id.id,
            st_line.journal_id.default_debit_account_id.id,
        ]
        domain_credit_card = [
            ("move_id", "!=", False),
            ("state", "in", ["done"]),
        ]
        # cuando sea macth para conciliacion filtrar por fechas
        # en sugerencias de conciliacion no filtrar
        if strict_date:
            domain_credit_card.append(("date_account", "=", st_line.date))
        # TODO: la liquidacion no tiene un campo de referencia
        # para filtrar con search_str
        # intentar implementarlo o buscar por el lote de las lineas
        credit_card_recs = self.env["account.credit.card.liquidation"].search(
            domain_credit_card
        )
        move_recs = credit_card_recs.mapped("move_id")
        domain = [
            ("move_id", "in", move_recs.ids),
            ("reconciled", "=", False),
            ("statement_id", "=", False),
            ("account_id", "in", aml_accounts),
        ]
        if excluded_ids:
            domain.append(("id", "not in", excluded_ids))
        if strict_amount:
            domain.append(("balance", "=", strict_amount))
        move_lines = aml_obj.search(domain, offset=offset, limit=limit)
        return move_lines

    def _prepare_proposition_from_credit_card(
        self,
        st_line,
        partner_id=None,
        excluded_ids=None,
        search_str=False,
        offset=0,
        limit=None,
        mode=None,
        strict_date=False,
        strict_amount=False,
    ):
        """Fill with the expected format the reconciliation proposition
        for the given statement line and possible credit card liquidation.
        """
        target_currency = (
            st_line.currency_id
            or st_line.journal_id.currency_id
            or st_line.journal_id.company_id.currency_id
        )
        elegible_lines = self._get_reconcile_lines_for_credit_card(
            st_line,
            partner_id=partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            offset=offset,
            limit=limit,
            mode=mode,
            strict_date=strict_date,
            strict_amount=strict_amount,
        )
        if elegible_lines:
            return self._prepare_move_lines(
                elegible_lines,
                target_currency=target_currency,
                target_date=st_line.date,
            )
        return []

    def get_bank_statement_line_data(self, st_line_ids, excluded_ids=None):
        """
        agregar los apuntes de liquidacion de TC como sugerencias automaticas,
        se hara filtro de fecha y monto
        """
        res = super().get_bank_statement_line_data(
            st_line_ids,
            excluded_ids=excluded_ids,
        )
        for line_vals in res.get("lines", []):
            st_line_obj = self.env["account.bank.statement.line"]
            st_line = st_line_obj.browse(line_vals["st_line"]["id"])
            proposition_vals = self._prepare_proposition_from_credit_card(
                st_line,
                excluded_ids=excluded_ids,
                search_str=st_line.name,
                strict_date=True,
                strict_amount=True,
            )
            if proposition_vals:
                line_vals["reconciliation_proposition"] = proposition_vals
        return res

    @api.model
    def get_move_lines_for_bank_statement_line(
        self,
        st_line_id,
        partner_id=None,
        excluded_ids=None,
        search_str=False,
        offset=0,
        limit=None,
        mode=None,
    ):
        """
        agregar los apuntes de liquidacion de TC
        a las sugerencias que se podrian conciliar
        No se hara busqueda exacta de fecha ni de monto
        """
        res = super().get_move_lines_for_bank_statement_line(
            st_line_id,
            partner_id=partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            offset=offset,
            limit=limit,
            mode=mode,
        )
        if mode == "rp":
            st_line_obj = self.env["account.bank.statement.line"]
            st_line = st_line_obj.browse(st_line_id)
            proposition_vals = self._prepare_proposition_from_credit_card(
                st_line,
                partner_id=partner_id,
                excluded_ids=excluded_ids,
                search_str=search_str,
                offset=offset,
                limit=limit,
                mode=mode,
            )
            if proposition_vals:
                res.extend(proposition_vals)
        return res
