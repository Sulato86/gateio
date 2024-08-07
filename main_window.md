```mermaid
classDiagram
    class MainWindow {
        - ws_handler: WebSocketHandler
        - market_data_model: PandaMarketData
        + __init__()
        + load_balances()
        + on_data_received(market_data)
        + add_pair()
        + import_market_data()
    }

    class BalancesTableModel {
        + __init__(data)
        + data(index, role)
        + rowCount(index)
        + columnCount(index)
        + headerData(section, orientation, role)
    }

    class PandaMarketData {
        +__init__(data)
        +data(index, role)
        +update_data(new_data)
        +rowCount(index)
        +columnCount(index)
        +headerData(section, orientation, role)
        +import_data(headers, new_data)
        +get_data(row, column)
    }

    class WebSocketHandler {
        - on_data_received: Callable
        - market_data: List
        - pairs: set
        - deleted_pairs: set
        - data_queue: asyncio.Queue
        - gateio_ws: GateIOWebSocket
        - loop: asyncio.AbstractEventLoop
        + __init__(on_data_received: Callable)
        + start()
        + run_loop()
        + process_queue()
        + on_message(data)
        + process_message(data)
        + add_pair(pair: str)
        + add_pairs_from_csv(pairs: List[str])
        + remove_pair(pair: str)
        + remove_pair_from_market_data(pair: str)
        + delete_selected_rows(pairs: List[str])
        + run_blocking_operation()
        + blocking_operation()
    }

    class GateIOWebSocket {
        - message_callback: Callable
        - ws_url: str
        - pairs: List[str]
        - websocket: websockets.WebSocketClientProtocol
        - pending_pairs: List[str]
        - connected: bool
        + __init__(message_callback: Callable, pairs: Optional[List[str]] = None)
        + on_message(message: str)
        + on_error(error: Exception)
        + on_close()
        + on_open(websocket: websockets.WebSocketClientProtocol)
        + subscribe(pairs: List[str])
        + subscribe_to_pair(pair: str)
        + unsubscribe_from_pair(pair: str)
        + run()
        + is_valid_pair(pair)
    }

    class csv_handler {
        +export_csv(tableView) void
        +import_csv(tableView) tuple
    }

    class balances_loader {
        + load_balances() List[Union[str, float]]
    }

    class GateIOAPI {
        + __init__(api_client)
        + get_balances() dict
        + get_order_history(currency_pair) list
        + cancel_order(currency_pair, order_id) dict
    }

    class api_client {
        + Configuration
        + ApiClient
    }

    %% Hubungan antar kelas
    MainWindow "1" *-- "1" BalancesTableModel: uses
    MainWindow "1" *-- "1" PandaMarketData: uses
    MainWindow "1" *-- "1" WebSocketHandler: uses
    WebSocketHandler "1" *-- "1" GateIOWebSocket: uses
    MainWindow "1" *-- "1" csv_handler : uses
    MainWindow "1" *-- "1" balances_loader : uses
    balances_loader "1" *-- "1" GateIOAPI: uses
    GateIOAPI "1" *-- "1" api_client: uses

    %% Spesifikasi fungsi yang berhubungan
    
    MainWindow ..> BalancesTableModel : load_balances() creates

    MainWindow ..> PandaMarketData : __init__() creates
    MainWindow ..> PandaMarketData : on_data_received() calls update_data()
    MainWindow ..> PandaMarketData : import_market_data() calls import_data()

    MainWindow ..> WebSocketHandler : __init__() calls start()
    MainWindow ..> WebSocketHandler : add_pair() calls add_pair()
    MainWindow ..> WebSocketHandler : import_market_data() calls add_pairs_from_csv()

    WebSocketHandler ..> MainWindow : on_message() calls on_data_received()
    WebSocketHandler ..> MainWindow : market_data_updated emits signal

    WebSocketHandler ..> GateIOWebSocket : on_message() calls on_message()
    WebSocketHandler ..> GateIOWebSocket : add_pair() calls is_valid_pair()
    WebSocketHandler ..> GateIOWebSocket : add_pair() calls subscribe_to_pair()
    WebSocketHandler ..> GateIOWebSocket : remove_pair() calls unsubscribe_from_pair()

    WebSocketHandler ..> WebSocketHandler : remove_pair_from_market_data() calls market_data_updated.emit()

    GateIOWebSocket ..> WebSocketHandler : on_message() calls message_callback()
    GateIOWebSocket ..> GateIOWebSocket : run() calls on_open()
    GateIOWebSocket ..> GateIOWebSocket : run() calls on_message()
    GateIOWebSocket ..> GateIOWebSocket : on_open() calls subscribe()
    GateIOWebSocket ..> GateIOWebSocket : subscribe_to_pair() calls subscribe()
    GateIOWebSocket ..> GateIOWebSocket : unsubscribe_from_pair() calls unsubscribe()

    MainWindow ..> csv_handler : import_market_data() calls import_csv()
    MainWindow ..> csv_handler : pushButton_exportmarketdata.clicked() calls export_csv()
    MainWindow ..> csv_handler : pushButton_importmarketdata.clicked() calls import_csv()

    MainWindow ..> MainWindow : on_data_received() updates UI

    MainWindow ..> balances_loader : load_balances() calls load_balances()
    balances_loader ..> GateIOAPI : load_balances() calls get_balances()
