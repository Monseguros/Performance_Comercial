def calcular_percentual(meta, resultado):
    if meta == 0:
        return 0
    return round((resultado / meta) * 100)

def calcular_variacao(resultado_atual, resultado_anterior):
    if resultado_anterior == 0:
        return "+100%", "green" if resultado_atual > 0 else "gray"
    variacao = ((resultado_atual - resultado_anterior) / resultado_anterior) * 100
    sinal = "+" if variacao >= 0 else "-"
    cor = "green" if variacao >= 0 else "red"
    return f"{sinal}{abs(round(variacao))}%", cor

