"""
Parser (Analizador Sintáctico) para el lenguaje Costeñol.
Construye un AST (Árbol de Sintaxis Abstracta) a partir de los tokens.
"""

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        self.symbol_table = {}  # nombre -> tipo

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        self.pos += 1

    def peek_type(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].type
        return None

    def peek_token(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def parse(self):
        statements = []
        while self.current_token() is not None:
            old_pos = self.pos
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            else:
                if self.pos == old_pos and self.current_token() is not None:
                    self.advance()
        return statements, self.errors

    def parse_statement(self):
        tok = self.current_token()
        if not tok:
            return None

        if tok.type == 'ID' and self.peek_type(1) == 'TYPE':
            return self.parse_declaration()
        elif tok.type == 'MENSAJE':
            return self.parse_mensaje()
        elif tok.type == 'ID' and self.peek_type(1) == 'ASSIGN':
            return self.parse_assignment()
        elif tok.type == 'KEYWORD_SI':
            return self.parse_if()
        elif tok.type == 'KEYWORD_MIENTRAS':
            return self.parse_while()
            
        elif tok.type == 'SEMI':
            self.advance()
            return None

        elif tok.type == 'ID':
            next_tok = self.peek_token(1)
            
            if next_tok and next_tok.type == 'SEMI':
                self.errors.append(
                    f"¡Tronco e' bololó! Línea {tok.line}, columna {tok.column}: "
                    f"Escribiste '{tok.value}' y terminaste la instrucción de un solo machetazo. ¡Pilas! Seguro te comiste el espacio para separar la variable de su tipo de dato (ej. suma Entero;), o te faltó asignarle algo con '='."
                )
                self.advance()
                self.advance()
                return None
            elif next_tok:
                self.errors.append(
                    f"¡Tronco e' bololó! Línea {tok.line}, columna {tok.column}: "
                    f"Me saliste con '{tok.value}' seguido de '{next_tok.value}'. "
                    f"¿Te comiste el '=' de asignación o la declaración del tipo de dato?"
                )
            else:
                self.errors.append(
                    f"¡Ey llave! Línea {tok.line}, columna {tok.column}: "
                    f"Instrucción mocha. Dejaste '{tok.value}' tirao a la mitad."
                )
            return None
        else:
            self.errors.append(
                f"¡Mandas cáscara! Línea {tok.line}, columna {tok.column}: "
                f"No reconozco '{tok.value}'. ¿Qué inventas ahí?"
            )
            return None

    def parse_declaration(self):
        var_tok = self.current_token()
        self.advance()
        type_tok = self.current_token()
        self.advance()

        var_name = var_tok.value
        var_type = type_tok.value

        if var_name in self.symbol_table:
            self.errors.append(
                f"¡Pilas compa! Línea {var_tok.line}, columna {var_tok.column}: "
                f"La variable '{var_name}' ya la habías soltado antes. Busca otra."
            )
        else:
            self.symbol_table[var_name] = var_type

        self.expect('SEMI', f"¡Te volaste el punto y coma ';' al final de '{var_name}'! Ponlo pa' que sirva.")
        return ('DECL', var_name, var_type, var_tok.line)

    def parse_assignment(self):
        var_tok = self.current_token()
        self.advance()
        self.advance()

        var_name = var_tok.value

        if var_name not in self.symbol_table:
            self.errors.append(
                f"¡Se te fueron las luces! Línea {var_tok.line}: "
                f"La variable '{var_name}' no existe. Declárala primero, haz la vuelta bien: '{var_name} Tipo;'"
            )

        val_tok = self.current_token()
        if val_tok and val_tok.type == 'CAPTURA':
            cap_type = val_tok.value.split('.')[1]
            self.advance()

            if var_name in self.symbol_table:
                declared_type = self.symbol_table[var_name]
                if cap_type != declared_type:
                    self.errors.append(
                        f"¡Barro eso! Línea {var_tok.line}: "
                        f"Pusiste que '{var_name}' es de tipo '{declared_type}' y le quieres zampa un '{cap_type}'. ¡Nada que ver!"
                    )

            self.expect('LPAREN', "¡Pilas! Te comiste el '(' de la Captura.")
            self.expect('RPAREN', "¡Eche! Cierra el paréntesis ')' del comando Captura.")
            self.expect('SEMI', "Falta el ';' al final de la Captura, llave.")
            return ('ASSIGN_CAPTURA', var_name, cap_type, var_tok.line)

        expr_node = self.parse_expression()

        if var_name in self.symbol_table and expr_node:
            declared_type = self.symbol_table[var_name]
            expr_type = self._infer_expr_type(expr_node)
            if expr_type and not self._types_compatible(declared_type, expr_type):
                self.errors.append(
                    f"¡Ey cuadro, relájate! Línea {var_tok.line}: "
                    f"'{var_name}' es de tipo '{declared_type}' y le quieres embutir un valor '{expr_type}'. ¡Corrige eso!"
                )

        self.expect('SEMI', "¡Te comiste el ';' al final de la asignación!")
        return ('ASSIGN_EXPR', var_name, expr_node, var_tok.line)

    def parse_mensaje(self):
        msg_tok = self.current_token()
        self.advance()
        self.expect('LPAREN', "Falta abrir el '(' después del Mensaje.")
        expr_node = self.parse_expression()
        self.expect('RPAREN', "¡Cierra el paréntesis ')' del Mensaje, no lo dejes tirao!")
        self.expect('SEMI', "Te volaste el ';' al final del Mensaje.")
        return ('MENSAJE', expr_node, msg_tok.line)

    def parse_if(self):
        si_tok = self.current_token()
        self.advance()

        self.expect('LPAREN', "Abre el paréntesis '(' para meter la condición del Si.")
        cond_node = self.parse_expression()
        self.expect('RPAREN', "¡Llave, cierra el ')' de la condición del Si!")

        # --- VALIDACIÓN ESTRICTA: EL SI NO LLEVA PUNTO Y COMA ---
        next_tok = self.current_token()
        if next_tok and next_tok.type == 'SEMI':
            self.errors.append(
                f"¡Eche compa! Línea {next_tok.line}, columna {next_tok.column}: "
                f"¿Y ese punto y coma ';' al final del 'Si'? Las condicionales no llevan ';' al final. Borra eso, llave."
            )
            self.advance() # Consumir y descartar el ';' mal puesto

        then_branch = []
        while self.current_token() and self.current_token().type not in ('KEYWORD_SINO', 'KEYWORD_FINSI'):
            stmt = self.parse_statement()
            if stmt:
                then_branch.append(stmt)
            else:
                if self.current_token() and self.current_token().type not in ('KEYWORD_SINO', 'KEYWORD_FINSI'):
                    self.advance()

        else_branch = []
        if self.current_token() and self.current_token().type == 'KEYWORD_SINO':
            self.advance()
            while self.current_token() and self.current_token().type != 'KEYWORD_FINSI':
                stmt = self.parse_statement()
                if stmt:
                    else_branch.append(stmt)
                else:
                    if self.current_token() and self.current_token().type != 'KEYWORD_FINSI':
                        self.advance()

        self.expect('KEYWORD_FINSI', "Todo bloque 'Si' debe cerrarse con 'FinSi', no dejes la vaina mocha.")
        return ('IF', cond_node, then_branch, else_branch, si_tok.line)

    def parse_while(self):
        while_tok = self.current_token()
        self.advance()

        self.expect('LPAREN', "Abre el '(' después de Mientras.")
        cond_node = self.parse_expression()
        self.expect('RPAREN', "¡Pilas, cierra el ')' en la condición del Mientras!")

        body = []
        while self.current_token() and self.current_token().type != 'KEYWORD_FINMIENTRAS':
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            else:
                if self.current_token() and self.current_token().type != 'KEYWORD_FINMIENTRAS':
                    self.advance()

        self.expect('KEYWORD_FINMIENTRAS', "Ponle 'FinMientras' al final del bucle pa' que termine el bololó.")
        return ('WHILE', cond_node, body, while_tok.line)

    def parse_expression(self):
        return self.parse_relational()

    def parse_relational(self):
        left = self.parse_addition()
        while self.current_token() and self.current_token().type == 'OP_REL':
            op_tok = self.current_token()
            op = op_tok.value
            self.advance()
            right = self.parse_addition()
            left = ('BINOP', op, left, right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.current_token() and self.current_token().type == 'OP_ARITH' and self.current_token().value in ('+', '-'):
            op = self.current_token().value
            self.advance()
            right = self.parse_multiplication()
            left = ('BINOP', op, left, right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.current_token() and self.current_token().type == 'OP_ARITH' and self.current_token().value in ('*', '/'):
            op = self.current_token().value
            self.advance()
            right = self.parse_unary()
            left = ('BINOP', op, left, right)
        return left

    def parse_unary(self):
        tok = self.current_token()
        if tok and tok.type == 'OP_ARITH' and tok.value == '-':
            self.advance()
            operand = self.parse_primary()
            return ('UNARY_NEG', operand)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current_token()
        if not tok: return None

        if tok.type == 'STRING':
            self.advance()
            return ('STRING', tok.value[1:-1])
        elif tok.type == 'INT':
            self.advance()
            return ('INT', int(tok.value))
        elif tok.type == 'REAL':
            self.advance()
            return ('REAL', float(tok.value.replace(',', '.')))
        elif tok.type == 'BOOL':
            self.advance()
            return ('BOOL', tok.value == 'Verdadero')
        elif tok.type == 'ID':
            self.advance()
            if tok.value not in self.symbol_table:
                self.errors.append(
                    f"¡Se te fueron las luces! Línea {tok.line}, columna {tok.column}: "
                    f"La variable '{tok.value}' no está declarada."
                )
            return ('VAR', tok.value)
        elif tok.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN', "Falta cerrar el paréntesis ')'.")
            return expr
        elif tok.type == 'DOLLAR':
            self.advance()
            next_tok = self.current_token()
            if next_tok and next_tok.type == 'ID':
                self.advance()
                if next_tok.value not in self.symbol_table:
                    self.errors.append(f"¡Ey! Línea {next_tok.line}: La variable '{next_tok.value}' no la conozco.")
                return ('VAR', next_tok.value)
            else:
                self.errors.append(f"Línea {tok.line}: ¿Y la variable después del '$' qué?")
                return None
        else:
            self.errors.append(f"¡Qué locura! Línea {tok.line}: Expresión no válida '{tok.value}'.")
            self.advance()
            return None

    def expect(self, token_type, error_msg):
        tok = self.current_token()
        if tok and tok.type == token_type:
            self.advance()
            return True
        else:
            line = tok.line if tok else '(final del archivo)'
            col = tok.column if tok else ''
            loc = f"Línea {line}" + (f", columna {col}" if col else "")
            self.errors.append(f"{loc}: {error_msg}")
            return False

    def _infer_expr_type(self, node):
        if node is None: return None
        node_type = node[0]
        if node_type == 'STRING': return 'Texto'
        elif node_type == 'INT': return 'Entero'
        elif node_type == 'REAL': return 'Real'
        elif node_type == 'BOOL': return 'Logico'
        elif node_type == 'VAR': return self.symbol_table.get(node[1])
        elif node_type == 'BINOP':
            op = node[1]
            if op in ('==', '!=', '<', '>', '<=', '>='): return 'Logico'
            left_type = self._infer_expr_type(node[2])
            right_type = self._infer_expr_type(node[3])
            if left_type == 'Texto' or right_type == 'Texto': return 'Texto'
            if left_type == 'Real' or right_type == 'Real': return 'Real'
            return left_type
        elif node_type == 'UNARY_NEG':
            return self._infer_expr_type(node[1])
        return None

    def _types_compatible(self, declared, inferred):
        if declared == inferred: return True
        if declared == 'Real' and inferred == 'Entero': return True
        if declared == 'Texto' and inferred == 'Texto': return True
        return False