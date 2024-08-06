```mermaid
classDiagram
    class WebSocketHandler {
        - market_data: List
        - pairs: Set
        - deleted_pairs: Set
        - data_queue: asyncio.Queue
        - gateio_ws: GateIOWebSocket
        - loop: asyncio.AbstractEventLoop
        + __init__(on_data_received: Callable)
        + on_message(message: str)
        + process_message(data: dict)
        + add_pair(pair: str)
        + delete_selected_rows(pairs: List[str])
        + remove_pair(pair: str)
        + remove_pair_from_market_data(pair: str)
        + add_pairs_from_csv(pairs: List[str])
        + start()
        + run_loop()
        + process_queue()
        + run_blocking_operation()
        + blocking_operation()
    }

    class MainWindow {
        - market_data: List
        - market_data_model: MarketDataTableModel
        - balances_model: BalancesTableModel
        - websocket_handler: WebSocketHandler
        - csv_handler: CsvHandler
        + __init__()
        + load_balances()
        + update_market_data(data: List)
        + on_data_received(market_data: List)
        + add_pair()
        + export_csv()
        + import_market_data()
        + run_asyncio_loop()
        + contextMenuEvent(event: QContextMenuEvent)
        + delete_selected_rows()
        + handle_header_clicked(logicalIndex: int)
    }

    class Ui_MainWindow {
        + setupUi(MainWindow)
    }

    class GateIOWebSocket {
        - message_callback: Callable
        - ws_url: str
        - pairs: List[str]
        - websocket: WebSocketClientProtocol
        - connected: bool
        + __init__(message_callback: Callable, pairs: List[str])
        + on_message(message: str)
        + on_error(error: Exception)
        + on_close()
        + on_open(websocket: WebSocketClientProtocol)
        + subscribe(pairs: List[str])
        + subscribe_to_pair(pair: str)
        + unsubscribe_from_pair(pair: str)
        + is_valid_pair(pair: str)
        + run()
    }

    class MarketDataTableModel {
        - _data: List
        - _headers: List[str]
        + __init__(data: List)
        + data(index: QModelIndex, role: int): Any
        + rowCount(index: QModelIndex): int
        + columnCount(index: QModelIndex): int
        + headerData(section: int, orientation: Qt.Orientation, role: int): Any
        + update_data(new_data: List)
        + import_data(headers: List[str], new_data: List[List[str]])
        + remove_rows(rows: List[int])
        + get_data(row: int, column: int): Any
        + find_row_by_pair(pair: str): int
    }

    class BalancesTableModel {
        - balances: List
        + __init__(balances: List)
        + data(index: QModelIndex, role: int)
        + rowCount(index: QModelIndex)
        + columnCount(index: QModelIndex)
        + headerData(section: int, orientation: Qt.Orientation, role: int)
    }

    class CsvHandler {
        + export_csv(view: QTableView)
        + import_csv(view: QTableView) : List
        + get_marketdata() : List
    }

    class BalancesLoader {
        + load_balances() : List
    }

    class GateIOAPI {
        - api_client: ApiClient
        - spot_api: SpotApi
        + __init__(api_client: ApiClient)
        + get_balances()
        + get_order_history(currency_pair: str)
        + place_order(order: dict)
        + cancel_order(order_id: str)
    }

    class SortableProxyModel {
        + lessThan(left: QModelIndex, right: QModelIndex) : bool
    }

    MainWindow --> WebSocketHandler : on_data_received() calls process_message()
    MainWindow --> WebSocketHandler : add_pair() calls add_pair()
    MainWindow --> WebSocketHandler : delete_selected_rows() calls delete_selected_rows()
    MainWindow --> WebSocketHandler : import_market_data() calls add_pairs_from_csv()
    MainWindow --> BalancesLoader : load_balances() calls load_balances()
    MainWindow --> BalancesTableModel : load_balances() creates BalancesTableModel
    MainWindow --> MarketDataTableModel : update_market_data() calls update_data()
    MainWindow --> MarketDataTableModel : import_market_data() calls import_data()
    MainWindow --> CsvHandler : export_csv() calls export_csv(tableView)
    MainWindow --> CsvHandler : import_market_data() calls import_csv(tableView)
    MainWindow --> SortableProxyModel : uses sortable_proxy_model
    MainWindow --> Ui_MainWindow : setupUi() calls setupUi()
    CsvHandler --> MainWindow : import_csv() returns headers, data
    CsvHandler --> MainWindow : export_csv() calls get_marketdata(tableView)
    WebSocketHandler --> GateIOWebSocket : add_pair() calls subscribe()
    WebSocketHandler --> GateIOWebSocket : remove_pair() calls unsubscribe()
    WebSocketHandler --> GateIOWebSocket : add_pair() calls is_valid_pair()
    WebSocketHandler --> GateIOWebSocket : on_message() calls on_message()
    GateIOWebSocket --> WebSocketHandler : on_message() calls on_message()
    BalancesLoader --> GateIOAPI : load_balances() calls get_balances()
    
