# ------------------------------------------- BIBLIOTECAS -------------------------------------------
import sys
import sqlite3
import locale
import re
from contextlib import suppress
from datetime import datetime
from tkinter import Image
from PyQt5 import QtWidgets, QtGui, QtCore
from babel.numbers import format_currency
import csv
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
from PyQt5.QtGui import QIntValidator, QDoubleValidator
# ------------------------------------------- FIM BIBLIOTECAS -------------------------------------------




# ------------------------------------------- VALIDAÇÕES -----------------------------------------------
with suppress(locale.Error):
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

# ------------------- FUNÇÃO DE FORMATAÇÃO -------------------
def format_currency(value) -> str:
    """Formata um valor numérico em moeda brasileira (R$)."""
    try:
        # garante que seja numérico
        value = float(value)
        return locale.currency(value, grouping=True)
    except (TypeError, ValueError):
        return "R$ 0,00"
    except Exception:
        # fallback manual
        s = f"{value:,.2f}"
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

# ----------- FORMATA TELEFONE PARA (XX) XXXXX-XXXX OU (XX) XXXX-XXXX -----------
def format_phone(phone: str) -> str:
    """Formata um número de telefone brasileiro."""
    if not phone:
        return ""
    
    digits = re.sub(r"\D", "", str(phone))  # remove tudo que não for dígito

    if len(digits) == 11:  # celular
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:  # fixo
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    
    # fallback: retorna como digitado
    return phone
# ------------------------------------------- FIM VALIDAÇÕES -----------------------------------------------




# -------------------------------------------------- VERSÃO ------------------------------------------------
def load_version():
    try:
        with open("version.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"  # fallback caso não exista

APP_VERSION = load_version()
# ------------------------------------------------ FIM VERSÃO ------------------------------------------------





# --------------------------------------------- BANCO DE DADOS ---------------------------------------------
conn = sqlite3.connect('crud_login.db')
cursor = conn.cursor()

def ensure_users_table():
    # cria tabela users se não existir (com campo role)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
    ''')
    conn.commit()

    # se a tabela existia mas não tem a coluna role, adiciona-a
    cursor.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'role' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        conn.commit()

ensure_users_table()



# ------------------- TABELA PRODUTOS -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_total REAL NOT NULL,
    brand_id INTEGER REFERENCES brands(id)
)
''')
conn.commit()


# ------------------TABELA MARCAS --------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')
conn.commit()


# ------------------ TABELA VENDEDORES -----------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS sellers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    commission_pct REAL DEFAULT 5,
    phone TEXT,
    cpf TEXT NOT NULL UNIQUE
)
''')
conn.commit()



# ------------------- TABELA VENDAS -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    total REAL NOT NULL,
    date TEXT NOT NULL,
    commission_pct REAL DEFAULT 5,
    payment_method TEXT DEFAULT '—',
    installments INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'Pendente',
    FOREIGN KEY(client_id) REFERENCES clients(id),
    FOREIGN KEY(seller_id) REFERENCES sellers(id)
    
)
''')
conn.commit()



# ------------------- TABELA ITENS DE VENDA -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    subtotal REAL
)
''')
conn.commit()



# ------------------- TABELA CLIENTES -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    aniversary DATE          
)
''')



# usuário padrão admin (com role)
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '1234', 'admin'))
    conn.commit()
# ----------------------------------------- FIM BANCO DE DADOS ---------------------------------------------




# --------------------------------------- COMPONENTES VISUAIS ---------------------------------------------
class HoverShadowEffect(QtWidgets.QGraphicsDropShadowEffect):
    # Efeito de sombra animada ao passar o mouse.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBlurRadius(12)
        self.setOffset(0, 3)
        self.setColor(QtGui.QColor(0, 0, 0, 60))

        # animações para blur e offset
        self.anim = QtCore.QPropertyAnimation(self, b"blurRadius")
        self.anim.setDuration(200)
        self.offset_anim = QtCore.QPropertyAnimation(self, b"yOffset")
        self.offset_anim.setDuration(200)

    def enterEvent(self, event):
        # Anima ao passar o mouse.
        self.anim.stop()
        self.anim.setStartValue(self.blurRadius())
        self.anim.setEndValue(28)
        self.anim.start()

        self.offset_anim.stop()
        self.offset_anim.setStartValue(self.yOffset())
        self.offset_anim.setEndValue(8)
        self.offset_anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        # Volta ao estado inicial ao sair com o mouse.
        self.anim.stop()
        self.anim.setStartValue(self.blurRadius())
        self.anim.setEndValue(12)
        self.anim.start()

        self.offset_anim.stop()
        self.offset_anim.setStartValue(self.yOffset())
        self.offset_anim.setEndValue(3)
        self.offset_anim.start()

        super().leaveEvent(event)
# --------------------------------------- FIM COMPONENTES VISUAIS ---------------------------------------------




# -------------------------------------------------- LOGIN ----------------------------------------------------
class LoginWindow(QtWidgets.QWidget):
    """Janela de login do sistema corporativo."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Sistema Corporativo")
        self.setGeometry(420, 160, 540, 460)
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        self.setup_ui()

    def setup_ui(self):
        # -------- LAYOUT PRINCIPAL --------
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 10, 20, 30)

        # -------- BOTÃO SAIR (TOPO DIREITO) --------
        self.exit_button = QtWidgets.QPushButton(self)
        self.exit_button.setFixedSize(36, 36)
        self.exit_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.exit_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton))
        self.exit_button.setIconSize(QtCore.QSize(18, 18))
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color:#c0392b;
                border-radius:18px;
            }
            QPushButton:hover { background-color:#e74c3c; }
            QPushButton:pressed { background-color:#a93226; }
        """)
        self.exit_button.clicked.connect(QtWidgets.QApplication.quit)

        # layout do botão sair
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(self.exit_button)
        layout.addLayout(top_layout)

        # -------- LOGO --------
        pixmap = QtGui.QPixmap("icons/logo.png")
        self.logo_label = QtWidgets.QLabel()
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(180, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)

        # -------- CAMPOS --------
        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("Usuário")
        self.username.setStyleSheet("""
            padding:12px; font-size:14px; border-radius:10px;
            border:1px solid #d0d7de; background:#fff; color:#2c3e50;
        """)

        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("Senha")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setStyleSheet("""
            padding:12px; font-size:14px; border-radius:10px;
            border:1px solid #d0d7de; background:#fff; color:#2c3e50;
        """)

        self.login_button = QtWidgets.QPushButton("Entrar")
        self.login_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color:#2980b9; color:white; font-size:15px; padding:12px;
                border-radius:10px; font-weight:700;
            }
            QPushButton:hover { background-color:#2e8ece; }
            QPushButton:pressed { background-color:#2574a9; }
        """)
        self.login_button.clicked.connect(self.login)

        # 🎨 aplica efeito de sombra animada no botão de login
        shadow_effect = HoverShadowEffect(self.login_button)
        self.login_button.setGraphicsEffect(shadow_effect)

        self.message = QtWidgets.QLabel("")
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.message.setStyleSheet("color:#ffd3d3; font-weight:bold;")

        # adicionar widgets
        layout.addWidget(self.logo_label)
        layout.addSpacing(6)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_button)
        layout.addWidget(self.message)

        self.setLayout(layout)

        # ENTER ativa login
        self.username.returnPressed.connect(self.login)
        self.password.returnPressed.connect(self.login)

    # ------------------- LÓGICA DE LOGIN -------------------
    def check_credentials(self, username: str, password: str):
        """Valida credenciais no banco de dados."""
        try:
            cursor.execute(
                "SELECT id, username, role FROM users WHERE username=? AND password=?",
                (username, password),
            )
            return cursor.fetchone()
        except Exception as e:
            print("Erro ao validar login:", e)
            return None

    def login(self):
        user = self.username.text().strip()
        pw = self.password.text().strip()
        row = self.check_credentials(user, pw)

        if row:
            user_info = {"id": row[0], "username": row[1], "role": row[2]}
            self.main = JanelaPrincipal(user_info)
            self.main.showMaximized()
            self.close()
        else:
            self.message.setText("Usuário ou senha incorretos")
#---------------------------------------------- FIM LOGIN ------------------------------------------------------




# ---------------------------------------- DASHBOARD COMPLETO --------------------------------------------------
def format_currency(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(value)


def format_date(value):
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except Exception:
        return str(value)


class InfoCard(QtWidgets.QFrame):
    def __init__(self, title, value, color="#3498db"):
        super().__init__()
        self.title = title
        self.value = value
        self.base_color = color

        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.base_color};
                border-radius: 12px;
                color: white;
            }}
        """)

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setContentsMargins(16, 16, 16, 16)
        self.vbox.setSpacing(6)

        self.lbl_title = QtWidgets.QLabel(title)
        self.lbl_title.setStyleSheet("font-size:14px; font-weight:600;")
        self.lbl_title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.vbox.addWidget(self.lbl_title)

        self.lbl_value = QtWidgets.QLabel(str(value))
        self.lbl_value.setStyleSheet("font-size:24px; font-weight:700;")
        self.lbl_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.vbox.addWidget(self.lbl_value)

        self.effect_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.effect_shadow.setBlurRadius(15)
        self.effect_shadow.setOffset(0, 4)
        self.effect_shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self.effect_shadow)

        self.setCursor(QtCore.Qt.PointingHandCursor)

    # Hover
    def enterEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._lighten_color(self.base_color, 30)};
                border-radius: 12px;
                color: white;
            }}
        """)
        self.effect_shadow.setBlurRadius(25)
        self.effect_shadow.setOffset(0, 8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.base_color};
                border-radius: 12px;
                color: white;
            }}
        """)
        self.effect_shadow.setBlurRadius(15)
        self.effect_shadow.setOffset(0, 4)
        super().leaveEvent(event)


    # Atualizar valor
    def atualizar_valor(self, new_value):
        # Se for datetime ou string no formato de data → converte para dd/mm/aaaa
        from datetime import datetime

        if isinstance(new_value, str):
            try:
                # tenta converter '2025-09-25' ou '2025-09-25 14:32:11'
                dt = datetime.fromisoformat(new_value)
                self.lbl_value.setText(dt.strftime("%d/%m/%Y"))
                return
            except Exception:
                pass

        elif isinstance(new_value, datetime):
            self.lbl_value.setText(new_value.strftime("%d/%m/%Y"))
            return

        # Se não for data → mostra direto
        self.lbl_value.setText(str(new_value))


    def _update_label(self, val, final_val):
        if isinstance(final_val, float):
            self.lbl_value.setText(format_currency(val))
        else:
            self.lbl_value.setText(str(int(val)))

    def _lighten_color(self, hex_color, amount=30):
        col = QtGui.QColor(hex_color)
        r = min(col.red() + amount, 255)
        g = min(col.green() + amount, 255)
        b = min(col.blue() + amount, 255)
        return f"rgb({r},{g},{b})"
    
    
class DashboardWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.outer = QtWidgets.QVBoxLayout(self)
        self.outer.setAlignment(QtCore.Qt.AlignTop)
        self.outer.setSpacing(20)
        self.outer.setContentsMargins(20, 16, 20, 20)
        self.setStyleSheet("background-color: #f8f9fa;")

        title = QtWidgets.QLabel("Dashboard")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:28px; font-weight:700; color:#2c3e50;")
        self.outer.addWidget(title)

        self.grid_general = QtWidgets.QGridLayout()
        self.grid_general.setSpacing(20)
        self.grid_sales = QtWidgets.QGridLayout()
        self.grid_sales.setSpacing(20)

        # Inicializa cards
        self._init_general_cards()
        self._init_sales_cards()

        wrapper_general = QtWidgets.QWidget()
        wrapper_general.setLayout(self.grid_general)
        wrapper_general.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.outer.addWidget(wrapper_general)

        wrapper_sales = QtWidgets.QWidget()
        wrapper_sales.setLayout(self.grid_sales)
        wrapper_sales.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.outer.addWidget(wrapper_sales)

        self.tip_label = QtWidgets.QLabel(
            "💡 Dica: Clique nos cards para ver detalhes ou atualize os dados para informações recentes."
        )
        self.tip_label.setAlignment(QtCore.Qt.AlignCenter)
        self.tip_label.setStyleSheet("font-size:12px; color:#7f8c8d; padding:6px;")
        self.outer.addWidget(self.tip_label)
        self.outer.addStretch(1)

        self.installEventFilter(self)
        self._connect_card_clicks()
    

    # ---------------- Função de soma comissão ----------------
    def _sum_commission(self):
        cursor.execute("""
            SELECT s.total, se.commission_pct
            FROM sales s
            JOIN sellers se ON s.seller_id = se.id
            WHERE s.status='Pago'
        """)
        rows = cursor.fetchall()
        total = 0
        for total_sale, pct in rows:
            if pct is None:
                pct = 5
            total += total_sale * (pct / 100)
        return total

    # ---------------- Inicializa Cards ----------------
    def _init_general_cards(self):
        self.products_count = self._count("products") # Quantidade de produtos
        self.users_count = self._count("users") # Quantidade de usuário
        self.stock_value = self._sum_price() # Estoque
        self.last_product = self._last("products", "name") # Último produto
        self.last_user = self._last("users", "username") # Último usuário
        self.last_client = self._last("clients", "name") # Último cliente
        self.last_sellers = self._last("sellers", "name") # Último vendedor
        self.total_commission = self._sum_commission() # Total de comissão

        stock_fmt = format_currency(self.stock_value)
        commission_fmt = format_currency(self.total_commission)

        self.card_products = InfoCard("Total de Produtos", self.products_count, "#3498db")
        self.card_users = InfoCard("Total de Usuários", self.users_count, "#2ecc71")
        self.card_stock = InfoCard("Valor total do estoque", stock_fmt, "#9b59b6")
        self.card_last_prod = InfoCard("Último produto cadastrado", self.last_product, "#e67e22")
        self.card_last_user = InfoCard("Último usuário cadastrado", self.last_user, "#16a085")
        self.card_last_client = InfoCard("Último cliente cadastrado", self.last_client, "#f1c40f")
        self.card_last_sellers = InfoCard("Último vendedor cadastrado", self.last_sellers, "#f39c12")
        self.card_total_commission = InfoCard("Total de Comissão", commission_fmt, "#1abc9c")  # Novo card

        self.grid_general.addWidget(self.card_products, 0, 0)
        self.grid_general.addWidget(self.card_users, 0, 1)
        self.grid_general.addWidget(self.card_stock, 0, 2)
        self.grid_general.addWidget(self.card_total_commission, 0, 3)
        self.grid_general.addWidget(self.card_last_prod, 1, 0)
        self.grid_general.addWidget(self.card_last_user, 1, 1)
        self.grid_general.addWidget(self.card_last_client, 1, 2)
        self.grid_general.addWidget(self.card_last_sellers, 1, 3)

    def _init_sales_cards(self):
        self.sales_count = self._count("sales")
        self.sales_total = self._sum_sales()
        self.last_sale = self._last("sales", "id")
        self.top_product = self._top_product()

        self.card_sales_count = InfoCard("Total de Vendas", self.sales_count, "#e74c3c")
        self.card_sales_total = InfoCard("Receita Total", format_currency(self.sales_total), "#d35400")
        self.card_last_sale = InfoCard("Última Venda ID", self.last_sale, "#8e44ad")
        self.card_top_product = InfoCard("Produto Mais Vendido", self.top_product, "#27ae60")

        self.grid_sales.addWidget(self.card_sales_count, 0, 0)
        self.grid_sales.addWidget(self.card_sales_total, 0, 1)
        self.grid_sales.addWidget(self.card_last_sale, 1, 0)
        self.grid_sales.addWidget(self.card_top_product, 1, 1)

    # ---------------- Conecta clique nos cards ----------------
    def _connect_card_clicks(self):
        cards_info = [
            (self.card_products, "Produtos", self._get_products_data, "#d6eaf8"),
            (self.card_users, "Usuários", self._get_users_data, "#d5f5e3"),
            (self.card_stock, "Estoque", self._get_products_data, "#d6eaf8"),
            (self.card_last_prod, "Último Produto", self._get_last_product_data, "#d6eaf8"),
            (self.card_last_user, "Último Usuário", self._get_last_user_data, "#d5f5e3"),
            (self.card_last_client, "Último Cliente", self._get_last_client_data, "#d5f5e3"),
            (self.card_sales_count, "Vendas", self._get_sales_data, "#f5b7b1"),
            (self.card_sales_total, "Receita", self._get_sales_data, "#f5b7b1"),
            (self.card_last_sale, "Última Venda", self._get_last_sale_data, "#f5b7b1"),
            (self.card_top_product, "Produto Mais Vendido", self._get_top_product_data, "#f5b7b1"),
            (self.card_last_sellers,"Último Vendedor", self._get_last_sellers, "#f5b7b1"),
            (self.card_total_commission, "Comissões", self._get_commission_data, "#1abc9c")
        ]
        for card, title, func, color in cards_info:
            if title == "Comissões":
                card.mousePressEvent = lambda e, f=func, t=title, c=color: self._show_modal(
                    f(), t, c, custom_headers=["ID Venda", "Total Venda", "% Comissão", "Valor Comissão", "Data"])
            else:
                card.mousePressEvent = lambda e, f=func, t=title, c=color: self._show_modal(f(), t, c)

    # ---------------- Modal genérico ----------------
    def _show_modal(self, data, title, color="#ffffff", custom_headers=None):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(1000, 600)
        dialog.setMinimumSize(800, 500)
        layout = QtWidgets.QVBoxLayout(dialog)

        if not data:
            layout.addWidget(QtWidgets.QLabel("Nenhum dado disponível."))
            dialog.setLayout(layout)
            dialog.exec_()
            return

        table = QtWidgets.QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(len(data[0]))

        # -------- Mapeamento de cabeçalhos --------
        headers_map = {
            "Produtos": ["Código", "Produto", "Valor Total"],
            "Usuários": ["Código", "Usuário"],
            "Último Produto": ["Código", "Produto", "Preço", "Quantidade", "Valor Total","Marca"],
            "Último Usuário": ["Código", "Usuário", "Perfil"],
            "Último Cliente": ["Código", "Cliente", "Email", "Telefone","Data de Nascimento"],
            "Último Vendedor": ["Código", "Vendedor", "Email", " % Comissão","Telefone", "CPF"],
            "Vendas": ["Código da Venda", "Valor Total", "Data"],
            "Receita": ["Código da Venda", "Valor Total", "Data"],
            "Última Venda": ["Código Venda", "Produto", "Quantidade", "Valor Unitário", "Valor Total", "Data"],
            "Produto Mais Vendido": ["Produto", "Quantidade"],
            "Comissões": ["Código da Venda", "Total Venda", "% Comissão", "Valor Comissão", "Data"],
            "Estoque": ["Código do produto","Produto","Valor Total"]
        }

        if custom_headers:
            headers = custom_headers
        elif title in headers_map:
            headers = headers_map[title]
        elif cursor.description:
            columns = [desc[0] for desc in cursor.description]
            headers = [desc for desc in columns]
        else:
            headers = [f"Coluna {i+1}" for i in range(len(data[0]))]

        table.setHorizontalHeaderLabels(headers)

        # -------- Formatar valores corretamente --------
        money_headers = ("Preço", "Valor", "Valor Unitário", "Valor Total", 
                         "Total", "Total Venda", "Valor Comissão")
        percent_headers = ("Percentual", "% Comissão", "Comissão %")

        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                header = headers[col_idx]

                if header in money_headers:
                    try:
                        txt = format_currency(float(value))
                    except:
                        txt = str(value)
                elif header in percent_headers:
                    txt = str(value) if "%" in str(value) else f"{value}%"
                else:
                    txt = str(value)

                item = QtWidgets.QTableWidgetItem(txt)
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                table.setItem(row_idx, col_idx, item)


        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                gridline-color: #dcdcdc;
                font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: #2c3e50;
                color: #ecf0f1;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #34495e;
            }}
            QTableWidget::item:selected {{
                background-color: #2980b9;
                color: #ffffff;
            }}
        """)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        table.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        table.resizeRowsToContents()
        layout.addWidget(table)

        dialog.setLayout(layout)
        dialog.exec_()

    # ---------------- Funções auxiliares ----------------
    def _count(self, table):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]

    def _sum_price(self):
        cursor.execute("SELECT SUM(valor_total) FROM products")
        val = cursor.fetchone()[0]
        return float(val) if val else 0.0

    def _last(self, table, column):
        cursor.execute(f"SELECT {column} FROM {table} ORDER BY id DESC LIMIT 1")
        res = cursor.fetchone()
        return res[0] if res else "Nenhum"

    def _sum_sales(self):
        cursor.execute("SELECT SUM(total) FROM sales")
        val = cursor.fetchone()[0]
        return float(val) if val else 0.0

    def _top_product(self):
        cursor.execute("""
            SELECT products.name, SUM(sales_items.quantity) as total_qty
            FROM sales_items
            JOIN products ON sales_items.product_id = products.id
            GROUP BY products.id
            ORDER BY total_qty DESC
            LIMIT 1
        """)
        res = cursor.fetchone()
        return res[0] if res else "Nenhum"

    # ---------------- Dados para cards/modais ----------------
    def _get_products_data(self):
        cursor.execute("SELECT id, name, valor_total FROM products ORDER BY id DESC")
        return cursor.fetchall()

    def _get_users_data(self):
        cursor.execute("SELECT id, username FROM users ORDER BY id DESC")
        return cursor.fetchall()

    def _get_last_product_data(self):
        cursor.execute("""
            SELECT p.id, p.name, p.price, p.quantidade, p.valor_total, b.name
            FROM products p
            INNER JOIN brands b ON p.brand_id = b.id
            ORDER BY p.id DESC
            LIMIT 1
        """)
        return cursor.fetchall()

    def _get_last_user_data(self):
        cursor.execute("SELECT id, username, role FROM users ORDER BY id DESC")
        return cursor.fetchall()

    def _get_last_client_data(self):
        cursor.execute("SELECT * FROM clients ORDER BY id DESC LIMIT 1")
        return cursor.fetchall()

    def _get_last_sellers(self):
        cursor.execute("SELECT * FROM sellers ORDER BY id DESC LIMIT 1")
        return cursor.fetchall()

    def _get_sales_data(self):
        cursor.execute("SELECT id, total, date FROM sales ORDER BY id DESC")
        rows = cursor.fetchall()
        formatted = []
        for sale_id, total, date in rows:
            try:
                dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                date = dt.strftime("%d/%m/%Y")
            except:
                pass
            formatted.append((sale_id, format_currency(total), date))
        return formatted

    def _get_last_sale_data(self):
        cursor.execute("""
            SELECT s.id AS SaleID,
                   p.name AS Produto,
                   si.quantity AS Quantidade,
                   p.price AS ValorUnitario,
                   (si.quantity * p.price) AS ValorTotal,
                   s.date AS DataVenda
            FROM sales s
            INNER JOIN sales_items si ON si.sale_id = s.id
            INNER JOIN products p ON si.product_id = p.id
            WHERE s.id = (SELECT id FROM sales ORDER BY id DESC LIMIT 1)
        """)
        results = cursor.fetchall()
        if not results:
            return []

        formatted = []
        for row in results:
            row_list = list(row)
            row_list[3] = format_currency(float(row_list[3]))
            row_list[4] = format_currency(float(row_list[4]))
            try:
                dt = datetime.strptime(row_list[5], "%Y-%m-%d %H:%M:%S")
                row_list[5] = dt.strftime("%d/%m/%Y")
            except:
                pass
            formatted.append(row_list)
        return formatted

    def _get_top_product_data(self):
        cursor.execute("""
            SELECT products.name, SUM(sales_items.quantity) as total_qty
            FROM sales_items
            JOIN products ON sales_items.product_id = products.id
            GROUP BY products.id
            ORDER BY total_qty DESC
            LIMIT 1
        """)
        return cursor.fetchall()

    def _get_commission_data(self):
        cursor.execute("""
            SELECT s.id, s.total, se.commission_pct, s.date
            FROM sales s
            JOIN sellers se ON s.seller_id = se.id
            WHERE s.status='Pago'
        """)
        rows = cursor.fetchall()
        data = []
        for sale_id, total, pct, date in rows:
            if pct is None:
                pct = 5
            try:
                dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                date_fmt = dt.strftime("%d/%m/%Y")
            except:
                date_fmt = str(date)
            data.append((
                sale_id,
                format_currency(total),
                f"{pct:.2f}%",
                format_currency(total * (pct / 100)),
                date_fmt
            ))
        return data

    # ---------------- Atualiza cards ----------------
    def refresh(self):
        self.card_products.atualizar_valor(self._count("products"))
        self.card_users.atualizar_valor(self._count("users"))
        self.card_stock.atualizar_valor(format_currency(self._sum_price()))
        self.card_last_prod.atualizar_valor(self._last("products", "name"))
        self.card_last_user.atualizar_valor(self._last("users", "username"))
        self.card_last_client.atualizar_valor(self._last("clients", "name"))
        self.card_sales_count.atualizar_valor(self._count("sales"))
        self.card_sales_total.atualizar_valor(format_currency(self._sum_sales()))
        self.card_last_sale.atualizar_valor(self._last("sales", "id"))
        self.card_last_sellers.atualizar_valor(self._last("sellers","name"))
        self.card_top_product.atualizar_valor(self._top_product())
        self.card_total_commission.atualizar_valor(format_currency(self._sum_commission()))
        
       
    def eventFilter(self, obj, event):
        if event.type() in (QtCore.QEvent.Show, QtCore.QEvent.WindowActivate):
            self.refresh()
        return super().eventFilter(obj, event)
#---------------------------------------------- FIM DASHBOARD ----------------------------------------------------




# -------------------------------------------- VENDEDORES -----------------------------------------------------
class SellersWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(12)
        self.vbox.setContentsMargins(20, 20, 20, 20)

        self.setup_ui()
        self.load_sellers()

        # Efeito de fade
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QtCore.QPropertyAnimation(self.opacity_effect, b'opacity', self)
        self.fade_anim.setDuration(400)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #d0d7de;
                font-size: 14px;
                gridline-color: #e6e6e6;
                alternate-background-color: #f7f9fc;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #d9ecff;
                color: #1c3f5d;
                border: 1px solid #5dade2;
                border-radius: 4px;
            }

            QTableWidget::item:hover {
                background-color: #eef6ff;
            }

            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-right: 1px solid #1f2d3a;
            }

            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }

            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }

            QScrollBar:vertical {
                width: 10px;
                background: #eef1f4;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #b7c2cc;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #9eabb9;
            }
        """)

    def setup_ui(self):
        # Campo de pesquisa
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar vendedores...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding:10px;
                border:1px solid #dcdcdc;
                border-radius:12px;
                background-color:#f7f9fc;
            }
            QLineEdit:focus {
                border:1.5px solid #3498db;
                background-color:#ffffff;
            }
        """)
        self.vbox.addWidget(self.search_input)

        # Botão de pesquisa
        self.btn_search = self.create_button("Pesquisar", "#2980b9", "#3498db", self.show_and_filter)
        self.vbox.addWidget(self.btn_search)

        # Tabela moderna
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Email", "Telefone", "CPF"])
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color:#2c3e50;
                color:white;
                font-weight:bold;
                font-size:14px;
                border:none;
                padding:10px;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e0e0e0;
                border-radius:8px;
            }
            QTableWidget::item:alternate { background-color: #f4f6f9; }
            QTableWidget::item:selected { background-color: #3498db; color: #ffffff; }
            QTableWidget::item:hover { background-color: #ecf4ff; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.vbox.addWidget(self.table)
        self.table.setVisible(False)  # <<< escondida inicialmente

        # Inputs
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Nome")
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Email")
        email_regex = QtCore.QRegExp(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        self.email_input.setValidator(QtGui.QRegExpValidator(email_regex, self.email_input))
        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Telefone")
        self.cpf_input = QtWidgets.QLineEdit()
        self.cpf_input.setPlaceholderText("CPF (Somente números)")

        # TELEFONE: apenas números com formatação
        phone_regex = QRegExp(r'^\(?\d{0,2}\)?\s?\d{0,5}-?\d{0,4}$')
        self.phone_input.setValidator(QRegExpValidator(phone_regex, self.phone_input))

        # CPF: apenas números, 11 dígitos
        self.cpf_input.setMaxLength(11)
        self.cpf_input.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp(r'\d{0,11}'), self.cpf_input))

        for widget in [self.name_input, self.email_input, self.phone_input, self.cpf_input]:
            widget.setStyleSheet("""
                QLineEdit {
                    padding:8px;
                    border:1px solid #d0d0d0;
                    border-radius:8px;
                    background-color:#f9fafb;
                }
                QLineEdit:focus {
                    border:1.5px solid #3498db;
                    background-color:#ffffff;
                }
            """)

        # Botões
        self.btn_add = self.create_button("Adicionar", "#27ae60", "#2ecc71", self.add_seller)
        self.btn_update = self.create_button("Atualizar", "#f39c12", "#f5a623", self.update_seller)
        self.btn_delete = self.create_button("Excluir", "#c0392b", "#e74c3c", self.delete_seller)
        self.btn_clear = self.create_button("Limpar Campos", "#7f8c8d", "#95a5a6", self.clear_grid)

        # Rodapé de ajuda
        self.lbl_help = QtWidgets.QLabel("💡 Dica: Clique duas vezes no item da grid para carregar os dados para alteração.")
        self.lbl_help.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic; padding:6px;")
        self.lbl_help.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.lbl_help)

        # Layout inputs + botões
        input_h = QtWidgets.QHBoxLayout()
        input_h.setSpacing(10)
        input_h.addWidget(self.name_input, 2)
        input_h.addWidget(self.email_input, 2)
        input_h.addWidget(self.phone_input, 1)
        input_h.addWidget(self.cpf_input, 1)
        input_h.addWidget(self.btn_add)
        input_h.addWidget(self.btn_update)
        input_h.addWidget(self.btn_delete)
        input_h.addWidget(self.btn_clear)

        self.vbox.addLayout(input_h)
        self.table.cellClicked.connect(self.fill_fields_from_table)

        # Permissões
        if self.current_user.get("role") != "admin":
            for btn in [self.btn_add, self.btn_update, self.btn_delete]:
                btn.setEnabled(False)
            for widget in [self.name_input, self.email_input, self.phone_input, self.cpf_input]:
                widget.setReadOnly(True)

    def create_button(self, text, color, hover_color, callback):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{color};
                color:white;
                padding:10px;
                border-radius:8px;
                font-weight:600;
            }}
            QPushButton:hover {{ background-color:{hover_color}; }}
        """)
        btn.clicked.connect(callback)
        return btn

    def get_seller_pct(seller_id):
        cursor.execute("SELECT commission_pct FROM sellers WHERE id=?", (seller_id,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return 5  # padrão 5% caso não for definido.

    # Fade-in
    def showEvent(self, event):
        self.fade_anim.stop()
        self.opacity_effect.setOpacity(0.0)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        super().showEvent(event)

    # Limpar
    def clear_grid(self):
        self.table.clearSelection()
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.cpf_input.clear()

    # Preencher
    def fill_fields_from_table(self, row, column):
        self.name_input.setText(self.table.item(row, 1).text())
        self.email_input.setText(self.table.item(row, 2).text())
        self.phone_input.setText(self.table.item(row, 3).text())
        item = self.table.item(row, 4)
        if item is not None:
            cpf_text = item.text().strip()
            self.cpf_input.setText(cpf_text)
        else:
            self.cpf_input.setText("")

    # Carregar
    def load_sellers(self):
        self.table.setRowCount(0)
        cursor.execute("SELECT id, name, email, phone, cpf FROM sellers")
        for r, row in enumerate(cursor.fetchall()):
            self.table.insertRow(r)
            for c, v in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(v))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(r, c, item)

    # Adicionar
    def add_seller(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = format_phone(self.phone_input.text())
        cpf = self.cpf_input.text().strip()
        if not name or not email or not cpf:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Nome, Email e CPF são obrigatórios!")
            return
        if self.email_input.hasAcceptableInput() is False:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Email inválido!")
            return
        if not cpf.isdigit() or len(cpf) != 11:
            QtWidgets.QMessageBox.warning(self, "Alerta", "CPF inválido! Deve conter 11 dígitos numéricos.")
            return
        cursor.execute("SELECT id FROM sellers WHERE cpf=?", (cpf,))
        if cursor.fetchone():
            QtWidgets.QMessageBox.warning(self, "Alerta", "Já existe um vendedor cadastrado com este CPF!")
            return
        try:
            cursor.execute("INSERT INTO sellers (name,email,phone,cpf) VALUES (?,?,?,?)",
                           (name, email, phone, cpf))
            conn.commit()
            self.load_sellers()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Vendedor adicionado com sucesso!")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Erro ao adicionar vendedor: {e}")

    # Atualizar
    def update_seller(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return
        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um vendedor para atualizar!")
            return
        sid = int(self.table.item(sel, 0).text())
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = format_phone(self.phone_input.text())
        cpf = self.cpf_input.text().strip()
        if not name or not email or not cpf:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Nome, Email e CPF são obrigatórios!")
            return
        cursor.execute("SELECT id FROM sellers WHERE cpf=? AND id<>?", (cpf, sid))
        if cursor.fetchone():
            QtWidgets.QMessageBox.warning(self, "Alerta", "Já existe outro vendedor cadastrado com este CPF!")
            return
        try:
            cursor.execute(
                "UPDATE sellers SET name=?, email=?, phone=?, cpf=? WHERE id=?",
                (name, email, phone, cpf, sid)
            )
            conn.commit()
            self.load_sellers()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Vendedor atualizado com sucesso!")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Erro ao atualizar vendedor: {e}")

    # Excluir
    def delete_seller(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return
        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um vendedor para excluir!")
            return
        sid = int(self.table.item(sel, 0).text())
        sname = self.table.item(sel, 1).text()
        
        
        # 🔎 Verificar se vendedor esta relacionado a uma venda.
        cursor.execute("SELECT COUNT(*) FROM sales WHERE seller_id=?", (sid,))
        count = cursor.fetchone()[0]
        if count > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Restrição",
                f"O vendedor '{sname}' não pode ser excluído, pois já está vinculado a {count} venda(s)."
            )
            return
        
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirmação")
        msg.setText(f"Tem certeza que deseja excluir o vendedor '{sname}'?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")
        reply = msg.exec_()
        if reply == QtWidgets.QMessageBox.Yes:
            cursor.execute("DELETE FROM sellers WHERE id=?", (sid,))
            conn.commit()
            self.load_sellers()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Vendedor excluído com sucesso!")

    # Mostrar grid só após clicar em "Pesquisar".
    def show_and_filter(self):
        self.table.setVisible(True)
        self.filter_table()
    
    def show_and_filter(self):
        self.table.setVisible(True)
        self.filter_table()
        # Verificar se existe pelo menos 1 linha visível após o filtro
        any_visible = False
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                any_visible = True
                break

        if not any_visible:
            QtWidgets.QMessageBox.information(
                self,
                "Nenhum resultado",
                "Nenhum vendedor encontrado com esse termo de pesquisa."
            )

    # Filtrar e esconder grid caso não tenha resultados.
    def filter_table(self):
        q = self.search_input.text().lower()
        any_visible = False
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            email = self.table.item(row, 2).text().lower()
            phone = self.table.item(row, 3).text().lower()
            cpf = self.table.item(row, 4).text().lower()
            hide = q not in name and q not in email and q not in phone and q not in cpf
            self.table.setRowHidden(row, hide)
            if not hide:
                any_visible = True
        self.table.setVisible(any_visible)
#-------------------------------------- FIM VENDEDORES ---------------------------------------------------------




# ---------------------------------------- TELA DE VENDAS -------------------------------------------------
# -------- Função utilitária para formatar valores monetários --------
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class SalesWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(10)
        self.vbox.setContentsMargins(16, 16, 16, 16)

        self.cart = []  # carrinho temporário
        self.setup_ui()
        self.load_clients()
        self.load_sellers()
        self.load_products()

    # centraliza e exibe mensagens
    def show_messagebox(self, icon, title, text):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        # centralizar
        screen = QtWidgets.QApplication.desktop().screenGeometry()
        x = (screen.width() - msg.sizeHint().width()) // 2
        y = (screen.height() - msg.sizeHint().height()) // 2
        msg.move(x, y)
        return msg.exec_()

    # ------------------- Setup UI -------------------
    def setup_ui(self):
        # Linha Cliente + Vendedor + Atualizar
        top_h = QtWidgets.QHBoxLayout()
        top_h.setSpacing(8)

        lbl_client = QtWidgets.QLabel("Cliente:")
        self.client_combo = QtWidgets.QComboBox()
        self.client_combo.setStyleSheet("padding:8px; border:1px solid #dcdcdc; border-radius:8px;")
        top_h.addWidget(lbl_client)
        top_h.addWidget(self.client_combo, 2)

        lbl_seller = QtWidgets.QLabel("Vendedor:")
        self.seller_combo = QtWidgets.QComboBox()
        self.seller_combo.setStyleSheet("padding:8px; border:1px solid #dcdcdc; border-radius:8px;")
        top_h.addWidget(lbl_seller)
        top_h.addWidget(self.seller_combo, 2)       

        # botão atualizar
        self.refresh_btn = QtWidgets.QPushButton("🔄 Atualizar")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        top_h.addWidget(self.refresh_btn)
        self.vbox.addLayout(top_h)

        # Atalho de teclado (F5)
        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self)
        shortcut.activated.connect(self.refresh_data)

        # Rodapé de dica
        self.lbl_help = QtWidgets.QLabel("💡 Dica: escolha o cliente e o vendedor antes de adicionar produtos.")
        self.lbl_help.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic; padding:6px;")
        self.lbl_help.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.lbl_help)

        # Seleção de produto
        product_layout = QtWidgets.QHBoxLayout()
        self.product_combo = QtWidgets.QComboBox()
        self.product_combo.setStyleSheet("padding:8px; border:1px solid #dcdcdc; border-radius:8px;")

        self.qty_input = QtWidgets.QLineEdit()
        self.qty_input.setPlaceholderText("Qtd")
        self.qty_input.setFixedWidth(60)
        self.qty_input.setValidator(QtGui.QIntValidator(1, 9999))

        self.btn_add_cart = QtWidgets.QPushButton("Adicionar ao Carrinho")
        self.btn_add_cart.setStyleSheet("background-color:#27ae60; color:white; padding:8px; border-radius:6px; font-weight:700;")
        self.btn_add_cart.clicked.connect(self.add_to_cart)

        product_layout.addWidget(QtWidgets.QLabel("Produto:"))
        product_layout.addWidget(self.product_combo, 3)
        product_layout.addWidget(QtWidgets.QLabel("Qtd:"))
        product_layout.addWidget(self.qty_input)
        product_layout.addWidget(self.btn_add_cart)
        self.vbox.addLayout(product_layout)

        # Tabela carrinho
        self.cart_table = QtWidgets.QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Produto", "Preço Unit.", "Qtd", "Subtotal", "Ações"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cart_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                background: #fff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                gridline-color: #ecf0f1;
            }
            QHeaderView::section {
                background: #2980b9;
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
        self.vbox.addWidget(self.cart_table)

        # Total
        total_layout = QtWidgets.QHBoxLayout()
        self.lbl_total = QtWidgets.QLabel("Total: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size:16px; font-weight:700; color:#2c3e50;")
        total_layout.addStretch()
        total_layout.addWidget(self.lbl_total)
        self.vbox.addLayout(total_layout)

        # Status de pagamento (COMBO MODERNO)
        status_layout = QtWidgets.QHBoxLayout()
        lbl_status = QtWidgets.QLabel("Status Pagamento:")
        lbl_status.setStyleSheet("font-weight:700; font-size:14px; color:#2c3e50;")
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItem("-- Selecione --", None)
        self.status_combo.addItem("Pendente", "Pendente")
        self.status_combo.currentIndexChanged.connect(self.update_status_color)
        self.update_status_color()
        status_layout.addStretch()
        status_layout.addWidget(lbl_status)
        status_layout.addWidget(self.status_combo)
        self.vbox.addLayout(status_layout)

        # Botão finalizar venda
        self.btn_finalize = QtWidgets.QPushButton("Finalizar Venda")
        self.btn_finalize.setStyleSheet("background-color:#2980b9; color:white; padding:12px; border-radius:8px; font-weight:700;")
        self.btn_finalize.clicked.connect(self.finalize_sale)
        self.vbox.addWidget(self.btn_finalize)

    # ------------------- Atualiza cor do status -------------------
    def update_status_color(self):
        status = self.status_combo.currentData()
        if status == "Pago":
            color = "#2ecc71"
            text_color = "white"
        elif status == "Pendente":
            color = "#e74c3c"
            text_color = "white"
        else:
            color = "#bdc3c7"
            text_color = "#7f8c8d"
        self.status_combo.setStyleSheet(f"""
            QComboBox {{
                padding:10px;
                border:2px solid #2980b9;
                border-radius:12px;
                font-weight:700;
                font-size:14px;
                color:{text_color};
                background-color:{color};
                min-width:140px;
            }}
            QComboBox::drop-down {{
                border-left:0px;
            }}
            QComboBox QAbstractItemView {{
                selection-background-color:#3498db;
                selection-color:white;
                font-weight:700;
                font-size:14px;
            }}
        """)

    # ------------------- Atualizar dados -------------------
    def refresh_data(self):
        self.load_clients()
        self.load_sellers()
        self.load_products()
        self.show_messagebox(QtWidgets.QMessageBox.Information, "Atualizado", "Dados recarregados com sucesso!")

    # ------------------- Carregar dados -------------------
    def load_clients(self):
        try:
            self.client_combo.clear()
            cursor.execute("SELECT id, name FROM clients")
            for cid, name in cursor.fetchall():
                self.client_combo.addItem(name, cid)
        except Exception as e:
            print("Erro load_clients:", e)

    def load_sellers(self):
        try:
            self.seller_combo.clear()
            cursor.execute("SELECT id, name FROM sellers")
            for sid, name in cursor.fetchall():
                self.seller_combo.addItem(name, sid)
        except Exception as e:
            print("Erro load_sellers:", e)

    def load_products(self):
        try:
            self.product_combo.clear()
            cursor.execute("SELECT id, name, price, quantidade FROM products")
            for pid, name, price, qty in cursor.fetchall():
                self.product_combo.addItem(f"{name} (Estoque: {qty})", (pid, price, qty))
        except Exception as e:
            print("Erro load_products:", e)

    # ------------------- Carrinho -------------------
    def add_to_cart(self):
        qty_text = self.qty_input.text().strip()
        if not qty_text.isdigit():
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Quantidade inválida.")
            return
        qty = int(qty_text)
        data = self.product_combo.currentData()
        if not data:
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Nenhum produto selecionado.")
            return
        pid, price, stock = data
        name = self.product_combo.currentText().split(" (")[0]
        if qty <= 0 or qty > stock:
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Quantidade fora do estoque disponível.")
            return
        existing = next((it for it in self.cart if it["pid"] == pid), None)
        if existing:
            new_qty = existing["qty"] + qty
            if new_qty > stock:
                self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Quantidade total excede o estoque disponível.")
                return
            existing["qty"] = new_qty
            existing["subtotal"] = existing["qty"] * existing["price"]
        else:
            self.cart.append({"pid": pid, "name": name, "price": price, "qty": qty, "subtotal": qty * price})
        self.qty_input.clear()
        self.refresh_cart()

    def refresh_cart(self):
        self.cart_table.setRowCount(0)
        total = 0
        for i, item in enumerate(self.cart):
            self.cart_table.insertRow(i)
            cell_name = QtWidgets.QTableWidgetItem(item["name"])
            cell_name.setTextAlignment(QtCore.Qt.AlignCenter)
            self.cart_table.setItem(i, 0, cell_name)
            cell_price = QtWidgets.QTableWidgetItem(format_currency(item["price"]))
            cell_price.setTextAlignment(QtCore.Qt.AlignCenter)
            self.cart_table.setItem(i, 1, cell_price)
            cell_qty = QtWidgets.QTableWidgetItem(str(item["qty"]))
            cell_qty.setTextAlignment(QtCore.Qt.AlignCenter)
            self.cart_table.setItem(i, 2, cell_qty)
            cell_sub = QtWidgets.QTableWidgetItem(format_currency(item["subtotal"]))
            cell_sub.setTextAlignment(QtCore.Qt.AlignCenter)
            self.cart_table.setItem(i, 3, cell_sub)

            btn_edit = QtWidgets.QPushButton("Editar")
            btn_edit.setStyleSheet("background:#f39c12; color:white; border-radius:6px; padding:4px;")
            btn_edit.setToolTip("Clique para editar este item do carrinho")
            btn_edit.clicked.connect(lambda _, r=i: self.edit_item(r))

            btn_del = QtWidgets.QPushButton("Excluir")
            btn_del.setStyleSheet("background:#c0392b; color:white; border-radius:6px; padding:4px;")
            btn_del.setToolTip("Clique para remover este item do carrinho")
            btn_del.clicked.connect(lambda _, r=i: self.delete_item(r))

            action_layout = QtWidgets.QHBoxLayout()
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_del)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget = QtWidgets.QWidget()
            action_widget.setLayout(action_layout)
            self.cart_table.setCellWidget(i, 4, action_widget)
            total += item["subtotal"]

        self.lbl_total.setText(f"Total: {format_currency(total)}")

    def delete_item(self, row):
        if 0 <= row < len(self.cart):
            del self.cart[row]
            self.refresh_cart()

    def edit_item(self, row):
        if row < 0 or row >= len(self.cart):
            return
        item = self.cart[row]
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Editar Item")
        dialog.setFixedSize(360, 220)
        layout = QtWidgets.QVBoxLayout(dialog)

        combo = QtWidgets.QComboBox()
        cursor.execute("SELECT id, name, price, quantidade FROM products")
        products = cursor.fetchall()
        for pid, name, price, qty in products:
            combo.addItem(f"{name} (Estoque: {qty})", (pid, name, price, qty))
        index = next((i for i, (pid_, _, _, _) in enumerate(products) if pid_ == item["pid"]), 0)
        combo.setCurrentIndex(index)

        qty_input = QtWidgets.QLineEdit(str(item["qty"]))
        qty_input.setValidator(QtGui.QIntValidator(1, 9999))

        btn_ok = QtWidgets.QPushButton("Salvar")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)

        layout.addWidget(QtWidgets.QLabel("Produto:"))
        layout.addWidget(combo)
        layout.addWidget(QtWidgets.QLabel("Quantidade:"))
        layout.addWidget(qty_input)
        btns = QtWidgets.QHBoxLayout()
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if not qty_input.text().isdigit():
                self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Quantidade inválida.")
                return
            new_qty = int(qty_input.text())
            pid, name, price, stock = combo.currentData()
            if new_qty <= 0 or new_qty > stock:
                self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Quantidade fora do estoque disponível.")
                return
            item["pid"] = pid
            item["name"] = name
            item["price"] = price
            item["qty"] = new_qty
            item["subtotal"] = new_qty * price
            self.refresh_cart()

    # ------------------- Finalizar venda -------------------
    def finalize_sale(self):
        if not self.cart:
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Carrinho vazio.")
            return
        client_id = self.client_combo.currentData()
        seller_id = self.seller_combo.currentData()
        if client_id is None:
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Selecione um cliente.")
            return
        if seller_id is None:
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "Selecione um vendedor.")
            return
        status = self.status_combo.currentData()
        if status is None:
            self.show_messagebox(QtWidgets.QMessageBox.Warning, "Erro", "O status de pagamento não pode ficar em branco.")
            return
        total = sum(item["subtotal"] for item in self.cart)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute(
                "INSERT INTO sales (client_id, seller_id, total, date, status) VALUES (?, ?, ?, ?, ?)",
                (client_id, seller_id, total, now, status)
            )
            sale_id = cursor.lastrowid
            for item in self.cart:
                cursor.execute(
                    "INSERT INTO sales_items (sale_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
                    (sale_id, item["pid"], item["qty"], item["subtotal"])
                )
                cursor.execute(
                    "UPDATE products SET quantidade = quantidade - ? WHERE id=?",
                    (item["qty"], item["pid"])
                )
            conn.commit()
            self.cart.clear()
            self.refresh_cart()
            self.load_products()
            self.show_messagebox(QtWidgets.QMessageBox.Information, "Sucesso", "Venda registrada com sucesso!")
        except Exception as e:
            conn.rollback()
            self.show_messagebox(QtWidgets.QMessageBox.Critical, "Erro", f"Erro ao registrar venda: {e}")
            print("Erro finalize_sale:", e)
