import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import yfinance as yf
from datetime import datetime, timedelta
import data_manager

class IPOPredictor:
    def __init__(self):
        self.reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.clf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoders = {}
        self.feature_cols = [
            'Sector', 'Issue Size (Cr)', 'QIB Subscription', 
            'NII Subscription', 'Retail Subscription', 'GMP_Pct'
        ]
        self.is_trained = False

    def train(self):
        """Train regression and classification models on historical IPO data."""
        try:
            df = data_manager.load_historical_data().copy()
            
            # Feature engineering: GMP as % of Issue Price
            # Avoid divide by zero
            df['GMP_Pct'] = np.where(
                df['Issue Price'] > 0, 
                (df['Avg Pre-Listing GMP'] / df['Issue Price']) * 100, 
                0.0
            )
            
            # Encode Sector
            le = LabelEncoder()
            df['Sector_Encoded'] = le.fit_transform(df['Sector'])
            self.label_encoders['Sector'] = le
            
            # Prepare X and y
            X = df[['Sector_Encoded', 'Issue Size (Cr)', 'QIB Subscription', 
                   'NII Subscription', 'Retail Subscription', 'GMP_Pct']].copy()
            
            # Listing Gain % is target for regression
            y_reg = df['Listing Gain (%)']
            
            # Classification target: Bullish (>20%), Neutral (0% to 20%), Risky (<0%)
            y_clf = np.where(y_reg > 20.0, 'Bullish', np.where(y_reg >= 0.0, 'Neutral', 'Risky'))
            
            # Train models
            self.reg_model.fit(X, y_reg)
            self.clf_model.fit(X, y_clf)
            self.is_trained = True
            print("ML Models trained successfully!")
        except Exception as e:
            print(f"Error training ML models: {e}")

    def predict(self, sector, issue_size, qib_sub, nii_sub, retail_sub, gmp):
        """Predict listing gain and risk classification for a new IPO."""
        if not self.is_trained:
            self.train()
            
        try:
            # Map sector encoding
            le = self.label_encoders.get('Sector')
            if sector in le.classes_:
                sector_encoded = le.transform([sector])[0]
            else:
                # Handle unseen sector
                sector_encoded = len(le.classes_)
                
            # GMP Pct estimate
            gmp_pct = gmp # Input should already be pre-listing expected gain or GMP %
            
            input_df = pd.DataFrame([[
                sector_encoded, issue_size, qib_sub, nii_sub, retail_sub, gmp_pct
            ]], columns=['Sector_Encoded', 'Issue Size (Cr)', 'QIB Subscription', 
                         'NII Subscription', 'Retail Subscription', 'GMP_Pct'])
            
            pred_gain = self.reg_model.predict(input_df)[0]
            pred_class = self.clf_model.predict(input_df)[0]
            
            # Calculate prediction confidence based on tree votes
            clf_probs = self.clf_model.predict_proba(input_df)[0]
            confidence = float(np.max(clf_probs))
            
            return {
                "predicted_gain_pct": round(pred_gain, 2),
                "classification": pred_class,
                "confidence": round(confidence * 100, 1)
            }
        except Exception as e:
            print(f"Error running prediction: {e}")
            # Dynamic fallback baseline logic if ML errors out
            fallback_gain = (gmp * 0.7) + (qib_sub * 0.2)
            fallback_class = "Bullish" if fallback_gain > 20 else ("Neutral" if fallback_gain >= 0 else "Risky")
            return {
                "predicted_gain_pct": round(fallback_gain, 2),
                "classification": fallback_class,
                "confidence": 75.0
            }


def get_sector_default_returns(sector):
    """Fallback annual return and volatility based on sector profile."""
    profiles = {
        "Technology": {"return": 0.22, "volatility": 0.28},
        "Financial Services": {"return": 0.16, "volatility": 0.20},
        "Renewable Energy": {"return": 0.28, "volatility": 0.35},
        "Manufacturing": {"return": 0.18, "volatility": 0.22},
        "Healthcare": {"return": 0.15, "volatility": 0.18},
        "Consumer Goods": {"return": 0.14, "volatility": 0.16},
        "Infrastructure": {"return": 0.12, "volatility": 0.24}
    }
    return profiles.get(sector, {"return": 0.15, "volatility": 0.22})


