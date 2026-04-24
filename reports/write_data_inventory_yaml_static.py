from pathlib import Path
import pandas as pd
import yaml

ROOT = Path(r"c:/Users/Jorge/OneDrive - UFV/BAINF/PAPER")
OUT_PATH = ROOT / "reports" / "data_inventory.yml"


def entry(id_, path, category, subcategory, ticker, sheet, header_row, data_start_row, freq, variables, unit, status="OK", notes=""):
    return {
        "id": id_,
        "path": path,
        "category": category,
        "subcategory": subcategory,
        "ticker": ticker,
        "sheet": sheet,
        "header_row": header_row,
        "data_start_row": data_start_row,
        "freq": freq,
        "variables": variables,
        "unit": unit,
        "status": status,
        "notes": notes,
    }


common_price_vars = ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High", "Volume", "Turnover - EUR", "Flow"]
commodity_vars = ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High", "Volume"]
brent_vars = ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High", "Volume", "OI", "Bid", "Ask"]
real_asset_vars = ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High"]

entries = [
    entry("investable_assets_cash_euribor_3m", "data/investable_assets/cash/EURIBOR_3M.xlsx", "investable_assets", "cash", "EURIBOR_3M", "Sheet 1", 10, 11, "daily", ["Exchange Date", "Fixing Value"], "rate_level"),
    entry("investable_assets_commodities_bloomberg_commodity", "data/investable_assets/commodities/Bloomberg_Commodity.xlsx", "investable_assets", "commodities", "Bloomberg_Commodity", "Sheet 1", 31, 32, "daily", commodity_vars, "price_index_level"),
    entry("investable_assets_commodities_brent", "data/investable_assets/commodities/Brent.xlsx", "investable_assets", "commodities", "Brent", "Sheet 1", 34, 35, "daily", brent_vars, "price_index_level"),
    entry("investable_assets_commodities_gold", "data/investable_assets/commodities/Gold.xlsx", "investable_assets", "commodities", "Gold", "Table Data", 2, 3, "daily", ["Date", "Close"], "price_index_level"),
    entry("investable_assets_equity_cac40", "data/investable_assets/equity/CAC 40.xlsx", "investable_assets", "equity", "CAC 40", "Sheet 1", 30, 31, "daily", common_price_vars, "price_index_level"),
    entry("investable_assets_equity_dax", "data/investable_assets/equity/DAX.xlsx", "investable_assets", "equity", "DAX", "Sheet 1", 29, 30, "daily", common_price_vars, "price_index_level"),
    entry("investable_assets_equity_eurostoxx50", "data/investable_assets/equity/EuroStoxx50.xlsx", "investable_assets", "equity", "EuroStoxx50", "Sheet 1", 33, 34, "daily", common_price_vars, "price_index_level"),
    entry("investable_assets_equity_ftse_mib", "data/investable_assets/equity/FTSE_MIB.xlsx", "investable_assets", "equity", "FTSE_MIB", "Sheet 1", 31, 32, "daily", common_price_vars, "price_index_level"),
    entry("investable_assets_equity_ibex35", "data/investable_assets/equity/IBEX35.xlsx", "investable_assets", "equity", "IBEX35", "Sheet 1", 30, 31, "daily", common_price_vars, "price_index_level"),
    entry("investable_assets_equity_stoxxeurope600", "data/investable_assets/equity/StoxxEurope600.xlsx", "investable_assets", "equity", "StoxxEurope600", "Sheet 1", 33, 34, "daily", common_price_vars, "price_index_level"),
    entry("investable_assets_real_assets_ftse_epra_nareit_europe", "data/investable_assets/real_assets/FTSE_EPRA_NAREIT_Europe.xlsx", "investable_assets", "real_assets", "FTSE_EPRA_NAREIT_Europe", "Sheet 1", 19, 20, "daily", real_asset_vars, "price_index_level"),

    entry("regime_variables_global_dxy_usd_index", "data/regime_variables/global/DXY_USD_Index.xlsx", "regime_variables", "global", "DXY_USD_Index", "Sheet 1", 10, 11, "daily", ["Exchange Date", "Trade Price"], "fx_index_level"),
    entry("regime_variables_global_us_10y_yield", "data/regime_variables/global/US_10Y_Yield.xlsx", "regime_variables", "global", "US_10Y_Yield", "Historical Values", 16, 17, "daily", ["Period", "aUSEBM10Y"], "yield_level"),
    entry("regime_variables_global_world_manufacturing_pmi", "data/regime_variables/global/World_Manufacturing_PMI.xlsx", "regime_variables", "global", "World_Manufacturing_PMI", "Historical Values", 19, 20, "monthly", ["Period", "aXWPMIMQA"], "diffusion_index"),

    entry("regime_variables_growth_eurozona_unemployment", "data/regime_variables/growth/Eurozona_Unemployment.xlsx", "regime_variables", "growth", "Eurozona_Unemployment", "Historical Values", 19, 20, "monthly", ["Period", "aEUUNRAR", "pEUUNR=M", "pEUUNR=L", "pEUUNR=H"], "macro_level"),
    entry("regime_variables_growth_eurozone_gdp_revised_qq", "data/regime_variables/growth/Eurozone_GDP_Revised_QQ.xlsx", "regime_variables", "growth", "Eurozone_GDP_Revised_QQ", "Historical Values", 28, 29, "quarterly", ["Period", "pEUGDPP=M", "pEUGDPP=L", "pEUGDPP=H", "pEUGDF=M", "pEUGDF=L", "pEUGDF=H"], "macro_level"),
    entry("regime_variables_growth_eurozone_industrial_production", "data/regime_variables/growth/Eurozone_Industrial_Production.xlsx", "regime_variables", "growth", "Eurozone_Industrial_Production", "Historical Values", 19, 20, "monthly", ["Period", "aXZIPAR", "pEUIP=M", "pEUIP=L", "pEUIP=H"], "macro_level"),
    entry("regime_variables_growth_eurozone_pmi_manufactoring", "data/regime_variables/growth/Eurozone_PMI_Manufactoring.xlsx", "regime_variables", "growth", "Eurozone_PMI_Manufactoring", "Historical Values", 20, 21, "monthly", ["Period", "pEUPMMF=M", "pEUPMMF=L", "pEUPMMF=H", "aEUPMIA/A", "pEUPMI=M"], "diffusion_index"),
    entry("regime_variables_growth_eurozone_pmi_services", "data/regime_variables/growth/Eurozone_PMI_Services.xlsx", "regime_variables", "growth", "Eurozone_PMI_Services", "Historical Values", 20, 21, "monthly", ["Period", "pEUPMSF=M", "pEUPMSF=L", "pEUPMSF=H", "aEUPMISA/A", "pEUPMIS=M"], "diffusion_index"),
    entry("regime_variables_growth_germany_gdp_detailed_qq", "data/regime_variables/growth/Germany_GDP_Detailed_QQ.xlsx", "regime_variables", "growth", "Germany_GDP_Detailed_QQ", "Historical Values", 29, 30, "quarterly", ["Period", "pDEGDF=M", "pDEGDF=L", "pDEGDF=H", "aDEGDPAR", "pDEGDP=M", "pDEGDP=L", "pDEGDP=H"], "macro_level"),
    entry("regime_variables_growth_spain_gdp_final_qq", "data/regime_variables/growth/Spain_GDP_Final_QQ.xlsx", "regime_variables", "growth", "Spain_GDP_Final_QQ", "Historical Values", 28, 29, "quarterly", ["Period", "pESGDFQ=M", "pESGDFQ=L", "pESGDFQ=H", "aESGDPQAR", "pESGDPQ=M", "pESGDPQ=L", "pESGDPQ=H"], "macro_level"),

    entry("regime_variables_inflation_eurozone_hicp", "data/regime_variables/inflation/Eurozone_HICP.xlsx", "regime_variables", "inflation", "Eurozone_HICP", "Historical Values", 33, 34, "monthly", ["Period", "aXZHICAR", "pEUHIC=M", "pEUHIC=L", "pEUHIC=H"], "inflation_level"),
    entry("regime_variables_inflation_eurozone_hicp_core", "data/regime_variables/inflation/Eurozone_HICP_Core.xlsx", "regime_variables", "inflation", "Eurozone_HICP_Core", "Historical Values", 16, 17, "monthly", ["Period", "aXZCPCOREF"], "inflation_level"),
    entry("regime_variables_inflation_eurozone_ppi", "data/regime_variables/inflation/Eurozone_PPI.xlsx", "regime_variables", "inflation", "Eurozone_PPI", "Historical Values", None, None, "monthly", [], "inflation_level", status="EMPTY_METADATA_ONLY", notes="metadata only in current workbook"),
    entry("regime_variables_inflation_germany_hicp", "data/regime_variables/inflation/Germany_HICP.xlsx", "regime_variables", "inflation", "Germany_HICP", "Historical Values", 20, 21, "monthly", ["Period", "pDEHIP=M", "pDEHIP=L", "pDEHIP=H", "aDEHICPAR", "pDEHICP=M", "pDEHICP=L", "pDEHICP=H"], "inflation_level", status="NEEDS_REFRESH", notes="Refinitiv formula block; refresh in Excel to populate cached values"),
    entry("regime_variables_inflation_spain_hicp", "data/regime_variables/inflation/Spain_HICP.xlsx", "regime_variables", "inflation", "Spain_HICP", "Historical Values", 19, 20, "monthly", ["Period", "aESHCPAR", "pESHCP=M", "pESHCP=L", "pESHCP=H", "pESHICP=M"], "inflation_level"),

    entry("regime_variables_monetary_ecb_balance_sheet", "data/regime_variables/monetary/ECB_Balance_Sheet.xlsx", "regime_variables", "monetary", "ECB_Balance_Sheet", "Balance Sheet", None, None, None, [], "balance_sheet_level", status="WRONG_ENTITY", notes="company fundamentals workbook, not a timeseries"),
    entry("regime_variables_monetary_ecb_deposit_facility_rate", "data/regime_variables/monetary/ECB_Deposit_Facility_Rate.xlsx", "regime_variables", "monetary", "ECB_Deposit_Facility_Rate", "Historical Values", 16, 17, "monthly", ["Period", "aXZDEPF"], "rate_level"),
    entry("regime_variables_monetary_ecb_main_refinancing_rate", "data/regime_variables/monetary/ECB_Main_Refinancing_Rate.xlsx", "regime_variables", "monetary", "ECB_Main_Refinancing_Rate", "Historical Values", 16, 17, "monthly", ["Period", "aXZECB"], "rate_level"),
    entry("regime_variables_monetary_germany_10y_yield", "data/regime_variables/monetary/Germany_10Y_Yield.xlsx", "regime_variables", "monetary", "Germany_10Y_Yield", "Historical Values", 16, 17, "monthly", ["Period", "aDEGBOND"], "yield_level"),
    entry("regime_variables_monetary_germany_2y_yield", "data/regime_variables/monetary/Germany_2Y_Yield.xlsx", "regime_variables", "monetary", "Germany_2Y_Yield", "Historical Values", None, None, None, [], "yield_level", status="EMPTY_METADATA_ONLY", notes="metadata only in current workbook"),

    entry("regime_variables_sentiment_eurozone_consumer_confidence", "data/regime_variables/sentiment/Eurozone_Consumer_Confidence.xlsx", "regime_variables", "sentiment", "Eurozone_Consumer_Confidence", "Historical Values", 20, 21, "monthly", ["Period", "Consumer Confid. Flash * (First Release)", "Poll", "Min", "Max", "Consumer Confid. Final * (First Release)", "Poll"], "sentiment_index"),
    entry("regime_variables_sentiment_eurozone_economic_sentiment_indicator", "data/regime_variables/sentiment/Eurozone_Economic_Sentiment_Indicator.xlsx", "regime_variables", "sentiment", "Eurozone_Economic_Sentiment_Indicator", "Historical Values", 19, 20, "monthly", ["Period", "aXZECOSAG", "pEUECOS=M", "pEUECOS=L", "pEUECOS=H"], "sentiment_index"),
    entry("regime_variables_sentiment_zew_germany", "data/regime_variables/sentiment/ZEW_Germany.xlsx", "regime_variables", "sentiment", "ZEW_Germany", "Historical Values", 19, 20, "monthly", ["Period", "aDEZEWSAR", "pDEZEWS=M", "pDEZEWS=L", "pDEZEWS=H"], "sentiment_index", status="NEEDS_REFRESH", notes="Refinitiv formula block; refresh in Excel to populate cached values"),

    entry("regime_variables_sovereign_yields_belgium_longterm_6plus", "data/regime_variables/sovereign_yields/Belgium_LongTerm_6Plus.xlsx", "regime_variables", "sovereign_yields", "Belgium_LongTerm_6Plus", "Historical Values", 16, 17, "monthly", ["Period", "aBEGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_france_longterm_7plus", "data/regime_variables/sovereign_yields/France_LongTerm_7Plus.xlsx", "regime_variables", "sovereign_yields", "France_LongTerm_7Plus", "Historical Values", 16, 17, "monthly", ["Period", "aFRGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_germany_10y", "data/regime_variables/sovereign_yields/Germany_10Y.xlsx", "regime_variables", "sovereign_yields", "Germany_10Y", "Historical Values", 16, 17, "monthly", ["Period", "aDEGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_italy_mixedmaturity", "data/regime_variables/sovereign_yields/Italy_MixedMaturity.xlsx", "regime_variables", "sovereign_yields", "Italy_MixedMaturity", "Historical Values", 16, 17, "monthly", ["Period", "aITGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_netherlands_10y", "data/regime_variables/sovereign_yields/Netherlands_10Y.xlsx", "regime_variables", "sovereign_yields", "Netherlands_10Y", "Historical Values", 16, 17, "monthly", ["Period", "aNLGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_portugal_10y", "data/regime_variables/sovereign_yields/Portugal_10Y.xlsx", "regime_variables", "sovereign_yields", "Portugal_10Y", "Historical Values", 16, 17, "monthly", ["Period", "aPTGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_spain_longterm", "data/regime_variables/sovereign_yields/Spain_LongTerm.xlsx", "regime_variables", "sovereign_yields", "Spain_LongTerm", "Historical Values", 16, 17, "monthly", ["Period", "aESGBOND"], "yield_level"),
    entry("regime_variables_sovereign_yields_uk_longterm_20plus", "data/regime_variables/sovereign_yields/UK_LongTerm_20Plus.xlsx", "regime_variables", "sovereign_yields", "UK_LongTerm_20Plus", "Historical Values", 16, 17, "monthly", ["Period", "aGBGBOND"], "yield_level"),

    entry("regime_variables_volatility_eurostoxx50_realizedvol", "data/regime_variables/volatility/EuroStoxx50_RealizedVol.xlsx", "regime_variables", "volatility", "EuroStoxx50_RealizedVol", "Sheet 1", 19, 20, "daily", ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High"], "volatility_index_level"),
    entry("regime_variables_volatility_move", "data/regime_variables/volatility/MOVE.xlsx", "regime_variables", "volatility", "MOVE", "Sheet 1", 19, 20, "daily", ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High"], "volatility_index_level"),
    entry("regime_variables_volatility_vix", "data/regime_variables/volatility/VIX.xlsx", "regime_variables", "volatility", "VIX", "VIX_History", 1, 2, "daily", ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"], "volatility_index_level"),
    entry("regime_variables_volatility_vstoxx", "data/regime_variables/volatility/VSTOXX.xlsx", "regime_variables", "volatility", "VSTOXX", "Sheet 1", 19, 20, "daily", ["Exchange Date", "Close", "Net", "%Chg", "Open", "Low", "High"], "volatility_index_level"),
]

entries = sorted(entries, key=lambda x: x["path"])

payload = {
    "version": 1,
    "generated_at": pd.Timestamp.utcnow().isoformat(),
    "rules": {
        "header_row": "row immediately above the first observation row",
        "data_start_row": "first observation row with a cached date; manual overrides are used for formula-driven sheets that require Excel refresh",
        "freq": "inferred from cached dates when available",
        "variables": "raw column labels from the detected header row",
    },
    "datasets": entries,
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True, width=140)

print(f"wrote {OUT_PATH}")
print(f"datasets={len(entries)}")