# ------------------------------------------ FIM VENDAS ------------------------------------------------------




# ------------------------------------ CONSULTAR VENDAS ---------------------------------------
class SalesHistoryWidget(QtWidgets.QWidget):
    def __init__(self, dashboard=None):
        super().__init__()
        self.dashboard = dashboard
        self.current_filter = "todas"

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(10)
        self.vbox.setContentsMargins(16, 16, 16, 16)

        self.setup_ui()
        # NÃO carrega vendas no início para manter oculto
        # self.load_sales()

    # ---------------- UI ----------------
    def setup_ui(self):
        title = QtWidgets.QLabel("Histórico de Vendas")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#2c3e50;")
        self.vbox.addWidget(title)

        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.setSpacing(10)

        self.refresh_btn = self.create_filter_button("🔄 Todas", "#34495e")
        self.refresh_btn.clicked.connect(self.reset_filter)

        self.pending_btn = self.create_filter_button("⏳ Pendentes", "#e67e22")
        self.pending_btn.clicked.connect(lambda: self.filter_sales("pendente"))

        self.paid_btn = self.create_filter_button("✅ Pagas", "#27ae60")
        self.paid_btn.clicked.connect(lambda: self.filter_sales("pago"))

        self.cancelled_btn = self.create_filter_button("❌ Canceladas", "#c0392b")
        self.cancelled_btn.clicked.connect(lambda: self.filter_sales("cancelada"))

        self.btn_layout.addWidget(self.refresh_btn)
        self.btn_layout.addWidget(self.pending_btn)
        self.btn_layout.addWidget(self.paid_btn)
        self.btn_layout.addWidget(self.cancelled_btn)
        

        self.delete_btn = QtWidgets.QPushButton("🗑️ Deletar")
        self.delete_btn.clicked.connect(self.delete_sale)
        self.btn_layout.addWidget(self.delete_btn)

        self.cancel_btn = QtWidgets.QPushButton("❌ Cancelar")
        self.cancel_btn.clicked.connect(self.cancel_sale)
        self.btn_layout.addWidget(self.cancel_btn)

        self.pay_btn = QtWidgets.QPushButton("💳 Pagar")
        self.pay_btn.clicked.connect(self.make_payment)
        self.btn_layout.addWidget(self.pay_btn)

        self.vbox.addLayout(self.btn_layout)

        self.sales_table = QtWidgets.QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels(
            ["ID", "Cliente", "Vendedor", "Data", "Total", "Status", "Pagamento"]
        )
        self.sales_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.sales_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.sales_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.itemSelectionChanged.connect(self.update_buttons)
        self.sales_table.doubleClicked.connect(self.view_sale_details)

        # <-- AJUSTE: COMEÇA OCULTO
        self.sales_table.setVisible(False)

        self.vbox.addWidget(self.sales_table)
        self.highlight_active_button(self.refresh_btn)

    # ---------------- BOTÕES ----------------
    def create_filter_button(self, text, color):
        btn = QtWidgets.QPushButton(text)
        btn.base_color = color
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
            }}
        """)
        return btn

    def highlight_active_button(self, active_btn):
        for btn in [self.refresh_btn, self.pending_btn, self.paid_btn, self.cancelled_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn.base_color};
                    color: white;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 6px 12px;
                }}
            """)

        active_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 12px;
                border: 2px solid white;
            }
        """)

    # ---------------- FILTROS ----------------
    def filter_sales(self, status):
        self.current_filter = status

        # <-- AJUSTE: oculta antes do carregamento
        self.sales_table.setVisible(False)

        btn_map = {
            "pendente": self.pending_btn,
            "pago": self.paid_btn,
            "cancelada": self.cancelled_btn
        }

        self.highlight_active_button(btn_map.get(status, self.refresh_btn))
        self.load_sales()

    def reset_filter(self):
        self.current_filter = "todas"

        # <-- AJUSTE: oculta antes
        self.sales_table.setVisible(False)

        self.highlight_active_button(self.refresh_btn)
        self.load_sales()

    # ---------------- CARREGAR ----------------
    def load_sales(self):
        self.sales_table.setRowCount(0)

        query = """
            SELECT s.id, c.name, sel.name, s.date, s.total, s.status,
                   COALESCE(s.payment_method, '—')
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            JOIN sellers sel ON s.seller_id = sel.id
        """

        if self.current_filter != "todas":
            query += " WHERE LOWER(s.status)=?"

        query += " ORDER BY s.date DESC"

        if self.current_filter != "todas":
            cursor.execute(query, (self.current_filter,))
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        from datetime import datetime

        for row, data in enumerate(rows):
            self.sales_table.insertRow(row)
            for col, value in enumerate(data):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(QtCore.Qt.AlignCenter)

                if col == 4:
                    item.setText(format_currency(value))

                if col == 3:
                    try:
                        item.setText(datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"))
                    except:
                        pass

                if col == 5:
                    colors = {
                        "pago": "#2ecc71",
                        "pendente": "#e74c3c",
                        "cancelada": "#e67e22"
                    }
                    item.setBackground(QtGui.QColor(colors.get(value.lower(), "#7f8c8d")))
                    item.setForeground(QtGui.QColor("white"))

                self.sales_table.setItem(row, col, item)

        # Atualiza botões / etc.
        self.update_buttons()

        # Controla visibilidade + mensagem
        if self.sales_table.rowCount() > 0:
            self.sales_table.setVisible(True)
        else:
            self.sales_table.setVisible(False)
            QtWidgets.QMessageBox.information(self, "Nenhum registro", "Nenhuma venda encontrada para o filtro selecionado.")

    # ---------------- CONTROLE ----------------
    def update_buttons(self):
        row = self.sales_table.currentRow()
        if row < 0:
            self.delete_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.pay_btn.setEnabled(False)
            return

        status = self.sales_table.item(row, 5).text().lower()

        self.delete_btn.setEnabled(status != "pago")
        self.cancel_btn.setEnabled(status == "pendente")
        self.pay_btn.setEnabled(status == "pendente")

    # ---------------- DETALHES ----------------
    def view_sale_details(self):
        row = self.sales_table.currentRow()
        if row < 0:
            return

        sale_id = int(self.sales_table.item(row, 0).text())

        cursor.execute("""
            SELECT c.name, sel.name, s.date, s.status, s.total,
                COALESCE(s.payment_method, '—'),
                COALESCE(s.installments, 1)
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            JOIN sellers sel ON s.seller_id = sel.id
            WHERE s.id=?
        """, (sale_id,))
        result = cursor.fetchone()

        if not result:
            return

        client, seller, date, status, total, payment_method, installments = result

        cursor.execute("""
            SELECT p.name, si.quantity, si.subtotal
            FROM sales_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id=?
        """, (sale_id,))
        items = cursor.fetchall()

        from datetime import datetime
        try:
            date_fmt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        except:
            date_fmt = date

        if payment_method.lower() == "cartão" and installments > 1:
            payment_display = f"{payment_method} ({installments}x)"
        else:
            payment_display = payment_method

        status_icon = {
            "pago": "✅",
            "pendente": "⏳",
            "cancelada": "❌"
        }.get(status.lower(), "ℹ️")

        details = f"""