def run_monte_carlo(selected_tickers, allocation_pcts, total_investment, num_simulations=1000, horizon_days=252):
    """
    Perform multi-asset Monte Carlo simulation.
    1. Fetch historical returns using yfinance or fall back to sector parameters.
    2. Calculate covariance matrix.
    3. Generate 1000 simulated paths for the portfolio.
    4. Calculate CAGR, Sharpe, Value at Risk (VaR), and expected return.
    """
    num_assets = len(selected_tickers)
    if num_assets == 0:
        return None
        
    df_historical = data_manager.load_historical_data()
    
    # We will get tickers
    tickers_list = []
    sector_list = []
    for ticker in selected_tickers:
        match = df_historical[df_historical['Ticker'] == ticker]
        if not match.empty:
            tickers_list.append(ticker)
            sector_list.append(match.iloc[0]['Sector'])
        else:
            tickers_list.append(ticker)
            sector_list.append("Technology")
            
    # Try fetching 1 year historical closing prices for listed stocks
    price_data = pd.DataFrame()
    
    # Download past data for standard covariance calculation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    valid_tickers = [t for t in tickers_list if t.endswith('.NS')]
    
    if valid_tickers:
        try:
            downloaded = yf.download(valid_tickers, start=start_date, end=end_date, progress=False)
            if 'Close' in downloaded.columns:
                price_data = downloaded['Close']
            elif len(valid_tickers) == 1:
                price_data = pd.DataFrame(downloaded['Close'])
                price_data.columns = valid_tickers
        except Exception as e:
            print(f"Error fetching historical price data for Monte Carlo: {e}")

    # Calculate returns
    returns_df = pd.DataFrame()
    
    for i, ticker in enumerate(tickers_list):
        if ticker in price_data.columns and len(price_data[ticker].dropna()) > 30:
            returns_df[ticker] = price_data[ticker].pct_change()
        else:
            # Fallback: Simulate daily returns matching the sector profile
            profile = get_sector_default_returns(sector_list[i])
            daily_ret = profile['return'] / 252.0
            daily_vol = profile['volatility'] / np.sqrt(252.0)
            sim_rets = np.random.normal(daily_ret, daily_vol, horizon_days)
            returns_df[ticker] = pd.Series(sim_rets)

    # Covariance and means
    mean_daily_returns = returns_df.mean()
    cov_matrix = returns_df.cov()
    
    # Fill missing values in covariance matrix
    cov_matrix = cov_matrix.fillna(0.0)
    # Ensure diagonal elements are at least daily volatility floor to avoid singular matrix
    for ticker in tickers_list:
        if ticker not in cov_matrix.columns:
            # Add dummy row/column
            cov_matrix[ticker] = 0.0
            cov_matrix.loc[ticker] = 0.0
        if cov_matrix.loc[ticker, ticker] <= 0:
            idx = tickers_list.index(ticker)
            profile = get_sector_default_returns(sector_list[idx])
            cov_matrix.loc[ticker, ticker] = (profile['volatility'] / np.sqrt(252.0)) ** 2

    # Clean up cov matrix indexing to match tickers_list order
    cov_matrix = cov_matrix.loc[tickers_list, tickers_list].values
    mean_daily_returns = mean_daily_returns.reindex(tickers_list).fillna(0.02/252.0).values
    
    # Allocation weights
    weights = np.array(allocation_pcts) / 100.0
    
    # Portfolio expected daily return and volatility
    port_expected_return = np.sum(mean_daily_returns * weights)
    port_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    port_volatility = np.sqrt(port_variance) if port_variance > 0 else 0.01
    
    # Simulation runs
    # We will simulate geometric Brownian motion paths
    # S_t = S_0 * exp((mu - 0.5 * sigma^2)*t + sigma * W_t)
    simulated_paths = np.zeros((horizon_days, num_simulations))
    simulated_paths[0, :] = total_investment
    
    dt = 1 # 1 day step
    for t in range(1, horizon_days):
        # Generate random normal shocks for all simulations
        shocks = np.random.normal(0, 1, num_simulations)
        growth_factor = np.exp((port_expected_return - 0.5 * port_volatility ** 2) * dt + 
                               port_volatility * np.sqrt(dt) * shocks)
        simulated_paths[t, :] = simulated_paths[t-1, :] * growth_factor

    # Analyze outcomes
    final_values = simulated_paths[-1, :]
    expected_final_value = float(np.mean(final_values))
    portfolio_return_pct = float(((expected_final_value - total_investment) / total_investment) * 100)
    
    # CAGR
    cagr = float(((expected_final_value / total_investment) ** (252.0 / horizon_days) - 1) * 100)
    
    # Volatility (Annualized)
    annualized_vol = float(port_volatility * np.sqrt(252) * 100)
    
    # Sharpe Ratio (assuming risk-free rate of 6.5% standard in India)
    rf = 6.5
    sharpe = float((cagr - rf) / annualized_vol) if annualized_vol > 0 else 0.0
    
    # 5% Value at Risk (VaR) -> 5th percentile of portfolio loss
    var_5pct = float(total_investment - np.percentile(final_values, 5))
    var_5pct_pct = float((var_5pct / total_investment) * 100)
    
    # Best & Worst paths
    percentiles = {
        "p5": np.percentile(final_values, 5),
        "p25": np.percentile(final_values, 25),
        "p50": np.percentile(final_values, 50),
        "p75": np.percentile(final_values, 75),
        "p95": np.percentile(final_values, 95),
    }

    # Diversification Score calculation
    # Calculated as weighted volatility / portfolio volatility.
    # A diversified portfolio has a portfolio volatility lower than the weighted sum of individual volatilities.
    indiv_ann_vols = []
    for i, t in enumerate(tickers_list):
        daily_var = cov_matrix[i, i]
        indiv_ann_vols.append(np.sqrt(daily_var) * np.sqrt(252) * 100)
    
    weighted_vol = np.sum(weights * indiv_ann_vols)
    actual_ann_vol = annualized_vol
    
    # Diversification ratio
    div_ratio = weighted_vol / actual_ann_vol if actual_ann_vol > 0 else 1.0
    # Map diversification ratio to 0-100 score (1.0 is no diversification, >1.3 is very good)
    diversification_score = min(100, int((div_ratio - 1.0) * 150 + 20)) if len(tickers_list) > 1 else 10

    return {
        "simulated_paths": simulated_paths, # Daily path values [days, simulations]
        "expected_final_value": round(expected_final_value, 2),
        "portfolio_return_pct": round(portfolio_return_pct, 2),
        "cagr": round(cagr, 2),
        "annualized_volatility": round(annualized_vol, 2),
        "sharpe_ratio": round(sharpe, 2),
        "var_5pct": round(var_5pct, 2),
        "var_5pct_pct": round(var_5pct_pct, 2),
        "diversification_score": int(diversification_score),
        "percentiles": percentiles
    }
