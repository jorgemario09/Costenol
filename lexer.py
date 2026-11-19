"""
Lexer (Analizador Léxico) para el lenguaje Costeñol.
Descompone el código fuente en tokens de izquierda a derecha.
"""
import re

class Token:
    """Representa un token del lenguaje Costeñol."""
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, L{self.line}:C{self.column})"


class Lexer:
    """
    Analizador léxico del lenguaje Costeñol.
    """
    RESERVED_WORDS = {
        'Si', 'Sino', 'FinSi',
        'Entero', 'Real', 'Logico', 'Texto',
        'Verdadero', 'Falso',
        'Mientras', 'FinMientras',
    }

    TOKEN_SPEC = [
        ('COMMENT',       r'//.*?//'),
        ('KEYWORD_SI',    r'\bSi\b'),
        ('KEYWORD_SINO',  r'\bSino\b'),
        ('KEYWORD_FINSI', r'\bFinSi\b'),
        ('KEYWORD_MIENTRAS',    r'\bMientras\b'),
        ('KEYWORD_FINMIENTRAS', r'\bFinMientras\b'),
        ('TYPE',          r'\b(Entero|Real|Logico|Texto)\b'),
        ('CAPTURA',       r'\bCaptura\.(Entero|Real|Logico|Texto)\b'),
        ('MENSAJE',       r'\bMensaje\.Texto\b'),
        ('BOOL',          r'\b(Verdadero|Falso)\b'),
        ('REAL',          r'\d+[,]\d+'),
        ('INT',           r'\d+'),
        ('STRING',        r'"[^"]*"'),
        ('ID',            r'[A-Za-z_][A-Za-z0-9_]*'),
        ('OP_REL',        r'==|!=|<=|>=|<|>'),
        ('ASSIGN',        r'='),
        ('SEMI',          r';'),
        ('LPAREN',        r'\('),
        ('RPAREN',        r'\)'),
        ('OP_ARITH',      r'[+\-*/]'),
        ('DOLLAR',        r'\$'),
        
        # --- REGLA GLOBAL ESTRICTA DE ESPACIADO ---
        ('MULTI_SPACE',   r'[ \t]{2,}'), # Atrapa 2 o más espacios en cualquier línea de código
        ('SKIP',          r'[ \t]'),
        
        ('NEWLINE',       r'\n'),
        ('MISMATCH',      r'.'),
    ]

    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.errors = []

    def tokenize(self):
        line_num = 1
        line_start = 0
        regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_SPEC)

        for match in re.finditer(regex, self.code, re.DOTALL):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start + 1

            if kind == 'MULTI_SPACE':
                if column == 1:
                    continue
                else:
                    self.errors.append(
                        f"¡Ponte mosca! Línea {line_num}, columna {column}: "
                        f"Metiste demasiados espacios juntos. El Costeñol es estricto, usa solo UN (1) espacio para separar las palabras."
                    )
            elif kind == 'SKIP':
                continue

            elif kind == 'NEWLINE':
                line_num += 1
                line_start = match.end()

            elif kind == 'COMMENT':
                newlines = value.count('\n')
                line_num += newlines
                if newlines > 0:
                    line_start = match.start() + value.rfind('\n') + 1

            # ---> AQUÍ ATRAPAMOS EL ERROR DEL "Si(" PEGADO <---
            elif kind in ('KEYWORD_SI', 'KEYWORD_MIENTRAS'):
                end_pos = match.end()
                # Si justo después de la palabra sigue el paréntesis, falta el espacio
                if end_pos < len(self.code) and self.code[end_pos] == '(':
                    self.errors.append(
                        f"¡Ey llave! Línea {line_num}, columna {column}: "
                        f"Te comiste el espacio obligatorio después del '{value}'. El manual manda que vaya separado del paréntesis: '{value} ('."
                    )
                self.tokens.append(Token(kind, value, line_num, column))

            elif kind in ('KEYWORD_SINO', 'KEYWORD_FINSI', 'KEYWORD_FINMIENTRAS'):
                self.tokens.append(Token(kind, value, line_num, column))

            elif kind == 'MISMATCH':
                if value == ':':
                    self.errors.append(
                        f"¡Eche! Línea {line_num}, columna {column}: ¿Y este garabato ':' de dónde salió? Borra eso llave, recuerda que lo correcto es terminar la instrucción con punto y coma ';'."
                    )
                    self.tokens.append(Token('SEMI', ';', line_num, column))
                else:
                    self.errors.append(
                        f"¡Eche! Línea {line_num}, columna {column}: ¿Y este garabato '{value}' de dónde salió? Borra eso, llave."
                    )

            elif kind == 'ID':
                lower_val = value.lower()
                reserved_map = {w.lower(): w for w in self.RESERVED_WORDS}

                if lower_val in reserved_map and value != reserved_map[lower_val]:
                    correct = reserved_map[lower_val]
                    self.errors.append(
                        f"¡No joda cuadro! Línea {line_num}, columna {column}: "
                        f"Escribiste '{value}'. La vuelta exacta es: '{correct}'. "
                        f"¡Las palabras reservadas y los tipos de datos van con su mayúscula, no seas flojo!"
                    )
                    
                    token_type = 'ID'
                    if correct in ('Entero', 'Real', 'Logico', 'Texto'): token_type = 'TYPE'
                    elif correct in ('Si', 'Sino', 'FinSi', 'Mientras', 'FinMientras'): 
                        token_type = 'KEYWORD_' + correct.upper()
                    elif correct in ('Verdadero', 'Falso'): token_type = 'BOOL'
                    
                    self.tokens.append(Token(token_type, correct, line_num, column))
                else:
                    self.tokens.append(Token(kind, value, line_num, column))

            else:
                if kind == 'REAL':
                    value = value.replace(',', '.')
                self.tokens.append(Token(kind, value, line_num, column))

        return self.tokens, self.errors