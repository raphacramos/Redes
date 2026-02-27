def ip_to_int(ip_str):
    # Extrai apenas o IP antes da porta se existir
    ip_only = ip_str.split('/')[0]  # Remove máscara primeiro
    ip_only = ip_only.split(':')[0]  # Remove porta depois
    partes = ip_only.split('.')
    return (int(partes[0]) << 24) | (int(partes[1]) << 16) | (int(partes[2]) << 8) | int(partes[3])

def int_to_ip(ip_int):
    return f"{(ip_int >> 24) & 255}.{(ip_int >> 16) & 255}.{(ip_int >> 8) & 255}.{ip_int & 255}"

def sumarizar_rotas(tabela):
    tabela_sumarizada = {}
    agrupamento = {}
    
    # Agrupa rotas pelo next_hop
    for rede, dados in tabela.items():
        nh = dados['next_hop']
        if nh not in agrupamento:
            agrupamento[nh] = []
        # Só adiciona rotas que são redes IP (contêm '/')
        if '/' in rede:
            agrupamento[nh].append((rede, dados['cost']))
        else:
            # Rotas que não são redes IP (como vizinhos) vão direto para a tabela final
            tabela_sumarizada[rede] = dados
        
    for nh, rotas in agrupamento.items():
        if len(rotas) <= 1:
            # Se tem 0 ou 1 rota, só copia
            for rede, custo in rotas:
                tabela_sumarizada[rede] = {'cost': custo, 'next_hop': nh}
            continue
            
        mudou = True
        max_iteracoes = 10  # Previne loop infinito
        iteracoes = 0
        
        while mudou and len(rotas) > 1 and iteracoes < max_iteracoes:
            iteracoes += 1
            mudou = False
            
            # Ordena por IP
            rotas.sort(key=lambda x: ip_to_int(x[0].split('/')[0]))
            
            novas_rotas = []
            pulou_proximo = False
            
            for i in range(len(rotas)):
                if pulou_proximo:
                    pulou_proximo = False
                    continue
                    
                if i < len(rotas) - 1:
                    ip1_str, mask1_str = rotas[i][0].split('/')
                    ip2_str, mask2_str = rotas[i+1][0].split('/')
                    
                    mask1, mask2 = int(mask1_str), int(mask2_str)
                    ip1, ip2 = ip_to_int(ip1_str), ip_to_int(ip2_str)
                    
                    # Só tenta sumarizar se máscaras forem iguais
                    if mask1 == mask2 and mask1 > 0:  # mask1 > 0 previne /0
                        tamanho_bloco = 1 << (32 - mask1)
                        # Checa se são adjacentes
                        if ip1 ^ ip2 == tamanho_bloco and (ip1 & (tamanho_bloco - 1)) == 0:
                            nova_mask = mask1 - 1
                            novo_ip = ip1 & (0xFFFFFFFF << (32 - nova_mask))
                            maior_custo = max(rotas[i][1], rotas[i+1][1])
                            
                            novas_rotas.append((f"{int_to_ip(novo_ip)}/{nova_mask}", maior_custo))
                            mudou = True
                            pulou_proximo = True
                            continue
                            
                novas_rotas.append(rotas[i])
            rotas = novas_rotas
            
        for rede, custo in rotas:
            tabela_sumarizada[rede] = {'cost': custo, 'next_hop': nh}
            
    return tabela_sumarizada

# Teste local rápido
if __name__ == '__main__':
    tabela_teste = {
        "10.0.0.0/24": {"cost": 0, "next_hop": "10.0.0.0/24"},
        "127.0.0.1:5001": {"cost": 5, "next_hop": "127.0.0.1:5001"},
        "127.0.0.1:5002": {"cost": 10, "next_hop": "127.0.0.1:5002"}
    }

    resultado = sumarizar_rotas(tabela_teste)
    print("Resultado:")
    for rede, dados in resultado.items():
        print(f"  {rede}: custo={dados['cost']}, next_hop={dados['next_hop']}")
