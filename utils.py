def calcular_percentual(meta, resultado):
    if meta and meta != 0:
        return round((resultado / meta) * 100, 1)
    return 0

def calcular_variacao(atual, anterior):
    if anterior == 0:
        return "+0%", "green"
    diff = atual - anterior
    sinal = "+" if diff >= 0 else "-"
    cor = "green" if diff >= 0 else "red"
    percentual = abs(round((diff / anterior) * 100, 1)) if anterior != 0 else 0
    return f"{sinal}{percentual}%", cor
