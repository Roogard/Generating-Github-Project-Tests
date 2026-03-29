def maybe_remove_trailing_comma(self, closing: Leaf) -> bool:
        """Remove trailing comma if there is one and it's safe."""
        if not (
            self.leaves
            and self.leaves[-1].type == token.COMMA
            and closing.type in CLOSING_BRACKETS
        ):
            return False

        if closing.type == token.RBRACE:
            self.remove_trailing_comma()
            return True

        if closing.type == token.RSQB:
            comma = self.leaves[-1]
            if comma.parent and comma.parent.type == syms.listmaker:
                self.remove_trailing_comma()
                return True

        # For parens let's check if it's safe to remove the comma.
        # Imports are always safe.
        if self.is_import:
            self.remove_trailing_comma()
            return True

        # Otherwise, if the trailing one is the only one, we might mistakenly
        # change a tuple into a different type by removing the comma.
        depth = closing.bracket_depth + 1
        commas = 0
        opening = closing.opening_bracket
        for _opening_index, leaf in enumerate(self.leaves):
            if leaf is opening:
                break

        else:
            return False

        for leaf in self.leaves[_opening_index + 1 :]:
            if leaf is closing:
                break

            bracket_depth = leaf.bracket_depth
            if bracket_depth == depth and leaf.type == token.COMMA:
                commas += 1
                if leaf.parent and leaf.parent.type == syms.arglist:
                    commas += 1
                    break

        if commas > 1:
            self.remove_trailing_comma()
            return True

        return False