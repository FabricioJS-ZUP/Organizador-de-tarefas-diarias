import requests
import re

CLIENT_ID = "e709e0c7-efe2-446b-bf80-63577776995b"
CLIENT_KEY = "Qew70yoxvwI5grTYr5OjLPOPc2Piib9Rv9Y6D9fE5gb7tm0E65HCg50jX5O9L2d8"
REALM = "zup"
AGENT_ID = "01K0C6DKXF6Z0G0F0R8FM3NBAK"


def ler_tarefas():
    print("Digite suas tarefas do dia, uma por linha! Pressione ENTER em branco para finalizar as suas tarefas!")
    tarefas = []
    while True:
        tarefa = input(f"Tarefa {len(tarefas)+1}: ").strip()
        if not tarefa:
            break
        tarefas.append(tarefa)
    return tarefas

def ler_pomodoros_periodo():
    while True:
        try:
            pomodoros_manha = int(input("Quantos pomodoros para a manhã? "))
            pomodoros_tarde = int(input("Quantos pomodoros para a tarde? "))
            if pomodoros_manha < 0 or pomodoros_tarde < 0:
                print("Valores devem ser positivos.")
                continue
            if pomodoros_manha == 0 and pomodoros_tarde == 0:
                print("Defina ao menos um pomodoro para algum período.")
                continue
            return pomodoros_manha, pomodoros_tarde
        except ValueError:
            print("Por favor, digite números inteiros válidos.")

def montar_prompt(tarefas, pomodoros_manha, pomodoros_tarde):
    texto = (
        "Minhas tarefas para o meu dia:\n"
        + "\n".join(f"- {t}" for t in tarefas)
        + f"\n\nDistribua-as em tarefas em blocos de pomodoro, sendo:\n"
        f"- {pomodoros_manha} pomodoros da manhã\n"
        f"- {pomodoros_tarde} pomodoros à tarde\n"
        "Retorne apenas a lista, sem explicações, sem títulos, sem resumo e sem duplicar tarefas "
        "Use bullet points (-), uma tarefa por pomodoro, separando manhã e tarde por uma linha '---------'. "
        "Não inclua textos extras. Deixe o mais limpo possível!"
    )
    return texto

def obter_jwt_token():
    url = f"https://idm.stackspot.com/{REALM}/oidc/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_KEY
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(url, data=data, headers=headers)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    else:
        print(f"Erro ao obter token: {resp.status_code} - {resp.text}")
        return None

def enviar_para_agent(prompt, jwt_token):
    url = f"https://genai-inference-app.stackspot.com/v1/agent/{AGENT_ID}/chat"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "streaming": False,
        "user_prompt": prompt,
        "stackspot_knowledge": False,
        "return_ks_in_response": True
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        resposta = resp.json()
        return resposta.get("answer") or resposta.get("response") or resposta
    else:
        print(f"Erro {resp.status_code}: {resp.text}")
        return None

def limpar_resposta(resposta):
    linhas = resposta.splitlines()
    tarefas = []
    bullet_regex = re.compile(r"^\s*[-•]\s*(.+)")
    separador_regex = re.compile(r"^-{3,}$")
    for linha in linhas:
        if bullet_regex.match(linha):
            tarefa = bullet_regex.match(linha).group(1)
            tarefa = re.sub(r"\s*\(Pomodoro\s*\d+\)", "", tarefa).strip()
            tarefas.append(f"- {tarefa}")
        elif separador_regex.match(linha):
            tarefas.append("---------")
    if not tarefas:
        num_regex = re.compile(r"^\s*\d+[-.\)]\s*(.+)")
        for linha in linhas:
            if num_regex.match(linha):
                tarefa = num_regex.match(linha).group(1)
                tarefa = re.sub(r"\s*\(Pomodoro\s*\d+\)", "", tarefa).strip()
                tarefas.append(f"- {tarefa}")
            elif separador_regex.match(linha):
                tarefas.append("---------")
    return "\n".join(tarefas)

if __name__ == "__main__":
    tarefas = ler_tarefas()
    if not tarefas:
        print("Nenhuma tarefa inserida.")
        exit(0)
    pomodoros_manha, pomodoros_tarde = ler_pomodoros_periodo()
    prompt = montar_prompt(tarefas, pomodoros_manha, pomodoros_tarde)

    print("\nObtendo token de autenticação...")
    jwt_token = obter_jwt_token()
    if not jwt_token:
        exit(1)

    print("\nEnviando suas tarefas para o Agent do StackSpot...\n")
    resposta = enviar_para_agent(prompt, jwt_token)
    if resposta:
        print("\nPlano sugerido pelo Agent:\n")
        resposta_texto = resposta.get("message") or ""
        print(limpar_resposta(resposta_texto))

    else:
        print("Não foi possível obter uma resposta do Agent.")