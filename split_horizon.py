"""
Split Horizon - Técnica para mitigar o problema de contagem ao infinito.

Princípio: ao anunciar a tabela de roteamento para um vizinho,
não inclua rotas cujo next_hop seja o próprio vizinho.
Isso evita que o vizinho "aprenda" de volta uma rota que ele mesmo ensinou.
"""


def apply_split_horizon(routing_table: dict, neighbor_address: str) -> dict:
    """
    Aplica Split Horizon filtrando rotas que têm o vizinho como next_hop.

    Args:
        routing_table (dict): Tabela de roteamento no formato:
            {
                "10.0.1.0/24": { "cost": 1, "next_hop": "127.0.0.1:5001" },
                "10.0.2.0/24": { "cost": 2, "next_hop": "127.0.0.1:5002" },
                ...
            }
        neighbor_address (str): Endereço IP:porta do vizinho destinatário
            (ex: "127.0.0.1:5001").

    Returns:
        dict: Nova tabela sem as rotas cujo next_hop é o vizinho informado.
    """
    filtered_table = {
        network: route_info
        for network, route_info in routing_table.items()
        if route_info.get("next_hop") != neighbor_address
    }
    return filtered_table


# Testes
if __name__ == "__main__":
    # Tabela de exemplo baseada no formato do projeto
    routing_table = {
        "10.0.0.0/24": {"cost": 0,  "next_hop": "10.0.0.0/24"},      # rede local (custo 0)
        "10.0.1.0/24": {"cost": 1,  "next_hop": "127.0.0.1:5001"},    # via vizinho B
        "10.0.2.0/24": {"cost": 2,  "next_hop": "127.0.0.1:5002"},    # via vizinho C
        "10.0.3.0/24": {"cost": 3,  "next_hop": "127.0.0.1:5001"},    # via vizinho B (multi-hop)
    }

    neighbor = "127.0.0.1:5001"

    print("=== Tabela original ===")
    for net, info in routing_table.items():
        print(f"  {net}: {info}")

    filtered = apply_split_horizon(routing_table, neighbor)

    print(f"\n=== Tabela após Split Horizon (vizinho: {neighbor}) ===")
    for net, info in filtered.items():
        print(f"  {net}: {info}")

    print(f"\nRotas removidas (next_hop == {neighbor}):")
    removed = {k: v for k, v in routing_table.items() if k not in filtered}
    for net, info in removed.items():
        print(f"  {net}: {info}")

    # --- Assertions ---
    assert "10.0.1.0/24" not in filtered, "ERRO: rota via vizinho B deveria ter sido removida"
    assert "10.0.3.0/24" not in filtered, "ERRO: rota via vizinho B deveria ter sido removida"
    assert "10.0.0.0/24" in filtered,     "ERRO: rede local não deveria ser removida"
    assert "10.0.2.0/24" in filtered,     "ERRO: rota via vizinho C não deveria ser removida"
    assert routing_table is not filtered,  "ERRO: a tabela original não deve ser modificada"

    print("\n Todos os testes passaram!")