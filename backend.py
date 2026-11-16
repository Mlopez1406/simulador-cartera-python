"""Servicios de cartera. SQLite confirma saldo, posiciones e historial conjuntamente."""
import csv
from contextlib import contextmanager
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time
from datetime import datetime

from modulos.portfolio_manager import comprar_accion, vender_accion, ingresar_saldo, calcular_resumen

ROOT = Path(__file__).resolve().parent


class PortfolioService:
    def __init__(self, database=None):
        self.database = Path(database or os.getenv('CARTERA_DB', ROOT / 'datos' / 'cartera_web.sqlite3'))
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS cuenta (id INTEGER PRIMARY KEY, estado TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY, fecha_hora TEXT, operacion TEXT, ticker TEXT, cantidad INTEGER, precio_unitario REAL, total REAL)')
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM cuenta').fetchone() is None:
                state = json.loads((ROOT / 'datos/cartera.json').read_text(encoding='utf-8'))
                db.execute('INSERT INTO cuenta VALUES (1, ?)', (json.dumps(state),))
                with (ROOT / 'datos/transacciones.csv').open(encoding='utf-8', newline='') as f:
                    for row in csv.DictReader(f, delimiter=';'):
                        db.execute('INSERT INTO movimientos (fecha_hora,operacion,ticker,cantidad,precio_unitario,total) VALUES (?,?,?,?,?,?)', tuple(row[k] for k in ('fecha_hora','operacion','ticker','cantidad','precio_unitario','total')))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def state(self):
        with self.connect() as db:
            return json.loads(db.execute('SELECT estado FROM cuenta WHERE id=1').fetchone()[0])

    def history(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT fecha_hora,operacion,ticker,cantidad,precio_unitario,total FROM movimientos ORDER BY id DESC')]

    def execute(self, operation, ticker='CASH', quantity=1, price=0):
        ticker = validate_ticker(ticker)
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError('La cantidad debe ser un número entero positivo.')
        if not math.isfinite(price) or price <= 0:
            raise ValueError('El importe debe ser positivo y finito.')
        if operation not in ('COMPRA', 'VENTA', 'INGRESO'):
            raise ValueError('Operación desconocida.')
        if operation == 'INGRESO' and (ticker != 'CASH' or quantity != 1):
            raise ValueError('Ingreso no válido.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            state = json.loads(db.execute('SELECT estado FROM cuenta WHERE id=1').fetchone()[0])
            if operation == 'INGRESO':
                ok, message = ingresar_saldo(state, price)
            else:
                fn = comprar_accion if operation == 'COMPRA' else vender_accion
                ok, message = fn(state, ticker, quantity, price)
            if not ok:
                raise ValueError(message)
            state['saldo_euros'] = round(state['saldo_euros'], 2)
            db.execute('UPDATE cuenta SET estado=? WHERE id=1', (json.dumps(state),))
            db.execute('INSERT INTO movimientos (fecha_hora,operacion,ticker,cantidad,precio_unitario,total) VALUES (?,?,?,?,?,?)', (datetime.now().isoformat(sep=' ', timespec='seconds'), operation,ticker,quantity,price,round(quantity*price,2)))
        return message

    def summary(self):
        return calcular_resumen(self.state(), lambda t: quote(t)[:2])

    def export_csv(self):
        result = io.StringIO()
        fields = ['fecha_hora','operacion','ticker','cantidad','precio_unitario','total']
        writer = csv.DictWriter(result, fields, delimiter=';')
        writer.writeheader()
        writer.writerows(self.history())
        return result.getvalue().encode('utf-8-sig')


def validate_ticker(ticker):
    ticker = ticker.strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,11}', ticker):
        raise ValueError('Introduce un ticker válido, por ejemplo AAPL o MSFT.')
    return ticker


def quote(ticker):
    """Precios de referencia reproducibles; no se presentan como mercado actual."""
    ticker = validate_ticker(ticker)
    data = json.loads((ROOT / 'datos/cache_cotizaciones.json').read_text(encoding='utf-8'))
    defaults = {'MSFT': 420.0, 'AMZN': 210.0, 'GOOGL': 180.0, 'META': 580.0}
    price = data.get(ticker, {}).get('precio', defaults.get(ticker))
    if price is None:
        raise ValueError('No hay precio de demostración para ese ticker. Usa uno de los símbolos disponibles.')
    return float(price), 'DEMO · referencia fija', time.time()