📄 VENDA Nº {sale_id}

👤 Cliente: {client}
🧑‍💼 Vendedor: {seller}
📅 Data: {date_fmt}

📌 Status: {status_icon} {status}
💰 Total: {format_currency(total)}
💳 Pagamento: {payment_display}

🛒 ITENS DA VENDA:
"""

        for name, qty, subtotal in items:
            details += f"- {name} | Qtd: {qty} | {format_currency(subtotal)}\n"

        QtWidgets.QMessageBox.information(
            self,
            "Detalhes da Venda",
            details
        )

    # ---------------- DELETAR ----------------
    def delete_sale(self):
        row = self.sales_table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Selecione uma venda.")
            return

        status = self.sales_table.item(row, 5).text().lower()
        if status == "pago":
            QtWidgets.QMessageBox.warning(self, "Ação não permitida", "Venda paga não pode ser excluída.")
            return

        sale_id = int(self.sales_table.item(row, 0).text())

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirmação")
        msg.setText(f"Deseja realmente excluir a venda #{sale_id}?")
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")

        if msg.exec_() != QtWidgets.QMessageBox.Yes:
            return

        cursor.execute("DELETE FROM sales_items WHERE sale_id=?", (sale_id,))
        cursor.execute("DELETE FROM sales WHERE id=?", (sale_id,))
        conn.commit()
        self.load_sales()

    # ---------------- CANCELAR ----------------
    def cancel_sale(self):
        row = self.sales_table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Selecione uma venda.")
            return

        status = self.sales_table.item(row, 5).text().lower()
        if status != "pendente":
            QtWidgets.QMessageBox.warning(
                self, "Ação não permitida", "Somente vendas pendentes podem ser canceladas."
            )
            return

        sale_id = int(self.sales_table.item(row, 0).text())

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirmação")
        msg.setText(f"Deseja realmente cancelar a venda #{sale_id}?")
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")

        if msg.exec_() != QtWidgets.QMessageBox.Yes:
            return

        cursor.execute("UPDATE sales SET status='Cancelada' WHERE id=?", (sale_id,))
        conn.commit()
        self.load_sales()

    # ---------------- PAGAR ----------------
    def make_payment(self):
        row = self.sales_table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(
                self, "Aviso", "Selecione uma venda para realizar o pagamento."
            )
            return

        sale_id = self.sales_table.item(row, 0).text()
        status = self.sales_table.item(row, 5).text().lower()

        if status != "pendente":
            QtWidgets.QMessageBox.information(
                self, "Pagamento", "Esta venda não está pendente."
            )
            return

        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Forma de Pagamento")
        dialog.setLabelText("Selecione a forma de pagamento:")
        dialog.setComboBoxItems(["Dinheiro", "Pix", "Cartão"])

        if not dialog.exec_():
            return

        payment_method = dialog.textValue()
        installments = 1

        if payment_method == "Cartão":
            parcels = QtWidgets.QInputDialog(self)
            parcels.setWindowTitle("Parcelamento")
            parcels.setLabelText("Escolha o número de parcelas:")
            parcels.setComboBoxItems([f"{i}x" for i in range(1, 13)])

            if not parcels.exec_():
                return

            installments = int(parcels.textValue().replace("x", ""))

        if payment_method == "Cartão" and installments > 1:
            payment_display = f"{payment_method} ({installments}x)"
        else:
            payment_display = payment_method

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirmar Pagamento")
        msg.setText(
            f"Deseja confirmar o pagamento da venda #{sale_id}?\n\n"
            f"Forma de pagamento: {payment_display}"
        )
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim, Pagar")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")

        if msg.exec_() != QtWidgets.QMessageBox.Yes:
            return

        cursor.execute("""
            UPDATE sales
            SET status = 'Pago',
                payment_method = ?,
                installments = ?
            WHERE id = ?
        """, (payment_method, installments, sale_id))
        conn.commit()

        self.load_sales()
        if self.dashboard:
            self.dashboard.refresh()

        QtWidgets.QMessageBox.information(
            self,
            "Sucesso",
            f"Pagamento realizado com sucesso!\n\nForma de pagamento: {payment_display}"
        )
# ------------------------------------ FIM CONSULTAR VENDAS ---------------------------------------






# --------------------------------------- COMISSÃO DE VENDAS ------------------------------------------
class SalesCommissionWidget(QtWidgets.QWidget):
    def __init__(self, dashboard=None):
        super().__init__()
        self.dashboard = dashboard
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(10)
        self.vbox.setContentsMargins(16,16,16,16)
        self.setup_ui()
        self.load_commissions()
        

    def setup_ui(self):
        # Título
        title = QtWidgets.QLabel("Comissão de Vendas")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#2c3e50;")
        self.vbox.addWidget(title)
        

        # Layout de filtros + botões
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(10)

        # Layout de filtros
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setSpacing(5)

        self.date_from = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_to = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_to.setCalendarPopup(True)

        self.seller_combo = QtWidgets.QComboBox()
        self.load_sellers()

        # Campos ajustáveis
        self.date_from.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.date_to.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.seller_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        filter_layout.addWidget(QtWidgets.QLabel("De:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QtWidgets.QLabel("Até:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QtWidgets.QLabel("Vendedor:"))
        filter_layout.addWidget(self.seller_combo)

        top_layout.addLayout(filter_layout)

        # Layout de botões
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(5)

        button_style = """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px 16px;
                border: 2px solid #2ecc71;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """

        # Botão Filtrar
        self.filter_btn = QtWidgets.QPushButton("🔍 Filtrar")
        self.filter_btn.setStyleSheet(button_style)
        self.filter_btn.clicked.connect(self.load_commissions)
        btn_layout.addWidget(self.filter_btn)

        # Botão Atualizar
        self.refresh_btn = QtWidgets.QPushButton("🔄 Atualizar")
        self.refresh_btn.setStyleSheet(button_style)
        self.refresh_btn.clicked.connect(self.load_sellers)
        btn_layout.addWidget(self.refresh_btn)
        

        top_layout.addLayout(btn_layout)
        top_layout.addStretch()  # garante botões à direita

        self.vbox.addLayout(top_layout)

        # Tabela de comissão
        self.commission_table = QtWidgets.QTableWidget()
        self.commission_table.setColumnCount(6)
        self.commission_table.setHorizontalHeaderLabels(
            ["ID Venda", "Cliente", "Vendedor", "Data", "Total Venda", "Comissão"]
        )
        self.commission_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.commission_table.verticalHeader().setVisible(False)
        self.commission_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.commission_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.vbox.addWidget(self.commission_table)

        # Resumo
        self.lbl_total = QtWidgets.QLabel("Total de Vendas: 0  |  Total de Comissão: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size:14px; font-weight:700; color:#27ae60; padding:6px;")
        self.vbox.addWidget(self.lbl_total)

    # Carrega vendedores no combo
    def load_sellers(self):
        self.seller_combo.clear()
        cursor.execute("SELECT id, name FROM sellers ORDER BY name")
        self.sellers = cursor.fetchall()
        self.seller_combo.addItem("Todos", 0)
        for sid, name in self.sellers:
            self.seller_combo.addItem(name, sid)

    # Recarrega a tabela mantendo filtros atuais
    def refresh_effect(self):
        self.load_commissions()
        self.load_sellers()
        # efeito visual temporário
        self.commission_table.setStyleSheet("QTableWidget {background-color: #ecf9f1;}")
        QtCore.QTimer.singleShot(300, lambda: self.reset_table_style())

    def reset_table_style(self):
        self.commission_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e0e0e0;
                border-radius:8px;
            }
            QTableWidget::item:alternate { background-color: #f4f6f9; }
            QTableWidget::item:selected { background-color: #2ecc71; color: #ffffff; }
            QTableWidget::item:hover { background-color: #ecf4ff; }
        """)

    # Carrega comissão
    def load_commissions(self):
        self.commission_table.setRowCount(0)
        date_from_q = self.date_from.date()
        date_to_q = self.date_to.date()

        # Validação
        if date_to_q < date_from_q:
            QtWidgets.QMessageBox.warning(self, "Aviso", "A data final não pode ser menor que a data inicial.")
            return

        date_from = date_from_q.toString("yyyy-MM-dd")
        date_to = date_to_q.toString("yyyy-MM-dd")
        seller_id = self.seller_combo.currentData()

        query = """
            SELECT s.id, c.name, sel.name, s.date, s.total
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            JOIN sellers sel ON s.seller_id = sel.id
            WHERE s.status='Pago' AND DATE(s.date) BETWEEN ? AND ?
        """
        params = [date_from, date_to]

        if seller_id != 0:
            query += " AND s.seller_id=?"
            params.append(seller_id)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        total_commission = 0
        fixed_pct = 5  # VALOR COMISSÃO FIXA

        for i, (sale_id, client, seller, date, total) in enumerate(rows):
            self.commission_table.insertRow(i)

            # ID
            item = QtWidgets.QTableWidgetItem(str(sale_id))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.commission_table.setItem(i, 0, item)

            # Cliente
            item = QtWidgets.QTableWidgetItem(client)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.commission_table.setItem(i, 1, item)

            # Vendedor
            item = QtWidgets.QTableWidgetItem(seller)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.commission_table.setItem(i, 2, item)

            # Data
            dt = QtCore.QDate.fromString(date[:10], "yyyy-MM-dd")
            item = QtWidgets.QTableWidgetItem(dt.toString("dd/MM/yyyy"))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.commission_table.setItem(i, 3, item)

            # Total Venda
            item = QtWidgets.QTableWidgetItem(format_currency(total))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.commission_table.setItem(i, 4, item)

            # Comissão
            commission_value = total * (fixed_pct / 100)
            total_commission += commission_value
            item = QtWidgets.QTableWidgetItem(format_currency(commission_value))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.commission_table.setItem(i, 5, item)

        # Atualiza resumo
        total_sales = len(rows)
        self.lbl_total.setText(
            f"Total de Vendas: {total_sales}  |  Total de Comissão: {format_currency(total_commission)}"
        )
# -------------------------------------- FIM COMISSÃO DE VENDAS ----------------------------------------





# ---------------------------------------- CLIENTES ----------------------------------------------------
class ClientsWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(12)
        self.vbox.setContentsMargins(20, 20, 20, 20)
        

        self.setup_ui()
        self.load_clients()

        # Efeito de fade
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QtCore.QPropertyAnimation(self.opacity_effect, b'opacity', self)
        self.fade_anim.setDuration(400)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #d0d7de;
                font-size: 14px;
                gridline-color: #e6e6e6;
                alternate-background-color: #f7f9fc;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #d9ecff;
                color: #1c3f5d;
                border: 1px solid #5dade2;
                border-radius: 4px;
            }

            QTableWidget::item:hover {
                background-color: #eef6ff;
            }

            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-right: 1px solid #1f2d3a;
            }

            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }

            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }

            QScrollBar:vertical {
                width: 10px;
                background: #eef1f4;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #b7c2cc;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #9eabb9;
            }
        """)

    def setup_ui(self):
        # Campo de pesquisa
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar clientes...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding:10px;
                border:1px solid #dcdcdc;
                border-radius:12px;
                background-color:#f7f9fc;
            }
            QLineEdit:focus {
                border:1.5px solid #3498db;
                background-color:#ffffff;
            }
        """)
        self.vbox.addWidget(self.search_input)

        # Botão de pesquisa
        self.btn_search = self.create_button("Pesquisar", "#2980b9", "#3498db", self.show_and_filter)
        self.vbox.addWidget(self.btn_search)

        # Tabela moderna
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Email", "Telefone", "Aniversário"])
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color:#34495e;
                color:white;
                font-weight:bold;
                font-size:14px;
                border:none;
                padding:10px;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e0e0e0;
                border-radius:8px;
            }
            QTableWidget::item:alternate { background-color: #f4f6f9; }
            QTableWidget::item:selected { background-color: #3498db; color: #ffffff; }
            QTableWidget::item:hover { background-color: #ecf4ff; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.vbox.addWidget(self.table)
        self.table.setVisible(False)  # <<< escondida inicialmente

        # Inputs
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Nome")
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Email")
        email_regex = QtCore.QRegExp(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        self.email_input.setValidator(QtGui.QRegExpValidator(email_regex, self.email_input))
        self.phone_input = QtWidgets.QLineEdit()
        self.phone_input.setPlaceholderText("Telefone")
        self.aniversary_input = QtWidgets.QLineEdit()
        self.aniversary_input.setPlaceholderText("Aniversário (DD/MM/AAAA)")

        # TELEFONE: apenas números com formatação
        phone_regex = QRegExp(r'^\(?\d{0,2}\)?\s?\d{0,5}-?\d{0,4}$')
        self.phone_input.setValidator(QRegExpValidator(phone_regex, self.phone_input))

        # ANIVERSÁRIO: máscara DD/MM/AAAA
        self.aniversary_input.setInputMask('00/00/0000;_')

        for widget in [self.name_input, self.email_input, self.phone_input, self.aniversary_input]:
            widget.setStyleSheet("""
                QLineEdit {
                    padding:8px;
                    border:1px solid #d0d0d0;
                    border-radius:8px;
                    background-color:#f9fafb;
                }
                QLineEdit:focus {
                    border:1.5px solid #3498db;
                    background-color:#ffffff;
                }
            """)

        # Botões modernos
        self.btn_add = self.create_button("Adicionar", "#27ae60", "#2ecc71", self.add_client)
        self.btn_update = self.create_button("Atualizar", "#f39c12", "#f5a623", self.update_client)
        self.btn_delete = self.create_button("Excluir", "#c0392b", "#e74c3c", self.delete_client)
        self.btn_clear = self.create_button("Limpar Campos", "#7f8c8d", "#95a5a6", self.clear_grid)

        # Rodapé
        self.lbl_help = QtWidgets.QLabel("💡 Dica: Clique duas vezes no item da grid para carregar os dados para alteração.")
        self.lbl_help.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic; padding:6px;")
        self.lbl_help.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.lbl_help)

        # Layout inputs + botões
        input_h = QtWidgets.QHBoxLayout()
        input_h.setSpacing(10)
        input_h.addWidget(self.name_input, 2)
        input_h.addWidget(self.email_input, 2)
        input_h.addWidget(self.phone_input, 1)
        input_h.addWidget(self.aniversary_input, 1)
        input_h.addWidget(self.btn_add)
        input_h.addWidget(self.btn_update)
        input_h.addWidget(self.btn_delete)
        input_h.addWidget(self.btn_clear)
        self.vbox.addLayout(input_h)

        self.table.cellClicked.connect(self.fill_fields_from_table)

        # Permissions
        if self.current_user.get("role") != "admin":
            for btn in [self.btn_add, self.btn_update, self.btn_delete]:
                btn.setEnabled(False)
            for widget in [self.name_input, self.email_input, self.phone_input, self.aniversary_input]:
                widget.setReadOnly(True)

    def create_button(self, text, color, hover_color, callback):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{color};
                color:white;
                padding:10px;
                border-radius:8px;
                font-weight:600;
            }}
            QPushButton:hover {{ background-color:{hover_color}; }}
        """)
        btn.clicked.connect(callback)
        return btn

    # Botão de pesquisa
    def show_and_filter(self):
        self.table.setVisible(True)
        self.filter_table()

    # Fade-in
    def showEvent(self, event):
        self.fade_anim.stop()
        self.opacity_effect.setOpacity(0.0)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        super().showEvent(event)

    # Limpar campos
    def clear_grid(self):
        self.table.clearSelection()
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.aniversary_input.clear()

    # Preencher campos
    def fill_fields_from_table(self, row, column):
        self.name_input.setText(self.table.item(row, 1).text())
        self.email_input.setText(self.table.item(row, 2).text())
        self.phone_input.setText(self.table.item(row, 3).text())
        self.aniversary_input.setText(self.table.item(row, 4).text())

    # Carregar clientes
    def load_clients(self):
        self.table.setRowCount(0)
        cursor.execute("SELECT * FROM clients")
        for r, row in enumerate(cursor.fetchall()):
            self.table.insertRow(r)
            for c, v in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(v))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(r, c, item)

    # Adicionar cliente
    def add_client(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return

        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = format_phone(self.phone_input.text())
        aniversary = self.aniversary_input.text().strip()

        if phone:
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) not in (10, 11):
                QtWidgets.QMessageBox.warning(
                    self, "Alerta",
                    "Telefone inválido! Use (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"
                )
                return

        if not name or not email or not aniversary:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Todos os campos são obrigatórios!")
            return

        if self.email_input.hasAcceptableInput() is False:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Email inválido!")
            return

        try:
            datetime.strptime(aniversary, "%d/%m/%Y")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Data inválida! Use DD/MM/AAAA.")
            return

        cursor.execute(
            "INSERT INTO clients (name,email,phone,aniversary) VALUES (?,?,?,?)",
            (name, email, phone, aniversary)
        )
        conn.commit()
        self.load_clients()
        self.clear_grid()
        QtWidgets.QMessageBox.information(self, "Sucesso", "Cliente adicionado!")

    # Atualizar cliente
    def update_client(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return

        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um cliente!")
            return

        cid = int(self.table.item(sel, 0).text())
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = format_phone(self.phone_input.text().strip())
        aniversary = self.aniversary_input.text().strip()

        if not name or not email or not phone or not aniversary:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Nome, Telefone, Email e Aniversário são obrigatórios!")
            return

        cursor.execute(
            "UPDATE clients SET name=?, email=?, phone=?, aniversary=? WHERE id=?",
            (name, email, phone, aniversary, cid)
        )
        conn.commit()
        self.load_clients()
        self.clear_grid()
        QtWidgets.QMessageBox.information(self, "Sucesso", "Cliente atualizado!")

    # Excluir cliente
    def delete_client(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return

        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um cliente!")
            return

        cid = int(self.table.item(sel, 0).text())
        cname = self.table.item(sel, 1).text()
        
        
        # 🔎 Verificar se o cliente esta relacionado a uma venda.
        cursor.execute("SELECT COUNT(*) FROM sales WHERE client_id=?", (cid,))
        count = cursor.fetchone()[0]
        if count > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Restrição",
                f"O cliente '{cname}' não pode ser excluído, pois já está vinculado a {count} venda(s)."
            )
            return

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirmação")
        msg.setText(f"Tem certeza que deseja excluir '{cname}'?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")

        reply = msg.exec_()
        if reply == QtWidgets.QMessageBox.Yes:
            cursor.execute("DELETE FROM clients WHERE id=?", (cid,))
            conn.commit()
            self.load_clients()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Cliente excluído!")
    
    # ------------------- Mostrar e filtrar tabela -------------------
    def show_and_filter(self):
        self.table.setVisible(True)
        self.filter_table()
        # Verificar se existe pelo menos 1 linha visível após o filtro
        any_visible = False
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                any_visible = True
                break

        if not any_visible:
            QtWidgets.QMessageBox.information(
                self,
                "Nenhum resultado",
                "Nenhum cliente encontrado com esse termo de pesquisa."
            )

    # Filtrar tabela
    def filter_table(self):
        q = self.search_input.text().lower()
        any_visible = False
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            email = self.table.item(row, 2).text().lower()
            phone = self.table.item(row, 3).text().lower()
            hide = q not in name and q not in email and q not in phone
            self.table.setRowHidden(row, hide)
            if not hide:
                any_visible = True
        self.table.setVisible(any_visible)  # só mostra se tiver resultados
# ---------------------------------------- FIM CLIENTES ----------------------------------------------------




# ----------------------------------------- PRODUTOS ------------------------------------------------------
class ProductsWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(12)
        self.vbox.setContentsMargins(20, 20, 20, 20)
        self.vbox.setAlignment(QtCore.Qt.AlignTop)
        
        # Título centralizado
        self.title_label = QtWidgets.QLabel("Gerenciamento de Produtos")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #34495e; margin-bottom: 10px;")
        self.vbox.addWidget(self.title_label)

        self.setup_ui()
        self.load_brands_in_combo()

        # Efeito fade
        self.effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QtCore.QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #d0d7de;
                font-size: 14px;
                gridline-color: #e6e6e6;
                alternate-background-color: #f7f9fc;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #d9ecff;
                color: #1c3f5d;
                border: 1px solid #5dade2;
                border-radius: 4px;
            }

            QTableWidget::item:hover {
                background-color: #eef6ff;
            }

            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-right: 1px solid #1f2d3a;
            }

            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }

            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }

            QScrollBar:vertical {
                width: 10px;
                background: #eef1f4;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #b7c2cc;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #9eabb9;
            }
        """)


    def setup_ui(self):
        # Campos
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Nome do Produto")

        self.price_input = QtWidgets.QLineEdit()
        self.price_input.setPlaceholderText("Preço")

        self.quantity_input = QtWidgets.QLineEdit()
        self.quantity_input.setPlaceholderText("Quantidade")
        
        # Apenas números para quantidade (inteiro)
        self.quantity_input.setValidator(QIntValidator(0, 999999, self))

        # Apenas números para preço (decimal)
        price_validator = QDoubleValidator(0.00, 999999.99, 2, self)
        price_validator.setNotation(QDoubleValidator.StandardNotation)
        self.price_input.setValidator(price_validator)

        # Combobox marca
        self.brand_input = QtWidgets.QComboBox()
        self.btn_refresh_brands = QtWidgets.QPushButton("🔄")
        self.btn_refresh_brands.setFixedWidth(40)
        self.btn_refresh_brands.clicked.connect(self.load_brands_in_combo)

        brand_h = QtWidgets.QHBoxLayout()
        brand_h.addWidget(self.brand_input)
        brand_h.addWidget(self.btn_refresh_brands)

        # Botões
        self.btn_add = self.create_button("Adicionar", "#27ae60", "#2ecc71", self.add_product)
        self.btn_update = self.create_button("Atualizar", "#f39c12", "#f5a623", self.update_product)
        self.btn_delete = self.create_button("Excluir", "#c0392b", "#e74c3c", self.delete_product)
        self.btn_clear = self.create_button("Limpar Campos", "#7f8c8d", "#95a5a6", self.clear_inputs)
        self.btn_search = self.create_button("Pesquisar", "#2980b9", "#3498db", self.show_and_filter)

        input_h = QtWidgets.QHBoxLayout()
        input_h.addWidget(self.name_input, 3)
        input_h.addWidget(self.price_input, 1)
        input_h.addWidget(self.quantity_input, 1)
        input_h.addLayout(brand_h, 2)
        input_h.addWidget(self.btn_add)
        input_h.addWidget(self.btn_update)
        input_h.addWidget(self.btn_delete)
        input_h.addWidget(self.btn_clear)
        input_h.addWidget(self.btn_search)
        

        self.vbox.addLayout(input_h)

        # Tabela
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Preço", "Qtd", "Marca"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self.fill_inputs_from_table)
        self.table.hide()

        self.vbox.addWidget(self.table)

        # Permissões
        if self.current_user.get("role") != "admin":
            for w in [self.btn_add, self.btn_update, self.btn_delete]:
                w.setEnabled(False)
            for w in [self.name_input, self.price_input, self.quantity_input, self.brand_input]:
                w.setEnabled(False)

    # Estilo dos botões
    def create_button(self, text, color, hover_color, slot):
        btn = QtWidgets.QPushButton(text)
        btn.clicked.connect(slot)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        return btn

    # CRUD Produtos
    def load_products(self):
        self.table.setRowCount(0)
        cursor.execute("""
            SELECT p.id, p.name, p.price, p.quantidade, b.name
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
        """)

        for r, row in enumerate(cursor.fetchall()):
            self.table.insertRow(r)
            for c, v in enumerate(row):
                if c == 2:  # Preço formatado
                    v = f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                item = QtWidgets.QTableWidgetItem(str(v))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(r, c, item)

    def load_brands_in_combo(self):
        self.brand_input.clear()
        cursor.execute("SELECT id, name FROM brands ORDER BY name")
        for bid, bname in cursor.fetchall():
            self.brand_input.addItem(bname, bid)

    # Normaliza o preço para float
    def normalize_price(self, price):
        return float(
            price.replace("R$", "")
                 .replace(" ", "")
                 .replace(".", "")
                 .replace(",", ".")
        )

    def add_product(self):
        name = self.name_input.text().strip()
        price = self.price_input.text().strip()
        qty = self.quantity_input.text().strip()
        brand_id = self.brand_input.currentData()

        if not name or not price or not qty:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Todos os campos são obrigatórios!")
            return

        try:
            price_val = self.normalize_price(price)
            qty_val = int(qty)
            valor_total = price_val * qty_val
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Preço ou quantidade inválidos!")
            return

        cursor.execute("""
            INSERT INTO products (name, price, quantidade, valor_total, brand_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, price_val, qty_val, valor_total, brand_id))
        conn.commit()

        self.load_products()
        self.clear_inputs()
        QtWidgets.QMessageBox.information(self, "Sucesso", "Produto adicionado!")

    def update_product(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um produto!")
            return

        pid = int(self.table.item(row, 0).text())
        name = self.name_input.text().strip()
        price = self.price_input.text().strip()
        qty = self.quantity_input.text().strip()
        brand_id = self.brand_input.currentData()

        if not name or not price or not qty:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Todos os campos são obrigatórios!")
            return

        try:
            price_val = self.normalize_price(price)
            qty_val = int(qty)
            valor_total = price_val * qty_val
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Preço ou quantidade inválidos!")
            return

        cursor.execute("""
            UPDATE products 
            SET name=?, price=?, quantidade=?, valor_total=?, brand_id=? 
            WHERE id=?
        """, (name, price_val, qty_val, valor_total, brand_id, pid))
        conn.commit()

        self.load_products()
        self.clear_inputs()
        QtWidgets.QMessageBox.information(self, "Sucesso", "Produto atualizado!")

    def delete_product(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um produto!")
            return

        pid = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()

        cursor.execute("SELECT COUNT(*) FROM sales_items WHERE product_id=?", (pid,))
        vendas = cursor.fetchone()[0]

        if vendas > 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", f"Produto '{nome}' não pode ser excluído, pois já possui '{vendas}' vendas!")
            return

        # Confirmação
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setWindowTitle("Confirmação de Exclusão")
        msg.setText(f"Tem certeza de que deseja excluir o produto '{nome}'?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")

        if msg.exec_() == QtWidgets.QMessageBox.Yes:
            cursor.execute("DELETE FROM products WHERE id=?", (pid,))
            conn.commit()
            self.load_products()
            self.clear_inputs()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Produto excluído!")

    # Utilitários
    def clear_inputs(self):
        self.name_input.clear()
        self.price_input.clear()
        self.quantity_input.clear()
        if self.brand_input.count() > 0:
            self.brand_input.setCurrentIndex(0)

    def fill_inputs_from_table(self, row, _):
        self.name_input.setText(self.table.item(row, 1).text())

        preco = self.table.item(row, 2).text()
        preco = preco.replace("R$", "").strip()
        self.price_input.setText(preco)

        self.quantity_input.setText(self.table.item(row, 3).text())

        brand_name = self.table.item(row, 4).text()
        idx = self.brand_input.findText(brand_name)
        if idx >= 0:
            self.brand_input.setCurrentIndex(idx)

    def show_and_filter(self):
        if not self.table.isVisible():
            self.load_products()
            self.table.show()

        filtro = self.name_input.text().strip().lower()

        # Se campo estiver vazio, mostra tudo
        if not filtro:
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            return

        any_visible = False

        for row in range(self.table.rowCount()):
            nome_produto = self.table.item(row, 1).text().lower()
            hide = filtro not in nome_produto
            self.table.setRowHidden(row, hide)

            if not hide:
                any_visible = True

        # Se nenhum resultado encontrado → alerta
        if not any_visible:
            QtWidgets.QMessageBox.information(
                self,
                "Nenhum resultado",
                "Nenhum produto encontrado com esse termo de pesquisa."
            )

# ----------------------------------------- FIM PRODUTOS ------------------------------------------------------





# ----------------------------------------- MARCAS ------------------------------------------------------
class BrandsWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(12)
        self.vbox.setContentsMargins(20, 20, 20, 20)

        self.setup_ui()
        self.load_brands()

        # Fade effect
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QtCore.QPropertyAnimation(self.opacity_effect, b'opacity', self)
        self.fade_anim.setDuration(400)

    def setup_ui(self):
        # Campo de pesquisa moderno
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar marcas...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding:10px;
                border:1px solid #dcdcdc;
                border-radius:12px;
                background-color:#f7f9fc;
            }
            QLineEdit:focus {
                border:1.5px solid #3498db;
                background-color:#ffffff;
            }
        """)
        self.vbox.addWidget(self.search_input)

        # Tabela moderna
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Nome"])
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color:#2c3e50;
                color:white;
                font-weight:bold;
                font-size:14px;
                border:none;
                padding:10px;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color:#ffffff; gridline-color:#e0e0e0; border-radius:8px; }
            QTableWidget::item:alternate { background-color:#f4f6f9; }
            QTableWidget::item:selected { background-color:#3498db; color:#ffffff; }
            QTableWidget::item:hover { background-color:#ecf4ff; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.vbox.addWidget(self.table)
        self.table.setVisible(False)  
        self.table.cellClicked.connect(self.fill_fields_from_table)

        # Inputs
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Nome da marca")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding:8px;
                border:1px solid #d0d0d0;
                border-radius:8px;
                background-color:#f9fafb;
            }
            QLineEdit:focus {
                border:1.5px solid #3498db;
                background-color:#ffffff;
            }
        """)

        # Botões modernos
        self.btn_add = self.create_button("Adicionar", "#27ae60", "#2ecc71", self.add_brand)
        self.btn_update = self.create_button("Atualizar", "#f39c12", "#f5a623", self.update_brand)
        self.btn_delete = self.create_button("Excluir", "#c0392b", "#e74c3c", self.delete_brand)
        self.btn_clear = self.create_button("Limpar Campos", "#7f8c8d", "#95a5a6", self.clear_grid)
        self.btn_search = self.create_button("Pesquisar", "#2980b9", "#3498db", self.show_and_filter)

        # Rodapé de ajuda
        self.lbl_help = QtWidgets.QLabel("💡 Dica: Clique no item da grid para carregar os dados para alteração.")
        self.lbl_help.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic; padding:6px;")
        self.lbl_help.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.lbl_help)

        # Layout inputs + botões
        input_h = QtWidgets.QHBoxLayout()
        input_h.setSpacing(10)
        input_h.addWidget(self.name_input, 3)
        input_h.addWidget(self.btn_add)
        input_h.addWidget(self.btn_update)
        input_h.addWidget(self.btn_delete)
        input_h.addWidget(self.btn_clear)
        input_h.addWidget(self.btn_search)
        self.vbox.addLayout(input_h)

        # Permissões
        if self.current_user.get("role") != "admin":
            for btn in [self.btn_add, self.btn_update, self.btn_delete]:
                btn.setEnabled(False)
            self.name_input.setReadOnly(True)

    def create_button(self, text, color, hover_color, callback):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{color};
                color:white;
                padding:10px;
                border-radius:8px;
                font-weight:600;
            }}
            QPushButton:hover {{ background-color:{hover_color}; }}
        """)
        btn.clicked.connect(callback)
        return btn

    # Fade-in
    def showEvent(self, event):
        self.fade_anim.stop()
        self.opacity_effect.setOpacity(0.0)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        super().showEvent(event)

    # Mostrar tabela e filtrar
    def show_and_filter(self):
        self.table.setVisible(True)
        self.filter_table()

    # Limpar campos
    def clear_grid(self):
        self.table.clearSelection()
        self.name_input.clear()

    # Preencher campos
    def fill_fields_from_table(self, row, column):
        self.name_input.setText(self.table.item(row, 1).text())

    # Carregar marcas
    def load_brands(self):
        self.table.setRowCount(0)
        cursor.execute("SELECT * FROM brands")
        for r, row in enumerate(cursor.fetchall()):
            self.table.insertRow(r)
            for c, v in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(v))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(r, c, item)

    # Adicionar marca
    def add_brand(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return

        name = self.name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Nome da marca é obrigatório!")
            return

        # 🔎 Verificar duplicidade
        cursor.execute("SELECT COUNT(*) FROM brands WHERE LOWER(name)=LOWER(?)", (name,))
        if cursor.fetchone()[0] > 0:
            QtWidgets.QMessageBox.warning(self, "Duplicado", f"A marca '{name}' já está cadastrada!")
            return

        cursor.execute("INSERT INTO brands (name) VALUES (?)", (name,))
        conn.commit()
        self.load_brands()
        self.clear_grid()
        QtWidgets.QMessageBox.information(self, "Sucesso", "Marca adicionada com sucesso!")

    # Atualizar marca
    def update_brand(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return

        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione uma marca para atualizar!")
            return

        bid = int(self.table.item(sel, 0).text())
        name = self.name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Nome da marca é obrigatório!")
            return

        # 🔎 Verificar duplicidade (exceto a própria marca)
        cursor.execute("SELECT COUNT(*) FROM brands WHERE LOWER(name)=LOWER(?) AND id<>?", (name, bid))
        if cursor.fetchone()[0] > 0:
            QtWidgets.QMessageBox.warning(self, "Duplicado", f"A marca '{name}' já existe em outro registro!")
            return

        cursor.execute("UPDATE brands SET name=? WHERE id=?", (name, bid))
        conn.commit()
        self.load_brands()
        self.clear_grid()
        self.table.clearSelection()
        QtWidgets.QMessageBox.information(self, "Sucesso", "Marca atualizada com sucesso!")

    # Excluir marca
    def delete_brand(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return

        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione uma marca para excluir!")
            return

        bid = int(self.table.item(sel, 0).text())
        bname = self.table.item(sel, 1).text()

        # 🔎 Verificar se marca está vinculada a produtos
        cursor.execute("SELECT COUNT(*) FROM products WHERE brand_id=?", (bid,))
        count = cursor.fetchone()[0]
        if count > 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Restrição",
                f"A marca '{bname}' não pode ser excluída, pois já está vinculada a {count} produto(s)."
            )
            return

        # Confirmação
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Confirmação")
        msg.setText(f"Tem certeza que deseja excluir a marca '{bname}'?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")
        reply = msg.exec_()
        if reply == QtWidgets.QMessageBox.Yes:
            cursor.execute("DELETE FROM brands WHERE id=?", (bid,))
            conn.commit()
            self.load_brands()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Marca excluída com sucesso!")

    # Filtrar tabela
    def filter_table(self):
        q = self.search_input.text().lower()
        any_visible = False
        for row in range(self.table.rowCount()):
            id_ = self.table.item(row, 0).text().lower()
            name = self.table.item(row, 1).text().lower()
            hide = q not in id_ and q not in name
            self.table.setRowHidden(row, hide)
            if not hide:
                any_visible = True
                # Se nenhum resultado encontrado → alerta
        if not any_visible:
            QtWidgets.QMessageBox.information(
                self,
                "Nenhum resultado",
                "Nenhuma marca encontrada."
            )
        self.table.setVisible(any_visible)
# ---------------------------------------- FIM MARCAS ----------------------------------------------------





# ----------------------------------------- USUÁRIOS -------------------------------------------------------
class UsersWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setSpacing(12)
        self.vbox.setContentsMargins(20, 20, 20, 20)
        self.vbox.setAlignment(QtCore.Qt.AlignTop)  # layout fixo no topo
        
        # ------------------ Título centralizado ------------------
        self.title_label = QtWidgets.QLabel("Gerenciamento de Usuários")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #34495e; margin-bottom: 10px;")
        self.vbox.addWidget(self.title_label)
    
        self.setup_ui()
        self.load_users()

        # Efeito de fade
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QtCore.QPropertyAnimation(self.opacity_effect, b'opacity', self)
        self.fade_anim.setDuration(400)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #d0d7de;
                font-size: 14px;
                gridline-color: #e6e6e6;
                alternate-background-color: #f7f9fc;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #d9ecff;
                color: #1c3f5d;
                border: 1px solid #5dade2;
                border-radius: 4px;
            }

            QTableWidget::item:hover {
                background-color: #eef6ff;
            }

            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-right: 1px solid #1f2d3a;
            }

            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }

            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }

            QScrollBar:vertical {
                width: 10px;
                background: #eef1f4;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #b7c2cc;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #9eabb9;
            }
        """)

    # ------------------- Setup UI -------------------
    def setup_ui(self):
        # Campo de pesquisa
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar usuários...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding:10px;
                border:1px solid #dcdcdc;
                border-radius:12px;
                background-color:#f7f9fc;
            }
            QLineEdit:focus {
                border:1.5px solid #3498db;
                background-color:#ffffff;
            }
        """)
        self.vbox.addWidget(self.search_input)

        # Botão pesquisar
        self.btn_search = self.create_button("Pesquisar", "#2980b9", "#3498db", self.show_and_filter)
        self.vbox.addWidget(self.btn_search)

        # Tabela moderna (inicialmente escondida)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Usuário", "Permissão"])
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color:#34495e;
                color:white;
                font-weight:bold;
                font-size:14px;
                border:none;
                padding:10px;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color:#ffffff; gridline-color:#e0e0e0; border-radius:8px; }
            QTableWidget::item:alternate { background-color:#f4f6f9; }
            QTableWidget::item:selected { background-color:#3498db; color:#ffffff; }
            QTableWidget::item:hover { background-color:#ecf4ff; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setVisible(False)  # <<< tabela começa escondida
        self.vbox.addWidget(self.table)

        # Inputs
        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setPlaceholderText("Usuário")
        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setPlaceholderText("Senha")
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.Password)

        # Combo de role
        self.role_input = QtWidgets.QComboBox()
        self.role_input.addItems(["user", "admin"])

        for widget in [self.user_input, self.pass_input, self.role_input]:
            widget.setStyleSheet("""
                QLineEdit, QComboBox {
                    padding:8px;
                    border:1px solid #d0d0d0;
                    border-radius:8px;
                    background-color:#f9fafb;
                }
                QLineEdit:focus, QComboBox:focus {
                    border:1.5px solid #3498db;
                    background-color:#ffffff;
                }
            """)

        # Botões
        self.btn_add = self.create_button("Adicionar", "#27ae60", "#2ecc71", self.add_user)
        self.btn_update = self.create_button("Atualizar", "#f39c12", "#f5a623", self.update_user)
        self.btn_delete = self.create_button("Excluir", "#c0392b", "#e74c3c", self.delete_user)
        self.btn_clear = self.create_button("Limpar Campos", "#7f8c8d", "#95a5a6", self.clear_grid)

        # Rodapé de ajuda
        self.lbl_help = QtWidgets.QLabel("💡 Dica: Clique duas vezes no item da tabela para carregar os dados.")
        self.lbl_help.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic; padding:6px;")
        self.lbl_help.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.lbl_help)

        # Layout inputs + botões
        input_h = QtWidgets.QHBoxLayout()
        input_h.setSpacing(10)
        input_h.addWidget(self.user_input, 2)
        input_h.addWidget(self.pass_input, 1)
        input_h.addWidget(self.role_input, 1)
        input_h.addWidget(self.btn_add)
        input_h.addWidget(self.btn_update)
        input_h.addWidget(self.btn_delete)
        input_h.addWidget(self.btn_clear)
        self.vbox.addLayout(input_h)

        self.table.cellClicked.connect(self.fill_fields_from_table)

        # Permissões
        if self.current_user.get("role") != "admin":
            for btn in [self.btn_add, self.btn_update, self.btn_delete]:
                btn.setEnabled(False)
            for widget in [self.user_input, self.pass_input, self.role_input]:
                widget.setEnabled(False)

    # ------------------- Botão helper -------------------
    def create_button(self, text, color, hover_color, callback):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{color};
                color:white;
                padding:10px;
                border-radius:8px;
                font-weight:600;
            }}
            QPushButton:hover {{ background-color:{hover_color}; }}
        """)
        btn.clicked.connect(callback)
        return btn

    # ------------------- Fade-in -------------------
    def showEvent(self, event):
        self.fade_anim.stop()
        self.opacity_effect.setOpacity(0.0)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        super().showEvent(event)

    # ------------------- Mostrar e filtrar tabela -------------------
    def show_and_filter(self):
        self.table.setVisible(True)
        self.filter_table()
        # Verificar se existe pelo menos 1 linha visível após o filtro
        any_visible = False
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                any_visible = True
                break

        if not any_visible:
            QtWidgets.QMessageBox.information(
                self,
                "Nenhum resultado",
                "Nenhum usuário encontrado com esse termo de pesquisa."
            )

    # ------------------- Limpar campos -------------------
    def clear_grid(self):
        self.table.clearSelection()
        self.user_input.clear()
        self.pass_input.clear()
        self.role_input.setCurrentIndex(0)

    # ------------------- Preencher campos -------------------
    def fill_fields_from_table(self, row, column):
        username = self.table.item(row, 1).text()
        role = self.table.item(row, 2).text()
        
        self.user_input.setText(username)
        self.pass_input.setText("")
        self.role_input.setCurrentIndex(0 if role == "user" else 1)

    # ------------------- Carregar usuários -------------------
    def load_users(self):
        self.table.setRowCount(0)
        cursor.execute("SELECT id, username, role FROM users")
        for r, row in enumerate(cursor.fetchall()):
            self.table.insertRow(r)
            for c, v in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(v))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(r, c, item)

    # ------------------- Adicionar usuário -------------------
    def add_user(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        role = self.role_input.currentText()
        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Todos os campos são obrigatórios!")
            return
        if len(password) < 3:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Senha deve ter pelo menos 3 caracteres!")
            return
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (username, password, role))
            conn.commit()
            self.load_users()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Usuário adicionado com sucesso!")
        except sqlite3.IntegrityError:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Usuário já existe!")

    # ------------------- Atualizar usuário -------------------
    def update_user(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return
        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um usuário para atualizar!")
            return
        uid = int(self.table.item(sel, 0).text())
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        role = self.role_input.currentText()
        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Todos os campos são obrigatórios!")
            return
        if len(password) < 3:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Senha deve ter pelo menos 3 caracteres!")
            return
        try:
            cursor.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
                           (username, password, role, uid))
            conn.commit()
            self.load_users()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Usuário atualizado com sucesso!")
        except sqlite3.IntegrityError:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Usuário já existe!")

    # ------------------- Excluir usuário -------------------
    def delete_user(self):
        if self.current_user.get("role") != "admin":
            QtWidgets.QMessageBox.warning(self, "Acesso", "Permissão negada.")
            return
        sel = self.table.currentRow()
        if sel < 0:
            QtWidgets.QMessageBox.warning(self, "Alerta", "Selecione um usuário para excluir!")
            return
        uid = int(self.table.item(sel, 0).text())
        username = self.table.item(sel, 1).text()
        if username == "admin":
            QtWidgets.QMessageBox.warning(self, "Alerta", "Não é permitido excluir o admin!")
            return
        msg = QtWidgets.QMessageBox(self)
        
        msg.setWindowTitle("Confirmação")
        msg.setText(f"Tem certeza que deseja excluir o usuário '{username}'?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sim")
        msg.button(QtWidgets.QMessageBox.No).setText("Não")
        if msg.exec_() == QtWidgets.QMessageBox.Yes:
            cursor.execute("DELETE FROM users WHERE id=?", (uid,))
            conn.commit()
            self.load_users()
            self.clear_grid()
            QtWidgets.QMessageBox.information(self, "Sucesso", "Usuário excluído com sucesso!")

    # ------------------- Filtrar tabela -------------------
    def filter_table(self):
        q = self.search_input.text().lower()
        any_visible = False
        for row in range(self.table.rowCount()):
            username = self.table.item(row, 1).text().lower()
            hide = q not in username
            self.table.setRowHidden(row, hide)
            if not hide:
                any_visible = True
        # se nenhum resultado, esconder tabela
        self.table.setVisible(any_visible)
