def ip_to_int(ip_str):
    partes = ip_str.split('.')
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
        agrupamento[nh].append((rede, dados['cost']))
        
    for nh, rotas in agrupamento.items():
        mudou = True
        while mudou and len(rotas) > 1:
            mudou = False
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
                    
                    if mask1 == mask2:
                        tamanho_bloco = 1 << (32 - mask1)
                        # Checa se são adjacentes
                        if ip1 ^ ip2 == tamanho_bloco and (ip1 & tamanho_bloco == 0):
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
        "10.0.2.0/24": {"cost": 2, "next_hop": "192.168.0.2:5000"},
        "10.0.3.0/24": {"cost": 3, "next_hop": "192.168.0.2:5000"}
    }
    print(sumarizar_rotas(tabela_teste)) 
    # Deve retornar '10.0.2.0/23' com custo 3
