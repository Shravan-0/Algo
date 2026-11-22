
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def fetch_data():
    # Initialize MT5 connection
    if not mt5.initialize():
        logger.error(f"MetaTrader5 initialization failed, error code: {mt5.last_error()}")
        return

    logger.info("MetaTrader5 initialized successfully")
    
    symbol = "XAUUSD"
    logger.info(f"Selected symbol: {symbol}")
    
    timeframe = mt5.TIMEFRAME_H1
    
    # Calculate time range: 5 years from now
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)
    
    logger.info(f"Downloading data for {symbol} from {start_date} to {end_date}...")
    
    # Copy rates
    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    
    # Shutdown MT5 connection
    mt5.shutdown()
    logger.info("MetaTrader5 shutdown")

    if rates is None or len(rates) == 0:
        logger.error("No data downloaded. Check symbol name or connection.")
        return

    logger.info(f"Data downloaded: {len(rates)} rows")

    # Create DataFrame
    df = pd.DataFrame(rates)
    
    # Convert time in seconds to datetime
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Set time as index
    df.set_index('time', inplace=True)
    
    # Keep specific columns
    required_columns = ['open', 'high', 'low', 'close', 'tick_volume']
    
    # Check if columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
         logger.warning(f"Missing columns: {missing_cols}. Available columns: {df.columns.tolist()}")

    # Select available required columns
    df = df[[col for col in required_columns if col in df.columns]]
    
    # Define output path
    output_dir = os.path.join("data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "XAUUSD_H1.csv")
    
    try:
        df.to_csv(output_file)
        logger.info(f"File saved successfully to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")

if __name__ == "__main__":
    try:
        fetch_data()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
