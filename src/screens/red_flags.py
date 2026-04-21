def detect(data: dict) -> list[str]:
    flags = []

    pp = data.get("promoterPledge")
    if pp is not None and pp > 25:
        flags.append("🚨 CRITICAL_PLEDGE_RISK")

    de = data.get("debtToEquity", 0)
    if de and de > 2.0:
        flags.append("🚨 EXCESSIVE_DEBT")

    pe = data.get("peRatio", 0)
    if pe and pe < 0:
        flags.append("🚨 LOSS_MAKING")

    cr = data.get("currentRatio", 0)
    if cr and cr < 1.0 and cr > 0:
        flags.append("🚨 LIQUIDITY_CRISIS")

    mc = data.get("marketCapCr", 0)
    if mc and mc < 200:
        flags.append("⚠️ MICRO_CAP")

    return flags
