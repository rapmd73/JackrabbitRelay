#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# JackrabbitRelay CCAPI Broker
# Uses CCAPI for execution + Database for market data

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')

import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from collections import deque
import JRRsupport

# CCAPI Python bindings
import ccapi

# Database reader classes (your existing code)
from db_ohlcv_mssql import (
    MSSQLFeedConfig,
    ReadOnlyOHLCV,
    ReadOnlyTradesAgg
)

class ccapiCrypto:
    """
    CCAPI-based broker for JackrabbitRelay
    - Market Data: Read from MS SQL database
    - Execution: Use CCAPI WebSocket connections
    - Maintains same interface as JRRccxt.py
    """
    
    def __init__(self, Exchange, Config, Active, Notify=True, Sandbox=False, 
                 DataDirectory=None):
        """
        Initialize CCAPI broker
        
        Args:
            Exchange: Exchange name (binance, okx, bybit, etc.)
            Config: Configuration dict
            Active: Active account settings
            Notify: Enable notifications
            Sandbox: Use testnet (not all exchanges support)
            DataDirectory: Data directory path
        """
        self.Exchange = Exchange.lower()
        self.Config = Config
        self.Active = Active
        self.Notify = Notify
        self.Sandbox = Sandbox
        self.DataDirectory = DataDirectory
        self.Log = self.Active['JRLog']
        self.Results = None
        
        # Stable coins for conversion (from JRRccxt)
        self.StableCoinUSD = ['USDT', 'USDC', 'BUSD', 'UST', 'DAI', 'FRAX', 
                              'TUSD', 'USDP', 'GUSD', 'USD']

        self.timeframes = {
            '1m':  '1m',
        }

        # Initialize database connection for market data
        self.db_config = self._init_db_config()
        self.ohlcv_reader = ReadOnlyOHLCV(
            config=self.db_config,
            mode="global",
            global_table="ohlcv",
            schema="dbo"
        )
        self.trades_reader = ReadOnlyTradesAgg(
            config=self.db_config,
            mode="global",
            global_table="ohlcv",
            schema="dbo"
        )
        
        # Initialize CCAPI session for execution
        self.ccapi_session = None
        self.ccapi_event_handler = None
        self.ccapi_running = False
        self.ccapi_thread = None
        
        # Response queues for synchronous calls
        self.response_queues = {}
        self.subscription_active = {}
        
        # Balance cache (updated via CCAPI subscription)
        self.balance_cache = {}
        self.balance_last_update = None
        
        # Position cache (for futures)
        self.position_cache = {}
        self.position_last_update = None
        
        # Markets cache
        self._markets_cache = {}
        
        # Initialize CCAPI
        self._init_ccapi()
        
        # Get markets from database
        self.Markets = self._GetMarkets()
        
        self.Log.Write(f"CCAPI Broker initialized for {self.Exchange}")
    
    def _init_db_config(self) -> MSSQLFeedConfig:
        return MSSQLFeedConfig(
            server="localhost",
            database="BTQ_MarketData",
            username="SA",
            password="q?}33YIToo:H%xue$Kr*",
        )
    
    def _init_ccapi(self):
        """Initialize CCAPI session with event handler"""
        # Create event handler
        self.ccapi_event_handler = CCAPIEventHandler(self)
        
        # Session options
        session_options = ccapi.SessionOptions()
        session_options.warnLateEventMaxMilliseconds = 500
        
        # Session configs (API credentials)
        session_configs = ccapi.SessionConfigs()
        
        # Set credentials based on exchange
        credentials = self._get_api_credentials()
        session_configs.setCredential(credentials)
        
        # Override URLs for sandbox if needed
        if self.Sandbox:
            # Implementation depends on exchange
            pass
        
        # Create CCAPI session
        self.ccapi_session = ccapi.Session(
            session_options,
            session_configs,
            self.ccapi_event_handler
        )
        
        # Start session in separate thread
        self.ccapi_running = True
        self.ccapi_thread = threading.Thread(
            target=self._run_ccapi_session,
            daemon=True
        )
        self.ccapi_thread.start()
        
        # Subscribe to account updates (balance, positions, orders)
        time.sleep(1)  # Wait for session to start
        self._subscribe_account_updates()

    def _ensure_ccapi(self):
        """
        Ensure CCAPI session exists.

        Right now __init__ always calls _init_ccapi(), so this is mostly
        a safety hook for GetBalance/GetPositions. If we ever disable
        auto-init in __init__, this will lazily start the session.
        """
        if self.ccapi_session is None:
            # Only (re)initialize if not already created
            try:
                self._init_ccapi()
            except Exception as e:
                self.Log.Error("_ensure_ccapi", f"Failed to init CCAPI: {e}")

    def _get_api_credentials(self) -> Dict[str, str]:
        """Get API credentials for exchange"""
        exchange_upper = self.Exchange.upper()
        
        credentials = {
            f"{exchange_upper}_API_KEY": self.Active.get('API', ''),
            f"{exchange_upper}_API_SECRET": self.Active.get('SECRET', ''),
        }
        
        # Some exchanges require passphrase
        if 'Passphrase' in self.Active:
            credentials[f"{exchange_upper}_API_PASSPHRASE"] = self.Active['Passphrase']
        
        # Remove empty credentials
        credentials = {k: v for k, v in credentials.items() if v}
        
        return credentials
    
    def _run_ccapi_session(self):
        """Run CCAPI session (blocking call)"""
        try:
            while self.ccapi_running:
                time.sleep(0.1)
        except Exception as e:
            self.Log.Error("CCAPI Session", str(e))
    
    def _subscribe_account_updates(self):
        """Subscribe to account updates (balance, positions, orders)"""
        try:
            # Subscribe to order updates
            subscription_order = ccapi.Subscription(
                self.Exchange,
                "",  # Empty instrument for account-level subscription
                "ORDER_UPDATE",
                "",
                f"order_updates_{self.Exchange}"
            )
            self.ccapi_session.subscribe(subscription_order)
            
            # Subscribe to balance updates (if supported)
            try:
                subscription_balance = ccapi.Subscription(
                    self.Exchange,
                    "",
                    "BALANCE_UPDATE",
                    "",
                    f"balance_updates_{self.Exchange}"
                )
                self.ccapi_session.subscribe(subscription_balance)
            except Exception:
                # Not all exchanges support balance updates
                pass
            
            # Subscribe to position updates (for futures)
            if self.Active.get('Market', 'spot') in ['future', 'swap']:
                try:
                    subscription_position = ccapi.Subscription(
                        self.Exchange,
                        "",
                        "POSITION_UPDATE",
                        "",
                        f"position_updates_{self.Exchange}"
                    )
                    self.ccapi_session.subscribe(subscription_position)
                except Exception:
                    pass
            
            self.Log.Write("Subscribed to account updates via CCAPI")
            
        except Exception as e:
            self.Log.Error("Subscribe Account Updates", str(e))
    
    # ============================================================================
    # MARKET DATA METHODS (READ FROM DATABASE)
    # ============================================================================
    
    def _GetMarkets(self) -> Dict:
        """
        Get markets from database
        Returns dict of market info compatible with CCXT format
        """
        if self._markets_cache:
            return self._markets_cache
        
        try:
            import fast_mssql
            conn_str = self.db_config.connection_string()
            
            # Query distinct symbols for this exchange
            sql = f"""
            SELECT DISTINCT symbol
            FROM dbo.orderbook_snapshots
            WHERE exchange = '{self._quote(self.Exchange)}'
            ORDER BY symbol;
            """
            
            rows = fast_mssql.fetch_data_from_db(conn_str, sql)
            
            markets = {}
            for (symbol,) in rows:
                # Normalize symbol (BTC-USDT -> BTC/USDT)
                normalized = symbol.replace('-', '/')
                base = normalized.split('/')[0]
                quote = normalized.split('/')[1] if '/' in normalized else 'USDT'
                
                markets[normalized] = {
                    'id': symbol,
                    'symbol': normalized,
                    'base': base,
                    'quote': quote,
                    'active': True,
                    'type': self.Active.get('Market', 'spot'),
                    'spot': True,
                    'future': False,
                    'swap': False,
                    'limits': {
                        'amount': {'min': 0.00001, 'max': None},
                        'price': {'min': 0.00001, 'max': None},
                        'cost': {'min': 10.0, 'max': None}
                    },
                    'precision': {
                        'amount': 8,
                        'price': 8
                    }
                }
            
            self._markets_cache = markets
            print(markets)
            return markets
            
        except Exception as e:
            self.Log.Error("GetMarkets", str(e))
            return {}
    
    def GetTicker(self, **kwargs) -> Dict:
        """
        Get latest ticker from database
        Uses latest trades to build bid/ask
        """
        try:
            symbol = kwargs.get('pair', kwargs.get('symbol'))
            if not symbol:
                return {}
            
            # Normalize symbol
            symbol = symbol.replace('/', '-')
            
            # Get latest trades
            now = datetime.now(timezone.utc)
            start = now - timedelta(seconds=10)
            
            trades = self.trades_reader.get_ticks_by_id(
                exchange=self.Exchange,
                symbol=symbol,
                last_id=0,
                limit=100
            )
            
            if trades:
                latest = trades[-1]
                close = float(latest['close'])
                
                # Simple bid/ask from recent prices
                prices = [float(t['close']) for t in trades[-20:]]
                bid = min(prices) if prices else close
                ask = max(prices) if prices else close
                
                return {
                    'DateTime': latest['timestamp'].isoformat() if isinstance(latest['timestamp'], datetime) else None,
                    'Ask': ask,
                    'Bid': bid,
                    'Spread': abs(ask - bid)
                }
            
            # Fallback to OHLCV
            ohlcv = self.ohlcv_reader.get_ohlcv(
                exchange=self.Exchange,
                symbol=symbol,
                timeframe='1m',
                start=start,
                end=now,
                limit=1
            )
            
            if ohlcv:
                close = float(ohlcv[0]['close'])
                return {
                    'DateTime': ohlcv[0]['timestamp'].isoformat(),
                    'Ask': close,
                    'Bid': close,
                    'Spread': 0
                }
            
            raise Exception(f"No ticker data for {symbol}")
            
        except Exception as e:
            self.Log.Error("GetTicker", str(e))
            raise
    
    def GetOHLCV(self, **kwargs) -> List[List]:
        """Get OHLCV data from database"""
        try:
            symbol = kwargs.get('symbol', kwargs.get('pair'))
            timeframe = kwargs.get('timeframe', '1m')
            limit = kwargs.get('limit', 100)
            since = kwargs.get('since')
            
            # Normalize symbol
            symbol = symbol.replace('/', '-')
            
            # Convert since to datetime
            if since:
                start = datetime.fromtimestamp(since / 1000.0, tz=timezone.utc)
            else:
                start = datetime.now(timezone.utc) - timedelta(hours=24)
            
            end = datetime.now(timezone.utc)
            
            # Fetch from database
            rows = self.ohlcv_reader.get_ohlcv(
                exchange=self.Exchange,
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit
            )
            
            # Convert to CCXT format
            ohlcv = []
            for row in rows:
                ts = row['timestamp']
                ts_ms = int(ts.timestamp() * 1000) if isinstance(ts, datetime) else int(ts)
                
                ohlcv.append([
                    ts_ms,
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume'])
                ])
            
            return ohlcv
            
        except Exception as e:
            self.Log.Error("GetOHLCV", str(e))
            return []
    
    # ============================================================================
    # EXECUTION METHODS (USE CCAPI WEBSOCKET)
    # ============================================================================
    def GetBalance(self, **kwargs) -> float:
        """
        Get balance via CCAPI
        Uses cached balance from subscription updates
        """
        try:
            # Lazily start CCAPI if needed
            self._ensure_ccapi()
            if self.ccapi_session is None:
                self.Log.Error("GetBalance", "CCAPI not initialized (execution disabled)")
                return 0.0 if kwargs.get('Base') else {}

            base = kwargs.get('Base')
            
            # If cache is recent (< 5 seconds), use it
            if (self.balance_last_update and 
                (datetime.now(timezone.utc) - self.balance_last_update).total_seconds() < 5):
                if base:
                    return self.balance_cache.get('free', {}).get(base.upper(), 0.0)
                return self.balance_cache
            
            # Otherwise fetch fresh balance
            correlation_id = f"balance_{int(time.time() * 1000)}"
            
            # 👇 IMPORTANT: correlation_id must be passed into the Request
            request = ccapi.Request(
                ccapi.Request.Operation_GET_ACCOUNT_BALANCES,  # in your build this may be Operation_GET_ACCOUNT_BALANCES
                self.Exchange,
                "",
                correlation_id,
            )
            
            # Send request and wait for response
            response = self._send_request_sync(request, correlation_id, timeout=10)
            
            if response:
                # Parse balance response
                balance = self._parse_balance_response(response)
                self.balance_cache = balance
                self.balance_last_update = datetime.now(timezone.utc)
                
                if base:
                    return balance.get('free', {}).get(base.upper(), 0.0)
                return balance
            
            raise Exception("Failed to fetch balance")
            
        except Exception as e:
            self.Log.Error("GetBalance", str(e))
            return 0.0 if kwargs.get('Base') else {}

    def GetPositions(self, **kwargs):
        """
        Get positions via CCAPI (for futures / swaps).
        Uses cached positions, otherwise sync GET_ACCOUNT_POSITIONS request.
        """
        try:
            symbols = kwargs.get('symbols', [])

            # Use cache if its fresh
            if (
                self.position_last_update is not None
                and (datetime.now(timezone.utc) - self.position_last_update).total_seconds() < 5
                and self.position_cache is not None
            ):
                if symbols:
                    symbol = symbols[0] if isinstance(symbols, list) else symbols
                    for pos in self.position_cache:
                        if pos['symbol'] == symbol:
                            contracts = pos['contracts']
                            if pos['side'] == 'short':
                                contracts = -contracts
                            return contracts
                    return 0.0
                return self.position_cache

            # Ensure CCAPI is ready
            self._ensure_ccapi()
            if self.ccapi_session is None:
                raise RuntimeError(
                    "CCAPI session not initialized - execution disabled or misconfigured"
                )

            correlation_id = f"positions_{int(time.time() * 1000)}"

            # Fetch fresh positions
            correlation_id = f"positions_{int(time.time() * 1000)}"

            request = ccapi.Request(
                ccapi.Request.Operation_GET_ACCOUNT_POSITIONS,  # or Operation_GET_ACCOUNT_POSITIONS in your build
                self.Exchange,
                "",
                correlation_id,
            )

            response_event = self._send_request_sync(request, correlation_id, timeout=10)

            if response_event is None:
                raise RuntimeError(f"Timeout waiting for {correlation_id}")

            positions = self._parse_position_response(response_event)
            self.position_cache = positions
            self.position_last_update = datetime.now(timezone.utc)

            if symbols:
                symbol = symbols[0] if isinstance(symbols, list) else symbols
                for pos in positions:
                    if pos['symbol'] == symbol:
                        contracts = pos['contracts']
                        if pos['side'] == 'short':
                            contracts = -contracts
                        return contracts
                return 0.0
            return positions

        except Exception as e:
            self.Log.Error("GetPositions", str(e))
            return 0.0 if kwargs.get('symbols') else []

    def PlaceOrder(self, **kwargs) -> Dict:
        """
        Place order via CCAPI WebSocket
        This is the main execution method
        """
        try:
            pair = kwargs.get('pair')
            order_type = kwargs.get('orderType', 'market').lower()
            action = kwargs.get('action', 'buy').lower()
            amount = float(kwargs.get('amount'))
            price = kwargs.get('price')
            
            # Normalize symbol
            symbol = pair.replace('/', '-')
            
            # Create CCAPI order request
            correlation_id = f"order_{int(time.time() * 1000)}"
            
            request = ccapi.Request(
                ccapi.Request.Operation_CREATE_ORDER,
                self.Exchange,
                symbol,
                correlation_id
            )
            
            # Add order parameters
            params = {
                "SIDE": action.upper(),
                "QUANTITY": str(amount)
            }
            
            if order_type == 'limit' and price:
                params["LIMIT_PRICE"] = str(price)
            
            # Add exchange-specific params if needed
            if 'params' in kwargs:
                params.update(kwargs['params'])
            
            request.appendParam(params)
            
            # Send request via CCAPI
            self.Log.Write(f"Placing {action} {order_type} order: {amount} {symbol}")
            
            response = self._send_request_sync(request, correlation_id, timeout=30)
            
            if response:
                order = self._parse_order_response(response)
                
                if order and order.get('id'):
                    self.Log.Write(f"|- Order Confirmation ID: {order['id']}")
                    
                    # Write order to database for audit trail
                    self._write_order_to_database(order)
                    
                    return order
                
            raise Exception("Order placement failed")
            
        except Exception as e:
            self.Log.Error("PlaceOrder", str(e))
            raise
    
    def CancelOrder(self, **kwargs) -> bool:
        """Cancel order via CCAPI"""
        try:
            order_id = kwargs.get('order_id')
            symbol = kwargs.get('symbol', kwargs.get('pair', ''))
            
            if not order_id:
                raise ValueError("order_id required")
            
            # Normalize symbol
            symbol = symbol.replace('/', '-')
            
            correlation_id = f"cancel_{int(time.time() * 1000)}"
            
            request = ccapi.Request(
                ccapi.Request.Operation_CANCEL_ORDER,
                self.Exchange,
                symbol,
                correlation_id
            )
            
            request.appendParam({
                "ORDER_ID": str(order_id)
            })
            
            self.Log.Write(f"Canceling order {order_id}")
            
            response = self._send_request_sync(request, correlation_id, timeout=10)
            
            if response:
                self.Log.Write(f"|- Order {order_id} cancelled")
                return True
            
            return False
            
        except Exception as e:
            self.Log.Error("CancelOrder", str(e))
            return False
    
    def GetOpenOrders(self, **kwargs) -> List[Dict]:
        """Get open orders via CCAPI"""
        try:
            symbol = kwargs.get('symbol', kwargs.get('pair', ''))
            
            if symbol:
                symbol = symbol.replace('/', '-')
            
            correlation_id = f"open_orders_{int(time.time() * 1000)}"
            
            request = ccapi.Request(
                ccapi.Request.Operation_GET_OPEN_ORDERS,
                self.Exchange,
                symbol,
                correlation_id
            )
            
            response = self._send_request_sync(request, correlation_id, timeout=10)
            
            if response:
                return self._parse_orders_response(response)
            
            return []
            
        except Exception as e:
            self.Log.Error("GetOpenOrders", str(e))
            return []
    
    # ============================================================================
    # CCAPI HELPER METHODS
    # ============================================================================
    
    def _send_request_sync(self, request: ccapi.Request, 
                          correlation_id: str, timeout: int = 10) -> Optional[Any]:
        """
        Send CCAPI request and wait for response synchronously
        Uses threading to block until response received
        """
        # Create response queue
        response_queue = deque(maxlen=1)
        self.response_queues[correlation_id] = response_queue
        
        try:
            self.ccapi_session.sendRequest(request)
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < timeout:
                if response_queue:
                    response = response_queue.popleft()
                    return response
                time.sleep(0.01)
            
            # Timeout
            self.Log.Error("CCAPI Request", f"Timeout waiting for {correlation_id}")
            return None
            
        finally:
            del self.response_queues[correlation_id]

    def _parse_balance_response(self, data) -> Dict:
        """
        Parse balance response.

        `data` is usually a list[list[dict]] created in CCAPIEventHandler._handle_response:
            [
              [ {'ASSET': 'BTC', 'QUANTITY_AVAILABLE_FOR_TRADING': '0.00000192', ...}, ... ],
              [ {...}, ... ]
            ]

        If someone accidentally passes a ccapi.Event, we convert it first.
        """
        balance = {
            'free': {},
            'used': {},
            'total': {},
        }

        try:
            # If we accidentally get a raw Event, convert it here
            if hasattr(data, "getMessageList"):
                py_messages = []
                for msg in data.getMessageList():
                    elem_list = []
                    for el in msg.getElementList():
                        raw_map = el.getNameValueMap()
                        elem_list.append({str(k): str(v) for k, v in raw_map.items()})
                    py_messages.append(elem_list)
                data = py_messages  # now a list[list[dict]]

            # Now assume data = list[list[dict]]
            for msg_elems in data:
                for m in msg_elems:
                    # 1) Asset / currency symbol
                    asset = (
                        m.get("ASSET") or
                        m.get("asset") or
                        m.get("CURRENCY") or
                        m.get("currency") or
                        m.get("symbol") or
                        m.get("coin")
                    )
                    if not asset:
                        continue

                    # 2) Available / total quantities.
                    #    For Binance / ccapi we see:
                    #    - QUANTITY_AVAILABLE_FOR_TRADING
                    #    - QUANTITY_TOTAL
                    avail_s = (
                        m.get("QUANTITY_AVAILABLE_FOR_TRADING")
                        or m.get("AVAILABLE_BALANCE")
                        or m.get("AVAILABLE")
                        or m.get("available")
                        or m.get("FREE")
                        or m.get("free")
                    )
                    total_s = (
                        m.get("QUANTITY_TOTAL")
                        or m.get("TOTAL_BALANCE")
                        or m.get("BALANCE")
                        or m.get("balance")
                        or avail_s
                    )

                    try:
                        available = float(avail_s) if avail_s is not None else 0.0
                    except Exception:
                        available = 0.0

                    try:
                        total = float(total_s) if total_s is not None else available
                    except Exception:
                        total = available

                    used = total - available

                    asset_u = asset.upper()
                    balance['free'][asset_u] = available
                    balance['total'][asset_u] = total
                    balance['used'][asset_u] = used

        except Exception as e:
            self.Log.Error("Parse Balance", f"{e}")

        return balance

    def _parse_position_response(self, event: ccapi.Event) -> List[Dict]:
        """Parse positions response from CCAPI event"""
        positions = []
        
        try:
            for message in event.getMessageList():
                for element in message.getElementList():
                    name_value_map = element.getNameValueMap()
                    
                    position = {
                        'symbol': name_value_map.get('INSTRUMENT', ''),
                        'side': name_value_map.get('POSITION_SIDE', 'long').lower(),
                        'contracts': float(name_value_map.get('POSITION_QUANTITY', 0)),
                        'entryPrice': float(name_value_map.get('POSITION_ENTRY_PRICE', 0)),
                        'unrealizedPnl': float(name_value_map.get('UNREALIZED_PNL', 0))
                    }
                    
                    if position['symbol']:
                        positions.append(position)
            
        except Exception as e:
            self.Log.Error("Parse Positions", str(e))
        
        return positions
    
    def _parse_order_response(self, event: ccapi.Event) -> Dict:
        """Parse order response from CCAPI event"""
        order = {}
        
        try:
            for message in event.getMessageList():
                for element in message.getElementList():
                    name_value_map = element.getNameValueMap()
                    
                    order = {
                        'id': name_value_map.get('ORDER_ID', ''),
                        'clientOrderId': name_value_map.get('CLIENT_ORDER_ID', ''),
                        'symbol': name_value_map.get('INSTRUMENT', ''),
                        'type': name_value_map.get('ORDER_TYPE', 'market').lower(),
                        'side': name_value_map.get('SIDE', '').lower(),
                        'price': float(name_value_map.get('LIMIT_PRICE', 0)) if name_value_map.get('LIMIT_PRICE') else None,
                        'amount': float(name_value_map.get('QUANTITY', 0)),
                        'filled': float(name_value_map.get('CUMULATIVE_FILLED_QUANTITY', 0)),
                        'status': name_value_map.get('STATUS', '').lower(),
                        'timestamp': int(time.time() * 1000),
                        'info': name_value_map
                    }
                    
                    break  # First element only
            
        except Exception as e:
            self.Log.Error("Parse Order", str(e))
        
        return order
    
    def _parse_orders_response(self, event: ccapi.Event) -> List[Dict]:
        """Parse multiple orders response"""
        orders = []
        
        try:
            for message in event.getMessageList():
                for element in message.getElementList():
                    name_value_map = element.getNameValueMap()
                    
                    order = {
                        'id': name_value_map.get('ORDER_ID', ''),
                        'symbol': name_value_map.get('INSTRUMENT', ''),
                        'type': name_value_map.get('ORDER_TYPE', 'market').lower(),
                        'side': name_value_map.get('SIDE', '').lower(),
                        'price': float(name_value_map.get('LIMIT_PRICE', 0)) if name_value_map.get('LIMIT_PRICE') else None,
                        'amount': float(name_value_map.get('QUANTITY', 0)),
                        'filled': float(name_value_map.get('CUMULATIVE_FILLED_QUANTITY', 0)),
                        'remaining': float(name_value_map.get('QUANTITY', 0)) - float(name_value_map.get('CUMULATIVE_FILLED_QUANTITY', 0)),
                        'status': name_value_map.get('STATUS', '').lower()
                    }
                    
                    orders.append(order)
            
        except Exception as e:
            self.Log.Error("Parse Orders", str(e))
        
        return orders
    
    def _write_order_to_database(self, order: Dict):
        """Write executed order to database for audit trail"""
        try:
            import fast_mssql
            conn_str = self.db_config.connection_string()
            
            sql = f"""
            INSERT INTO dbo.orders 
            (id, exchange, account, symbol, side, type, price, amount, 
             filled, remaining, status, timestamp, client_order_id)
            VALUES (
                '{self._quote(order['id'])}',
                '{self._quote(self.Exchange)}',
                '{self._quote(self.Active.get("Account", "main"))}',
                '{self._quote(order['symbol'])}',
                '{self._quote(order['side'])}',
                '{self._quote(order['type'])}',
                {order['price'] if order['price'] else 'NULL'},
                {order['amount']},
                {order['filled']},
                {order['amount'] - order['filled']},
                '{self._quote(order['status'])}',
                GETUTCDATE(),
                '{self._quote(order.get("clientOrderId", ""))}'
            );
            """
            
            fast_mssql.execute_query(conn_str, sql)
            
        except Exception as e:
            self.Log.Error("Write Order to DB", str(e))
        
    def GetMarkets(self):
        self.Markets=self.API("load_markets")
        return self.Markets

    # ============================================================================
    # COMPATIBILITY METHODS (MATCH JRRccxt INTERFACE)
    # ============================================================================
    
    def API(self, function, **kwargs):
        """
        Generic API wrapper to match JRRccxt interface
        Maps function names to appropriate methods
        """
        retry = 0
        RetryLimit = int(self.Active.get('Retry', 3))
        
        done = False
        while not done:
            try:
                if function == 'load_markets':
                    self.Results = self._GetMarkets()
                elif function == 'fetch_balance':
                    self.Results = self.GetBalance(**kwargs)
                elif function == 'fetch_positions':
                    self.Results = self.GetPositions(**kwargs)
                elif function == 'fetch_ohlcv':
                    self.Results = self.GetOHLCV(**kwargs)
                elif function == 'fetch_ticker':
                    self.Results = self.GetTicker(**kwargs)
                elif function == 'fetch_open_orders':
                    self.Results = self.GetOpenOrders(**kwargs)
                elif function == 'create_order':
                    self.Results = self.PlaceOrder(**kwargs)
                elif function == 'cancel_order':
                    self.Results = self.CancelOrder(**kwargs)
                else:
                    raise NotImplementedError(f"Function {function} not implemented")
                
                done = True
                
            except Exception as e:
                retry += 1
                if retry >= RetryLimit:
                    self.Log.Error(function, str(e))
                    done = True
                else:
                    self.Log.Write(f"{function} Retrying ({retry}), {str(e)}")
        
        return self.Results
    
    def GetMinimum(self, **kwargs):
        """Get minimum order size from markets"""
        symbol = kwargs.get('symbol', kwargs.get('pair'))
        if symbol in self.Markets:
            limits = self.Markets[symbol]['limits']
            return limits['amount']['min'], limits['cost']['min']
        return 0.00001, 10.0
    
    def MakeOrphanOrder(self, id, Order):
        """Create orphan order entry (from JRRccxt)"""
        orphanLock = JRRsupport.Locker("OliverTwist")
        Order.pop('Identity', None)
        
        Orphan = {
            'Status': 'Open',
            'Framework': 'ccapi',
            'ID': id,
            'DateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'Order': json.dumps(Order),
            'Class': 'Orphan'
        }
        
        nsf = f"{self.DataDirectory}/OliverTwist.Receiver"
        orphanLock.Lock()
        JRRsupport.AppendFile(nsf, json.dumps(Orphan) + '\n')
        orphanLock.Unlock()
    
    def WriteLedger(self, **kwargs):
        """Write ledger entry (implement as needed)"""
        pass
    
    @staticmethod
    def _quote(s: str) -> str:
        """SQL quote escaping"""
        return str(s).replace("'", "''")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.ccapi_running = False
        if self.ccapi_session:
            try:
                self.ccapi_session.stop()
            except Exception:
                pass


