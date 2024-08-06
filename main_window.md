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
        + process_data()
        + add_pair(pair: str)
        + delete_selected_rows(pairs: List[str])
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
        + on_market_data_updated(data: List)
        + add_pair()
        + export_csv()
        + import_market_data()
        + run_asyncio_loop()
        + contextMenuEvent()
        + delete_selected_rows()
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
        + unsubscribe(pairs: List[str])
        + is_valid_pair(pair: str)
        + run()
    }

    class MarketDataTableModel {
        - data: List
        + __init__(data: List)
        + update_data(data: List)
        + import_data(headers: List[str], data: List[List[str]])
        + data(index: QModelIndex, role: int)
        + rowCount(index: QModelIndex)
        + columnCount(index: QModelIndex)
        + headerData(section: int, orientation: Qt.Orientation, role: int)
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

    MainWindow --> WebSocketHandler : update_market_data() calls process_data()
    MainWindow --> WebSocketHandler : add_pair() calls add_pair()
    MainWindow --> WebSocketHandler : delete_selected_rows() calls delete_selected_rows()
    MainWindow --> BalancesLoader : load_balances() calls load_balances()
    MainWindow --> CsvHandler : export_csv() calls export_csv()
    MainWindow --> CsvHandler : import_market_data() calls import_csv()
    MainWindow --> BalancesTableModel : load_balances() creates BalancesTableModel
    MainWindow --> MarketDataTableModel : update_market_data() calls update_data()
    MainWindow --> MarketDataTableModel : import_market_data() calls import_data()
    WebSocketHandler --> GateIOWebSocket : add_pair() calls subscribe()
    WebSocketHandler --> GateIOWebSocket : remove_pair() calls unsubscribe()
    WebSocketHandler --> GateIOWebSocket : add_pair() calls is_valid_pair()
    WebSocketHandler --> GateIOWebSocket : on_message() calls on_message()
    GateIOWebSocket --> WebSocketHandler : on_message() calls on_message()
    BalancesLoader --> GateIOAPI : load_balances() calls get_balances()
    MainWindow --> Ui_MainWindow : Inherits setupUi()
