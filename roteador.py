# -*- coding: utf-8 -*-

import csv
import json
import threading
import time
from argparse import ArgumentParser
import copy

import requests
from flask import Flask, jsonify, request

from sumarizacao import sumarizar_rotas

class Router:
    """
    Representa um roteador que executa o algoritmo de Vetor de Distância.
    """

    def __init__(self, my_address, neighbors, my_network, update_interval=1):
        """
        Inicializa o roteador.

        :param my_address: O endereço (ip:porta) deste roteador.
        :param neighbors: Um dicionário contendo os vizinhos diretos e o custo do link.
                          Ex: {'127.0.0.1:5001': 5, '127.0.0.1:5002': 10}
        :param my_network: A rede que este roteador administra diretamente.
                           Ex: '10.0.1.0/24'
        :param update_interval: O intervalo em segundos para enviar atualizações, o tempo que o roteador espera 
                                antes de enviar atualizações para os vizinhos.        """
        self.my_address = my_address
        self.neighbors = neighbors
        self.my_network = my_network
        self.update_interval = update_interval

        self.routing_table = {}
        
        # 1. Rota para a própria rede (custo 0)
        self.routing_table[self.my_network] = {
            "cost": 0,
            "next_hop": self.my_network
        }
        
        # 2. Rotas para os vizinhos diretos (pegando do dicionário neighbors)
        for vizinho, custo in self.neighbors.items():
            self.routing_table[vizinho] = {
                "cost": custo,
                "next_hop": vizinho
            }

        print("Tabela de roteamento inicial:")
        print(json.dumps(self.routing_table, indent=4))

        # Inicia o processo de atualização periódica em uma thread separada
        self._start_periodic_updates()

    def _start_periodic_updates(self):
        """Inicia uma thread para enviar atualizações periodicamente."""
        thread = threading.Thread(target=self._periodic_update_loop)
        thread.daemon = True
        thread.start()

    def _periodic_update_loop(self):
        """Loop que envia atualizações de roteamento em intervalos regulares."""
        while True:
            time.sleep(self.update_interval)
            print(f"[{time.ctime()}] Enviando atualizações periódicas para os vizinhos...")
            try:
                self.send_updates_to_neighbors()
            except Exception as e:
                print(f"Erro durante a atualização periódida: {e}")

    def send_updates_to_neighbors(self):
        # 1. Cria cópia para não alterar a tabela real do roteador
        tabela_copiada = copy.deepcopy(self.routing_table)
        
        # 2. Aplica a sumarização
        tabela_sumarizada = sumarizar_rotas(tabela_copiada)

        # 3. Monta o pacote e envia
        payload = {
            "sender_address": self.my_address,
            "routing_table": tabela_sumarizada
        }

        for neighbor_address in self.neighbors:
            url = f'http://{neighbor_address}/receive_update'
            try:
                # print(f"Enviando tabela para {neighbor_address}")
                requests.post(url, json=payload, timeout=5)
            except requests.exceptions.RequestException as e:
                pass

# --- API Endpoints ---
# Instância do Flask e do Roteador (serão inicializadas no main)
app = Flask(__name__)
router_instance = None

@app.route('/routes', methods=['GET'])
def get_routes():
    """Endpoint para visualizar a tabela de roteamento atual."""
    # TODO: Aluno! Este endpoint está parcialmente implementado para ajudar na depuração.
    # Você pode mantê-lo como está ou customizá-lo se desejar.
    # - mantenha o routing_table como parte da resposta JSON.
    if router_instance:
        return jsonify({
            "message": "Sucesso",
            "vizinhos" : router_instance.neighbors,
            "my_network": router_instance.my_network,
            "my_address": router_instance.my_address,
            "update_interval": router_instance.update_interval,
            "routing_table": router_instance.routing_table # Exibe a tabela de roteamento atual (a ser implementada)
        })
    return jsonify({"error": "Roteador não inicializado"}), 500

@app.route('/receive_update', methods=['POST'])
def receive_update():
    """Endpoint que recebe atualizações de roteamento de um vizinho."""
    if not request.json:
        return jsonify({"error": "Invalid request"}), 400

    update_data = request.json
    sender_address = update_data.get("sender_address")
    sender_table = update_data.get("routing_table")

    if not sender_address or not isinstance(sender_table, dict):
        return jsonify({"error": "Missing sender_address or routing_table"}), 400

    print(f"Recebida atualização de {sender_address}:")
    print(json.dumps(sender_table, indent=4))

    global router_instance
    
    # 1. Obter o custo do link direto para o remetente
    custo_link_direto = router_instance.neighbors.get(sender_address)
    
    if custo_link_direto is None:
        return jsonify({"error": "Vizinho desconhecido"}), 403
        
    houve_atualizacao = False
    
    # 2. Iterar sobre a tabela recebida
    for rede_destino, info in sender_table.items():
        custo_vizinho = info['cost']
        
        # 3. Matemática do Bellman-Ford
        novo_custo = custo_link_direto + custo_vizinho
        
        # Regras de atualização
        if rede_destino not in router_instance.routing_table:
            # a. Rede nova descoberta
            router_instance.routing_table[rede_destino] = {"cost": novo_custo, "next_hop": sender_address}
            houve_atualizacao = True
            
        elif novo_custo < router_instance.routing_table[rede_destino]["cost"]:
            # b. Caminho mais barato encontrado
            router_instance.routing_table[rede_destino] = {"cost": novo_custo, "next_hop": sender_address}
            houve_atualizacao = True
            
        elif router_instance.routing_table[rede_destino]["next_hop"] == sender_address and router_instance.routing_table[rede_destino]["cost"] != novo_custo:
            # c. Atualização forçada: se o vizinho atual mudou de ideia e o custo piorou, temos que aceitar
            router_instance.routing_table[rede_destino]["cost"] = novo_custo
            houve_atualizacao = True
            
    if houve_atualizacao:
        print(f"[*] Tabela atualizada internamente após receber dados de {sender_address}")

    return jsonify({"status": "success", "message": "Update received"}), 200

if __name__ == '__main__':
    parser = ArgumentParser(description="Simulador de Roteador com Vetor de Distância")
    parser.add_argument('-p', '--port', type=int, default=5000, help="Porta para executar o roteador.")
    parser.add_argument('-f', '--file', type=str, required=True, help="Arquivo CSV de configuração de vizinhos.")
    parser.add_argument('--network', type=str, required=True, help="Rede administrada por este roteador (ex: 10.0.1.0/24).")
    parser.add_argument('--interval', type=int, default=10, help="Intervalo de atualização periódica em segundos.")
    args = parser.parse_args()

    # Leitura do arquivo de configuração de vizinhos
    neighbors_config = {}
    try:
        with open(args.file, mode='r') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                neighbors_config[row['vizinho']] = int(row['custo'])
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração '{args.file}' não encontrado.")
        exit(1)
    except (KeyError, ValueError) as e:
        print(f"Erro no formato do arquivo CSV: {e}. Verifique as colunas 'vizinho' e 'custo'.")
        exit(1)

    my_full_address = f"127.0.0.1:{args.port}"
    print("--- Iniciando Roteador ---")
    print(f"Endereço: {my_full_address}")
    print(f"Rede Local: {args.network}")
    print(f"Vizinhos Diretos: {neighbors_config}")
    print(f"Intervalo de Atualização: {args.interval}s")
    print("--------------------------")

    router_instance = Router(
        my_address=my_full_address,
        neighbors=neighbors_config,
        my_network=args.network,
        update_interval=args.interval
    )

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=args.port, debug=False)