import re
from typing import Optional
from django.db.models import Q
from medialib import models as ml_models


class DSLError(Exception):
    pass


class TagDSLParser:
    """
    Tag DSL parser:
    & (AND), | (OR), ! (NOT), - (unary NOT)
    () - regular groups
    {} - AND groups (space character = &)
    [] - OR groups (space character = |)
    """

    def __init__(self, query_string: str):
        self.query_string: str = query_string
        self.tokens: list[re.Match[str]] = self._tokenize(query_string)
        self.tokens_length: int = len(self.tokens)
        self.token_idx: int = 0

    def _tokenize(self, s: str) -> list[re.Match[str]]:
        """
        Translates DSL query string into the list of tokens
        """
        token_specification = [
            ("L_BRACE", r"\{"),
            ("R_BRACE", r"\}"),
            ("L_BRACKET", r"\["),
            ("R_BRACKET", r"\]"),
            ("L_PAREN", r"\("),
            ("R_PAREN", r"\)"),
            ("AND", r"\&"),
            ("OR", r"\|"),
            (
                "EXPLICIT_NOT",
                r"\!",
            ),
            (
                "UNARY_NOT",
                r"\-",
            ),
            ("TAG", r"[a-zA-Z0-9_:']+"),
            ("WS", r"\s+"),
        ]
        tok_regex = "|".join(
            "(?P<%s>%s)" % pair for pair in token_specification
        )
        return [m for m in re.finditer(tok_regex, s)]

    def _get_current_token_if_possible(self) -> Optional[re.Match[str]]:
        return (
            self.tokens[self.token_idx]
            if self.token_idx < self.tokens_length
            else None
        )

    def _read_token(
        self, expected_type: Optional[str] = None
    ) -> re.Match[str]:
        """
        Reads current token, verifies result, and increments token index
        """
        token = self._get_current_token_if_possible()
        if not token:
            raise DSLError("Unexpected end of query")
        if expected_type and token.lastgroup != expected_type:
            raise DSLError(f"Expected {expected_type}, got {token.lastgroup}")
        self.token_idx += 1
        return token

    def _get_next_meaningful_token(self) -> Optional[re.Match[str]]:
        current_token = self._get_current_token_if_possible()
        while current_token and current_token.lastgroup == "WS":
            self._read_token("WS")
            current_token = self._get_current_token_if_possible()
        return current_token

    def _resolve_tag(self, tag_name) -> Q:
        """
        Returns Q object with tag, or exception if not found
        """
        alias = (
            ml_models.TagAlias.objects.filter(title=tag_name)
            .select_related("tag")
            .first()
        )
        if alias:
            tag = alias.tag
            subquery = ml_models.Content.objects.filter(tags=tag).values("pk")
            return Q(pk__in=subquery)
        raise DSLError(f"Not found tag '{tag_name}'")

    def parse(self):
        if not self.tokens:
            raise DSLError("Query is empty. Nothing to parse.")
        return self._parse_expression()

    def _parse_expression(self) -> Q:
        node = self._parse_and()
        current_token = self._get_next_meaningful_token()
        while current_token is not None and current_token.lastgroup == "OR":
            self._read_token("OR")
            node |= self._parse_and()
            current_token = self._get_next_meaningful_token()
        return node

    def _parse_and(self) -> Q:
        node = self._parse_negate()
        current_token = self._get_next_meaningful_token()
        while current_token is not None and current_token.lastgroup == "AND":
            self._read_token("AND")
            node &= self._parse_negate()
            current_token = self._get_next_meaningful_token()
        return node

    def _parse_spaceless_tag(self):
        return self._resolve_tag(self._read_token("TAG").group().strip())

    def _parse_unary_negation(self) -> Q:
        current_token = self._get_current_token_if_possible()

        if current_token and current_token.lastgroup == "UNARY_NOT":
            self._read_token("UNARY_NOT")
            return ~self._parse_spaceless()

        return self._parse_spaceless()

    def _parse_negate(self) -> Q:
        current_token = self._get_next_meaningful_token()

        if current_token and current_token.lastgroup == "EXPLICIT_NOT":
            self._read_token("EXPLICIT_NOT")
            return ~self._parse_primary()

        return self._parse_primary()

    def _parse_primary(self) -> Q:
        """
        Recursively parse DSL expression
        """
        token = self._get_current_token_if_possible()

        if not token:
            raise DSLError("Unexpected end of query")

        if token.lastgroup == "L_PAREN":
            self._read_token("L_PAREN")
            node = self._parse_expression()
            self._read_token("R_PAREN")
            return node
        elif token.lastgroup == "L_BRACE":
            self._read_token("L_BRACE")
            return self._parse_group("R_BRACE", mode="AND")
        elif token.lastgroup == "L_BRACKET":
            self._read_token("L_BRACKET")
            return self._parse_group("R_BRACKET", mode="OR")

        return self._consume_complex_tag()

    def _parse_spaceless(self) -> Q:
        """
        Recursively parse DSL expression
        """
        token = self._get_current_token_if_possible()
        if not token:
            raise DSLError("Unexpected end of query")

        elif token.lastgroup == "L_BRACE":
            self._read_token("L_BRACE")
            return self._parse_group("R_BRACE", mode="AND")
        elif token.lastgroup == "L_BRACKET":
            self._read_token("L_BRACKET")
            return self._parse_group("R_BRACKET", mode="OR")

        return self._parse_spaceless_tag()

    def _consume_complex_tag(self) -> Q:
        """
        process tag with space character and returns Q object
        """
        name_parts: list[str] = []
        current_token = self._get_current_token_if_possible()
        while current_token:
            if current_token and current_token.lastgroup in ("TAG", "WS"):
                name_parts.append(self._read_token().group())
                current_token = self._get_current_token_if_possible()
            else:
                break

        full_name = "".join(name_parts).strip()
        if not full_name:
            raise DSLError("Empty tag name")
        return self._resolve_tag(full_name)

    def _parse_group(self, close_type, mode="AND") -> Q:
        """
        Parse special groups and returns Q object
        """
        nodes = []
        current_token = self._get_current_token_if_possible()
        while (
            current_token is not None and current_token.lastgroup != close_type
        ):
            if current_token and current_token.lastgroup == "WS":
                self._read_token("WS")
                current_token = self._get_current_token_if_possible()
                continue

            nodes.append(self._parse_unary_negation())

            current_token = self._get_current_token_if_possible()

        self._read_token(close_type)
        if not nodes:
            return Q()

        res = nodes[0]
        for next_node in nodes[1:]:
            if mode == "AND":
                res &= next_node
            else:
                res |= next_node
        return res