# ----------------------------------------- FIM USUÁRIOS -------------------------------------------------------




# --------------------------------------- JANELA PRINCIPAL -----------------------------------------------------
class ClickableLabel(QtWidgets.QLabel):
    """Label clicável para detectar clique no texto da versão."""
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()


class JanelaPrincipal(QtWidgets.QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("Sistema Corporativo")
        self.resize(1300, 800)
        self.setStyleSheet("background-color:#ecf0f1;")
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)

        hl = QtWidgets.QHBoxLayout(self.central)
        hl.setContentsMargins(0,0,0,0)

        # menu lateral
        menu = QtWidgets.QFrame()
        menu.setFixedWidth(240)
        menu.setStyleSheet("background-color:#2c3e50;")
        mlay = QtWidgets.QVBoxLayout(menu)
        mlay.setContentsMargins(12,12,12,12)
        mlay.setSpacing(8)
        mlay.setAlignment(QtCore.Qt.AlignTop)

        # logo do menu
        logo = QtGui.QPixmap("icons/logo.png")
        logo_label = QtWidgets.QLabel()
        if not logo.isNull():
            logo_label.setPixmap(logo.scaled(140,140, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        logo_label.setAlignment(QtCore.Qt.AlignCenter)
        mlay.addWidget(logo_label)
        
        
        # botões do menu
        self.btn_dashboard = QtWidgets.QPushButton(" Dashboard")
        self.btn_products = QtWidgets.QPushButton(" Produtos")
        self.btn_users = QtWidgets.QPushButton(" Usuários")
        self.btn_clients = QtWidgets.QPushButton(" Clientes")
        self.btn_sales = QtWidgets.QPushButton(" Vendas")
        self.btn_sellers = QtWidgets.QPushButton(" Vendedores")
        self.btn_sales_history = QtWidgets.QPushButton(" Consulta de Vendas")
        self.btn_comissao = QtWidgets.QPushButton(" Comissões")
        self.btn_logout = QtWidgets.QPushButton(" Sair")
        self.btn_relatorio = QtWidgets.QPushButton(" Relatórios")
        self.btn_marcas = QtWidgets.QPushButton(" Marcas")
        self.btn_home = QtWidgets.QPushButton(" Início")
        
        icon_size = QtCore.QSize(20,20)
        self.btn_dashboard.setIcon(QtGui.QIcon("icons/dashboard.png"))
        self.btn_products.setIcon(QtGui.QIcon("icons/products.png"))
        self.btn_users.setIcon(QtGui.QIcon("icons/user.png"))
        self.btn_clients.setIcon(QtGui.QIcon("icons/clients.png"))
        self.btn_sellers.setIcon(QtGui.QIcon("icons/sellers.png"))
        self.btn_logout.setIcon(QtGui.QIcon("icons/logout.png"))
        self.btn_sales.setIcon(QtGui.QIcon("icons/sales.png"))
        self.btn_sales_history.setIcon(QtGui.QIcon("icons/history.png"))
        self.btn_comissao.setIcon(QtGui.QIcon("icons/comissao.png"))
        self.btn_relatorio.setIcon(QtGui.QIcon("icons/relatorio.png"))
        self.btn_marcas.setIcon(QtGui.QIcon("icons/marcas.png"))
        self.btn_home.setIcon(QtGui.QIcon("icons/home.png"))

        for b in (self.btn_dashboard, self.btn_products, self.btn_users, self.btn_clients, self.btn_logout,
                  self.btn_sales, self.btn_sales_history, self.btn_sellers, self.btn_comissao,
                  self.btn_relatorio, self.btn_marcas, self.btn_home):
            
            b.setIconSize(icon_size)
            b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            b.setMinimumHeight(44)
            b.setStyleSheet(self.menu_button_style(False))

        # conexões dos botões
        self.btn_dashboard.clicked.connect(lambda: self.switch_to(0, self.btn_dashboard))
        self.btn_products.clicked.connect(lambda: self.switch_to(1, self.btn_products))
        self.btn_users.clicked.connect(lambda: self.switch_to(2, self.btn_users))
        self.btn_clients.clicked.connect(lambda: self.switch_to(3, self.btn_clients))
        self.btn_sales.clicked.connect(lambda: self.switch_to(5, self.btn_sales))
        self.btn_sellers.clicked.connect(lambda: self.switch_to(4, self.btn_sellers))
        self.btn_sales_history.clicked.connect(lambda: self.switch_to(6, self.btn_sales_history))
        self.btn_comissao.clicked.connect(lambda: self.switch_to(7, self.btn_comissao))
        self.btn_relatorio.clicked.connect(lambda: self.switch_to(8, self.btn_relatorio))
        self.btn_marcas.clicked.connect(lambda: self.switch_to(9, self.btn_marcas))
        self.btn_home.clicked.connect(lambda: self.switch_to(10, self.btn_home))

        self.btn_logout.clicked.connect(self.confirmar_saida)

        # adicionando botões ao menu
        mlay.addWidget(self.btn_dashboard)
        mlay.addWidget(self.btn_products)
        mlay.addWidget(self.btn_users)
        mlay.addWidget(self.btn_clients)   
        mlay.addWidget(self.btn_sellers) 
        mlay.addWidget(self.btn_sales)
        mlay.addWidget(self.btn_sales_history)
        mlay.addWidget(self.btn_comissao)
        mlay.addWidget(self.btn_relatorio)
        mlay.addWidget(self.btn_marcas)
        mlay.addWidget(self.btn_home)
        mlay.addStretch(1)

        # rodapé com usuário e data
        footer = QtWidgets.QLabel(
            f"Usuário: {self.current_user.get('username')} ({self.current_user.get('role')})\n"
            f"Data do Sistema: {datetime.now().strftime('%d/%m/%Y')}"
        )
        footer.setStyleSheet("color:white; padding:8px; font-weight:600; font-size:13px;")
        mlay.addWidget(footer)

        
        
        # label clicável da versão
        self.versao_label = ClickableLabel(f"Versão: {APP_VERSION}")
        self.versao_label.setStyleSheet("color:white; padding-left:8px; font-size:12px;")
        self.versao_label.setAlignment(QtCore.Qt.AlignLeft)

        # conecta clique à função
        self.versao_label.clicked.connect(self.info_versao)

        mlay.addWidget(self.versao_label)

        mlay.addWidget(self.btn_logout)




        # área de conteúdo dos widgets
        self.stack = QtWidgets.QStackedWidget()
        self.dashboard = DashboardWidget()
        self.products = ProductsWidget(self.current_user)
        self.users = UsersWidget(self.current_user)
        self.clients = ClientsWidget(self.current_user)
        self.sellers = SellersWidget(self.current_user)
        self.sales = SalesWidget(self.current_user)
        self.marcas = BrandsWidget(self.current_user)
        self.sales_history = SalesHistoryWidget()
        self.comissao = SalesCommissionWidget()
        self.relatorio = ReportWindow()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.products)
        self.stack.addWidget(self.users)
        self.stack.addWidget(self.clients)
        self.stack.addWidget(self.sellers)
        self.stack.addWidget(self.sales)
        self.stack.addWidget(self.sales_history)
        self.stack.addWidget(self.comissao)
        self.stack.addWidget(self.relatorio)
        self.stack.addWidget(self.marcas)

        self.welcome = WelcomeWidget(self.current_user)
        self.stack.addWidget(self.welcome)

        hl.addWidget(menu)
        hl.addWidget(self.stack, 1)

        self.active_button = None

        # restrição para não admin
        if self.current_user.get("role") != "admin":
            self.btn_users.hide()
            self.btn_comissao.hide()
            self.btn_dashboard.hide()
            self.btn_sellers.hide()
            self.btn_clients.hide()
            self.btn_relatorio.hide()
            self.btn_products.hide()
            self.btn_marcas.hide()

        self.stack.setCurrentWidget(self.welcome)

    # informações da versão
    def info_versao(self):
        QtWidgets.QMessageBox.information(
            self,
            "Informações do Sistema",
            f"Sistema Corporativo\n"
            f"Versão: {APP_VERSION}\n"
            f"Correções de bugs e melhorias de performance.\n\n"
            "Desenvolvido por: AR Tecnologia e Suporte\n"
            "© 2026 - Todos os direitos reservados."
    )

    # voltar boas vindas
    def voltar_boas_vindas(self):
        if self.active_button:
            self.active_button.setStyleSheet(self.menu_button_style(False))
            self.stack.setCurrentWidget(self.welcome)
            self.active_button = None

    def menu_button_style(self, active):
        if active:
            return """
                QPushButton {
                    color:white; background-color:#1f2b38; font-weight:700; padding:12px; text-align:left; border-radius:8px;
                    border: 2px solid #347ab6;
                }
                QPushButton:hover { background-color:#253441; }
            """
        else:
            return """
                QPushButton {
                    color:white; background-color:transparent; font-weight:600; padding:12px; text-align:left;
                }
                QPushButton:hover { background-color:#34495e; border-radius:8px; }
            """

    def abrir_relatorio(self):
        self.relatorio_window = ReportWindow()
        self.relatorio_window.show()

    def switch_to(self, index, button):
        restricted_indexes = {2: "Usuários", 7: "Comissões", 8: "Relatório"}
        if self.current_user.get("role") != "admin" and index in restricted_indexes:
            QtWidgets.QMessageBox.warning(self, "Acesso Negado",
                                          f"Você não tem permissão para acessar {restricted_indexes[index]}.")
            return

        if self.active_button:
            self.active_button.setStyleSheet(self.menu_button_style(False))
        button.setStyleSheet(self.menu_button_style(True))
        self.active_button = button
        self.stack.setCurrentIndex(index)

        if index == 0:
            self.dashboard.refresh()

    def confirmar_saida(self):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Confirmação")
        msg_box.setText("Deseja realmente sair do sistema?")

        btn_sim = msg_box.addButton("Sim", QtWidgets.QMessageBox.YesRole)
        btn_nao = msg_box.addButton("Não", QtWidgets.QMessageBox.NoRole)

        msg_box.setDefaultButton(btn_nao)
        msg_box.exec_()

        if msg_box.clickedButton() == btn_sim:
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

# --------------------------------------- FIM JANELA PRINCIPAL -----------------------------------------------------

            
            
            
            
# --------------------------------------- BOAS VINDAS ------------------------------------------------------------
class WelcomeWidget(QtWidgets.QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setStyleSheet("""
            QWidget { background-color: #ecf0f1; font-family: 'Segoe UI'; }
            QLabel { font-size: 20px; font-weight: 600; color: #2c3e50; }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        self.label = QtWidgets.QLabel(f"Olá, {self.current_user.get('username')}!\nBem-vindo ao sistema.")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)
# --------------------------------------- FIM BOAS VINDAS ---------------------------------------------------------




# --------------------------------------- RELATORIOS -----------------------------------------------------------
class ReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Relatórios")
        self.resize(1200, 700)
        self.layout = QtWidgets.QVBoxLayout(self)

        # ----------------- Estilo Global -----------------
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                font-size: 10pt;
                background-color: #f4f6f9;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton#filterBtn { background-color: #0078d7; }
            QPushButton#filterBtn:hover { background-color: #005a9e; }
            QPushButton#csvBtn { background-color: #28a745; }
            QPushButton#csvBtn:hover { background-color: #218838; }
            QPushButton#pdfBtn { background-color: #dc3545; }
            QPushButton#pdfBtn:hover { background-color: #c82333; }
            QComboBox, QDateEdit {
                background-color: white;
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                font-weight: bold;
            }
        """)

        # ----------------- Filtros -----------------
        filter_frame = QtWidgets.QFrame()
        filter_frame.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; }")
        filter_layout = QtWidgets.QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(12)

        self.combo_report_type = QtWidgets.QComboBox()
        self.combo_report_type.addItems(["Vendas", "Comissão", "Produtos", "Clientes","Vendedores", "Marcas"])
        filter_layout.addWidget(QtWidgets.QLabel("📑 Tipo:"))
        filter_layout.addWidget(self.combo_report_type)

        self.date_from = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.setFixedWidth(120)
        filter_layout.addWidget(QtWidgets.QLabel("📅 De:"))
        filter_layout.addWidget(self.date_from)

        self.date_to = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setFixedWidth(120)
        filter_layout.addWidget(QtWidgets.QLabel("Até:"))
        filter_layout.addWidget(self.date_to)

        self.btn_filter = QtWidgets.QPushButton("🔍 Filtrar")
        self.btn_filter.setObjectName("filterBtn")
        self.btn_filter.clicked.connect(self.load_report)
        filter_layout.addWidget(self.btn_filter)

        self.layout.addWidget(filter_frame)

        # ----------------- Tabela -----------------
        self.table = QtWidgets.QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                selection-background-color: #0078d7;
                selection-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget::item:hover {
                background-color: #eaf3ff;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.table)

        # ----------------- Botões de exportação -----------------
        export_frame = QtWidgets.QFrame()
        export_layout = QtWidgets.QHBoxLayout(export_frame)
        export_layout.setAlignment(QtCore.Qt.AlignRight)
        export_layout.setSpacing(12)

        self.btn_export_csv = QtWidgets.QPushButton("📂 Exportar CSV")
        self.btn_export_csv.setObjectName("csvBtn")
        self.btn_export_csv.clicked.connect(self.export_csv)
        export_layout.addWidget(self.btn_export_csv)

        self.btn_export_pdf = QtWidgets.QPushButton("📄 Exportar PDF")
        self.btn_export_pdf.setObjectName("pdfBtn")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        export_layout.addWidget(self.btn_export_pdf)

        self.layout.addWidget(export_frame)

    # ----------------- Carrega dados na tabela -----------------
    def load_report(self):
        report_type = self.combo_report_type.currentText()
        date_from = self.date_from.date().toString("yyyy-MM-dd") + " 00:00:00"
        date_to = self.date_to.date().toString("yyyy-MM-dd") + " 23:59:59"
        
        # --------- Vendas ---------
        if report_type == "Vendas":
            cursor.execute("""
                SELECT s.id, c.name as Cliente, p.name as Produto, si.subtotal as Valor, s.date, s.status, b.name as Marca
                FROM sales s
                JOIN clients c ON s.client_id = c.id
                JOIN sales_items si ON si.sale_id = s.id
                JOIN products p ON p.id = si.product_id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE s.date BETWEEN ? AND ?
                ORDER BY s.date DESC
            """, (date_from, date_to))
            data = cursor.fetchall()
            headers = ["ID Venda", "Cliente", "Produto", "Valor", "Data", "Status", "Marca"]

        # --------- Comissão ---------
        elif report_type == "Comissão":
            cursor.execute("""
                SELECT s.id, se.name as Vendedor, s.total, se.commission_pct,
                       (s.total * se.commission_pct / 100) as Comissão, s.date
                FROM sales s
                JOIN sellers se ON s.seller_id = se.id
                WHERE s.status='Pago' AND s.date BETWEEN ? AND ?
                ORDER BY s.date DESC
            """, (date_from, date_to))
            data = cursor.fetchall()
            headers = ["ID Venda", "Vendedor", "Total Venda", "% Comissão", "Valor Comissão", "Data"]
        
        # --------- Produtos ---------
        elif report_type == "Produtos":
            cursor.execute("""
                SELECT p.id, p.name, b.name as Marca
                FROM products p
                LEFT JOIN brands b ON p.brand_id = b.id
                ORDER BY p.id DESC
            """)
            data = cursor.fetchall()
            headers = ["ID Produto", "Produto", "Marca"]
        
        # --------- Clientes ---------
        elif report_type == "Clientes":
            cursor.execute("""
                SELECT id, name, email, phone
                FROM clients
                ORDER BY id DESC
            """)
            data = cursor.fetchall()
            headers = ["ID Cliente", "Nome", "E-mail", "Telefone"]
        
        # --------- Vendedores ---------
        elif report_type == "Vendedores":
            cursor.execute("""
                SELECT id, name, email, phone
                FROM sellers
                ORDER BY id DESC
            """)
            data = cursor.fetchall()
            headers = ["ID Vendedor", "Nome", "E-mail", "Telefone"]
        
        # --------- Marcas ---------
        elif report_type == "Marcas":
            cursor.execute("""
                SELECT id, name
                FROM brands
                ORDER BY id DESC
            """)
            data = cursor.fetchall()
            headers = ["ID Marca", "Nome"]
        else:
            data = []
            headers = []
        self.populate_table(data, headers)

    def populate_table(self, data, headers):
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        money_columns = ["Valor", "Total Venda", "Valor Comissão"]
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                header = headers[col_idx]

                # Formata datas
                if isinstance(value, str) and "-" in value and ":" in value:
                    try:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                        value = dt.strftime("%d/%m/%Y")
                    except:
                        pass

                # Formata valores monetários
                if header in money_columns:
                    value = format_currency(value)

                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeRowsToContents()


    # ----------------- Exportar CSV -----------------
    def export_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV (*.csv)")
        if not path:
            return
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            for row in range(self.table.rowCount()):
                writer.writerow([self.table.item(row, col).text() for col in range(self.table.columnCount())])
        QtWidgets.QMessageBox.information(self, "Exportar CSV", "CSV exportado com sucesso!")


    # ----------------- Exportar PDF -----------------
    def export_pdf(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF (*.pdf)")
        if not path:
            return

        doc = SimpleDocTemplate(
            path,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20
        )

        elements = []
        styles = getSampleStyleSheet()


        # ----------------- Cabeçalho com logo -----------------
        try:
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons", "logo.png"))
            if os.path.exists(logo_path):
                logo = Image(logo_path)
                logo.drawHeight = 80
                logo.drawWidth = 80
            else:
                raise FileNotFoundError(f"Logo não encontrado em {logo_path}")

            titulo = Paragraph(f"<b>Relatório - {self.combo_report_type.currentText()}</b>", styles['Title'])
            data_geracao = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal'])

            header_table = Table([[logo, titulo, data_geracao]], colWidths=[80, 400, 200])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('ALIGN', (2,0), (2,0), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12)
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 20))

        except Exception as e:
            print("Erro ao carregar logo:", e)
            elements.append(Paragraph(f"Relatório - {self.combo_report_type.currentText()}", styles['Title']))
            elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 12))


        # ----------------- Tabela de dados -----------------
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = [headers]
        for row in range(self.table.rowCount()):
            linha = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                linha.append(item.text() if item else "")
            data.append(linha)

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0078d7")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6)
        ]))
        elements.append(table)

        try:
            doc.build(elements)
            QtWidgets.QMessageBox.information(self, "Exportar PDF", "PDF exportado com sucesso!")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Erro ao gerar PDF: {str(e)}")
# --------------------------------------- FIM RELATORIOS -----------------------------------------------------------




# -------------------------------------- EXECUÇÃO ----------------------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Segoe UI", 10))
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
# -------------------------------------- FIM EXECUÇÃO ----------------------------------------------