class CCAPIEventHandler(ccapi.EventHandler):
    """
    Event handler for CCAPI events
    Processes responses and subscription data
    """

    def __init__(self, broker):
        super().__init__()
        self.broker = broker

    def processEvent(self, event: ccapi.Event, sessionPtr: ccapi.Session):
        try:
            et = event.getType()
            self.broker.Log.Write(f"CCAPI event type: {et}")

            # simplest & safest: just try all handlers;
            # each decides if the event is relevant.
            self._handle_response(event)
            self._handle_subscription_data(event)
            self._handle_subscription_status(event)
            self._handle_authorization_status(event)

        except Exception as e:
            self.broker.Log.Error("CCAPI Event", f"CCAPI Event failed with: {e}")

        # REQUIRED: SWIG expects a bool
        return True

    def _handle_response(self, event: ccapi.Event):
        """Handle response events: convert ccapi.Event -> pure Python and push to queue."""
        try:
            messages = event.getMessageList()
            if not messages:
                return

            correlation_ids = messages[0].getCorrelationIdList()
            if not correlation_ids:
                return

            correlation_id = correlation_ids[0]

            # Optional: small debug for balances
            if correlation_id.startswith("balance_"):
                try:
                    debug_payload = []
                    for msg in messages:
                        elems = []
                        for el in msg.getElementList():
                            raw_map = el.getNameValueMap()
                            elems.append({str(k): str(v) for k, v in raw_map.items()})
                        debug_payload.append({
                            "type": str(msg.getType()),
                            "corr": list(msg.getCorrelationIdList()),
                            "elements": elems,
                        })
                    # Truncate to keep logs sane
                    self.broker.Log.Write(
                        "CCAPI BALANCE RAW: " + json.dumps(debug_payload)[:2000]
                    )
                except Exception as e:
                    self.broker.Log.Error("Debug Balance", f"{e}")

            # If nobody is waiting on this correlation ID, we are done here
            if correlation_id not in self.broker.response_queues:
                return

            # CRITICAL PART:
            # Convert the ccapi.Event into a pure-Python structure so we dont
            # hold onto C++ objects after this callback returns.
            #
            # py_messages = [
            #   [ {k: v, ...}, {k: v, ...}, ... ],  # message 0 elements
            #   [ {k: v, ...}, ... ],                # message 1 elements
            # ]
            py_messages = []
            for msg in messages:
                elem_list = []
                for el in msg.getElementList():
                    raw_map = el.getNameValueMap()
                    elem_list.append({str(k): str(v) for k, v in raw_map.items()})
                py_messages.append(elem_list)

            # Store pure Python in the queue
            self.broker.response_queues[correlation_id].append(py_messages)

        except Exception as e:
            self.broker.Log.Error("Handle Response", str(e))

    def _handle_subscription_data(self, event: ccapi.Event):
        """Handle subscription data (balances, orders, positions, etc.)."""
        try:
            for message in event.getMessageList():
                message_type_str = str(message.getType())

                # Order updates
                if "ORDER" in message_type_str:
                    self._handle_order_update(message)

                # Balance updates
                elif "BALANCE" in message_type_str:
                    self._handle_balance_update(message)

                # Position updates
                elif "POSITION" in message_type_str:
                    self._handle_position_update(message)

        except Exception as e:
            self.broker.Log.Error("Handle Subscription Data", str(e))

    def _handle_order_update(self, message: ccapi.Message):
        """Handle real-time order updates."""
        try:
            for element in message.getElementList():
                name_value_map = element.getNameValueMap()

                order_id = name_value_map.get('ORDER_ID', '')
                status = name_value_map.get('STATUS', '')

                self.broker.Log.Write(
                    f"Order Update: {order_id} - {status}"
                )
                # TODO :: update DB here

        except Exception as e:
            self.broker.Log.Error("Handle Order Update", str(e))

    def _handle_balance_update(self, message: ccapi.Message):
        """Handle real-time balance updates."""
        try:
            from datetime import datetime, timezone

            for element in message.getElementList():
                name_value_map = element.getNameValueMap()

                asset = name_value_map.get('ASSET', name_value_map.get('CURRENCY', ''))
                available = float(name_value_map.get('AVAILABLE_BALANCE', 0))

                if asset:
                    if 'free' not in self.broker.balance_cache:
                        self.broker.balance_cache['free'] = {}
                    self.broker.balance_cache['free'][asset] = available
                    self.broker.balance_last_update = datetime.now(timezone.utc)

        except Exception as e:
            self.broker.Log.Error("Handle Balance Update", str(e))

    def _handle_position_update(self, message: ccapi.Message):
        """Handle real-time position updates (for futures)."""
        try:
            # TODO :: Parse and update self.broker.position_cache here later
            pass
        except Exception as e:
            self.broker.Log.Error("Handle Position Update", str(e))

    def _handle_subscription_status(self, event: ccapi.Event):
        """Handle subscription status events."""
        try:
            for message in event.getMessageList():
                message_type_str = str(message.getType())
                correlation_ids = message.getCorrelationIdList()

                if message_type_str == "SUBSCRIPTION_STARTED":
                    if correlation_ids:
                        self.broker.subscription_active[correlation_ids[0]] = True
                    self.broker.Log.Write("CCAPI subscription started")

                elif message_type_str == "SUBSCRIPTION_FAILURE":
                    self.broker.Log.Error("CCAPI Subscription", "Subscription failed")

        except Exception as e:
            self.broker.Log.Error("Handle Subscription Status", str(e))

    def _handle_authorization_status(self, event: ccapi.Event):
        """Handle authorization status events."""
        try:
            for message in event.getMessageList():
                message_type_str = str(message.getType())

                if message_type_str == "AUTHORIZATION_SUCCESS":
                    self.broker.Log.Write("CCAPI authorization successful")

                elif message_type_str == "AUTHORIZATION_FAILURE":
                    self.broker.Log.Error("CCAPI Authorization", "Authorization failed")

        except Exception as e:
            self.broker.Log.Error("Handle Authorization", str(e))
