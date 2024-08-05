classDiagram
    class MainWindow {
        +__init__()
        +run_asyncio_loop()
        +load_balances()
        +update_market_data(market_data: List[dict])
        +add_pair()
        +contextMenuEvent(event: QContextMenuEvent)
        +delete_selected_rows()
    }

    class BalancesTableModel {
        +__init__(data: List[List])
        +data(index: QModelIndex, role: int) Any
        +rowCount(index: QModelIndex) int
        +columnCount(index: QModelIndex) int
        +headerData(section: int, orientation: Qt.Orientation, role: int) Any
    }

    class MarketDataTableModel {
        +__init__(data: List[List])
        +data(index: QModelIndex, role: int) Any
        +rowCount(index: QModelIndex) int
        +columnCount(index: QModelIndex) int
        +headerData(section: int, orientation: Qt.Orientation, role: int) Any
        +update_data(new_data: List[dict])
    }

    class WebSocketHandler {
        +__init__(on_data_received)
        +run_asyncio_loop()
        +process_queue()
        +on_message(data: dict)
        +process_message(data: dict)
        +add_pair(pair: str)
        +remove_pair(pair: str)
        +remove_pair_from_market_data(pair: str)
        +delete_selected_rows(pairs: List[str])
        +run_blocking_operation()
        +blocking_operation()
    }

    class GateIOWebSocket {
        +__init__(message_callback: Callable, pairs: Optional[List[str]] = None)
        +on_message(message: str)
        +on_error(error: Exception)
        +on_close()
        +on_open(websocket: websockets.WebSocketClientProtocol)
        +subscribe(pairs: List[str])
        +subscribe_to_pair(pair: str)
        +unsubscribe_from_pair(pair: str)
        +run()
        +is_valid_pair(pair: str)
    }

    class BalancesLoader {
        +load_balances() List[Union[str, float]]
    }

    class GateIOAPI {
        +__init__(api_client: ApiClient)
        +get_balances()
        +get_order_history(currency_pair: str)
        +cancel_order(currency_pair: str, order_id: str)
    }

    class ApiClient {
        +configuration: Configuration
    }

    class SpotApi {
        +list_spot_accounts()
        +list_orders(currency_pair: str, status: str)
        +cancel_order(currency_pair: str, order_id: str)
    }

    class Configuration {
        +key: str
        +secret: str
    }

    MainWindow "1" --> "1" WebSocketHandler : contains
    WebSocketHandler "1" --> "1" GateIOWebSocket : contains

    MainWindow --> WebSocketHandler : update_market_data() calls process_message()
    MainWindow --> WebSocketHandler : add_pair() calls add_pair()
    MainWindow --> WebSocketHandler : delete_selected_rows() calls delete_selected_rows()
    MainWindow --> BalancesLoader : load_balances() calls load_balances()
    WebSocketHandler --> GateIOWebSocket : add_pair() calls subscribe_to_pair()
    WebSocketHandler --> GateIOWebSocket : remove_pair() calls unsubscribe_from_pair()
    WebSocketHandler --> GateIOWebSocket : add_pair() calls is_valid_pair()
    WebSocketHandler --> GateIOWebSocket : on_message() calls on_message()
    GateIOWebSocket --> WebSocketHandler : on_message() calls on_message()

    MainWindow o-- BalancesTableModel : uses
    MainWindow o-- MarketDataTableModel : uses
    MainWindow o-- load_balances : uses

    MainWindow <|-- QApplication : uses
    MainWindow <|-- QMainWindow : inherits

    WebSocketHandler <|-- ThreadPoolExecutor : uses

    BalancesLoader --> GateIOAPI : uses
    GateIOAPI --> SpotApi : uses list_spot_accounts()
    GateIOAPI --> SpotApi : uses list_orders()
    GateIOAPI --> SpotApi : uses cancel_order()

    Configuration o-- ApiClient : configures
    ApiClient o-- SpotApi : uses
    GateIOAPI o-- ApiClient : uses
    GateIOAPI o-- SpotApi : uses
