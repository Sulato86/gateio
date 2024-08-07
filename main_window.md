classDiagram
    class MainWindow {
        +__init__()
        +load_balances()
        +on_data_received(market_data)
        +add_pair()
        +import_market_data()
        +setupUi()
    }

    class WebSocketHandler {
        +pyqtSignal market_data_updated
        -asyncio.Queue data_queue
        -set pairs
        -set deleted_pairs
        -list market_data
        -Callable on_data_received
        -GateIOWebSocket gateio_ws
        -asyncio.AbstractEventLoop loop
        +__init__(on_data_received)
        +start()
        +run_loop()
        +async process_queue()
        +async on_message(data)
        +process_message(data)
        +async add_pair(pair)
        +async add_pairs_from_csv(pairs)
        +remove_pair(pair)
        +remove_pair_from_market_data(pair)
        +delete_selected_rows(pairs)
        +async run_blocking_operation()
        +blocking_operation()
    }

    class MarketDataTableModel {
        +__init__(data)
        +data(index, role)
        +update_data(new_data)
        +rowCount(index)
        +columnCount(index)
        +headerData(section, orientation, role)
        +import_data(headers, new_data)
        +get_data(row, column)
    }

    class GateIOWebSocket {
        -Callable message_callback
        -str ws_url
        -list pairs
        -WebSocketClientProtocol websocket
        -list pending_pairs
        -bool connected
        +__init__(message_callback, pairs)
        +async on_message(message)
        +async on_error(error)
        +async on_close()
        +async on_open(websocket)
        +async subscribe(pairs)
        +async subscribe_to_pair(pair)
        +async unsubscribe_from_pair(pair)
        +async run()
        +async is_valid_pair(pair)
    }

    class BalancesLoader {
        +load_balances() List~Union[str, float]~
    }

    class BalancesTableModel {
        +__init__(data)
        +data(index, role)
        +rowCount(index)
        +columnCount(index)
        +headerData(section, orientation, role)
    }

    class CSVHandler {
        +get_marketdata(tableView)
        +export_csv(tableView)
        +import_csv(tableView) returns (headers, data)
    }

    %% Relationships
    MainWindow --> MarketDataTableModel : uses
    MainWindow ..> MarketDataTableModel : on_data_received() calls update_data()
    MainWindow ..> MarketDataTableModel : import_market_data() calls import_data()
    MainWindow ..> MarketDataTableModel : __init__() initializes

    MainWindow --> WebSocketHandler : uses
    MainWindow ..> WebSocketHandler : add_pair() calls add_pair()
    MainWindow ..> WebSocketHandler : import_market_data() calls add_pairs_from_csv()
    MainWindow ..> WebSocketHandler : __init__() initializes
    WebSocketHandler ..> MainWindow : market_data_updated signal
    WebSocketHandler ..> MainWindow : on_data_received callback

    WebSocketHandler --> GateIOWebSocket : uses
    WebSocketHandler ..> GateIOWebSocket : on_message() callback
    WebSocketHandler ..> GateIOWebSocket : add_pair() calls is_valid_pair()
    WebSocketHandler ..> GateIOWebSocket : add_pair() calls subscribe_to_pair()
    WebSocketHandler ..> GateIOWebSocket : remove_pair() calls unsubscribe_from_pair()

    MainWindow --> BalancesLoader : uses
    MainWindow ..> BalancesLoader : load_balances() calls load_balances()

    MainWindow --> BalancesTableModel : uses
    MainWindow ..> BalancesTableModel : load_balances() calls __init__()
    MainWindow ..> BalancesTableModel : load_balances() calls setModel()
    MainWindow ..> BalancesTableModel : load_balances() calls headerData()

    MainWindow --> CSVHandler : uses
    MainWindow ..> CSVHandler : import_market_data() calls import_csv()
    MainWindow ..> CSVHandler : pushButton_exportmarketdata calls export_csv()
