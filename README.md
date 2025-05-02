# Sistema de Emissão de Senhas para Clínica

Um sistema completo em Python Flask para controle de senhas em clínicas, com interface moderna, real-time, autenticação, relatórios e painel administrativo.

## Funcionalidades

- **Emissão de Senhas**: Paciente escolhe o tipo de atendimento e recebe senha impressa/tela.
- **Monitor de Chamadas**: Painel público em tempo real com notificações sonoras, voz (TTS) e tema escuro.
- **Painel do Operador**: Login, chamada, repetição, finalização de senhas e histórico.
- **Painel Administrativo**:
  - Dashboard com gráficos
  - Relatórios com exportação CSV
  - Gerenciamento de usuários (criar, editar, remover)
  - Gerenciamento de tipos de atendimento (criar, editar, remover)
  - Configurações gerais (nome da clínica, mensagem do painel)
- **Zeramento Diário Automático** das senhas
- **Autenticação**: Usuários e administradores
- **Interface Responsiva**: Bootstrap 5, tema claro/escuro
- **Banco de Dados**: SQLite (pronto para migração)
- **Impressão Automática**: Senhas são impressas automaticamente em impressoras térmicas compatíveis (Linux via CUPS/ESC-POS)
- **Notificação Sonora e Voz**: Todas as chamadas são anunciadas (fila de anúncios), mesmo com múltiplos operadores/guichês.

## Instalação

1. **Clone o repositório**
   ```bash
   git clone <repo-url>
   cd sistema_senhas_flask
   ```

2. **Instale as dependências**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Inicialize o banco de dados e dados iniciais**
   ```bash
   python3 init_db.py
   ```
   Usuários criados:
   - Operador: `operador` / `1234`
   - Admin: `admin` / `admin123`

4. **Execute o sistema**
   ```bash
   python3 run.py
   ```
   Acesse: [http://localhost:5000](http://localhost:5000)

## Impressão de Senhas

- **Linux (Recomendado):**
  - Impressão automática via CUPS e pycups.
  - Compatível com impressoras térmicas ESC/POS (Epson, Bematech, Elgin, Daruma etc).
  - O ticket é centralizado, fonte dupla para o número, corte automático.
  - Configure a impressora no CUPS (http://localhost:631) e teste antes de usar.

- **Windows:**
  - Impressão automática **NÃO SUPORTADA** nativamente.
  - O sistema exibirá a senha na tela, mas não enviará para a impressora diretamente.
  - Para impressão automática em Windows, é necessário adaptar para bibliotecas como `win32print` ou usar um serviço local de spool.
  - **Alternativa:** Imprima manualmente a tela ou utilize um script externo para monitorar e imprimir o arquivo gerado.

## Notificação Sonora e Voz

- O monitor público anuncia todas as senhas chamadas, mesmo se múltiplos operadores chamarem ao mesmo tempo.
- Utiliza áudio local (`/static/audio/notificacao.mp3`) e síntese de voz (Web Speech API, TTS).
- Fila de anúncios garante que cada senha seja anunciada integralmente, sem cortes.
- O botão "Testar Som" permite validar o áudio/voz no navegador do monitor.

## Estrutura de Diretórios

```
sistema_senhas_flask/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── public.py
│   │   ├── operator.py
│   │   └── admin.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── public/
│   │   ├── operator/
│   │   └── admin/
│   └── ...
├── run.py
├── init_db.py
├── requirements.txt
├── static/
│   └── audio/
│       └── notificacao.mp3
└── README.md
```

## Principais Rotas

- `/` — Emissão de senha
- `/monitor` — Painel público de chamadas
- `/operador/login` — Painel do operador
- `/admin/login` — Painel administrativo

## Painel Administrativo

- Dashboard: visão geral, gráfico de senhas por tipo
- Relatórios: filtro por data, exportação CSV
- Usuários: criar, editar, remover
- Tipos: criar, editar, remover
- Configurações: nome da clínica, mensagem do painel

## Tema Escuro

- O sistema suporta tema claro e escuro (botão no monitor).

## Produção

- Recomenda-se executar com `eventlet` para WebSocket:
  ```bash
  python3 run.py
  # ou
  gunicorn -k eventlet -w 1 run:app
  ```

## Troubleshooting (Solução de Problemas)

### Áudio/voz não toca no monitor
- Verifique se o arquivo `static/audio/notificacao.mp3` existe e está acessível.
- Confirme se o navegador do monitor permite reprodução automática de áudio.
- Teste o botão "Testar Som" no monitor para validar áudio e voz.
- Alguns navegadores exigem interação do usuário para liberar o áudio na primeira vez.

### O painel não atualiza em tempo real
- Certifique-se de rodar o servidor Flask com `eventlet` ou outro servidor compatível com WebSocket.
- Verifique se não há firewall bloqueando as portas 5000 (ou a porta configurada).
- Confira se a conexão com a internet/rede está estável.

### Impressora não imprime (Linux)
- Confirme se o CUPS está instalado e a impressora está ativa em http://localhost:631.
- Teste imprimir uma página de teste pelo painel do CUPS.
- Verifique se o nome da impressora está correto nas configurações do sistema.
- Confira se a dependência `pycups` está instalada corretamente.

### Impressora não imprime (Windows)
- Impressão automática não suportada nativamente. Imprima manualmente a senha exibida na tela.
- Para automação, será necessário adaptar o código para usar `win32print` ou outro método.

### Erro ao instalar dependências
- Use Python 3.8 ou superior.
- Atualize o pip: `pip install --upgrade pip`.
- Instale eventlet manualmente se necessário: `pip install eventlet`.

### Banco de dados não inicializa
- Certifique-se de rodar `python3 init_db.py` antes de iniciar o sistema.
- Verifique permissões de escrita na pasta do projeto.

### Outros problemas
- Consulte os logs do terminal para mensagens de erro detalhadas.
- Abra uma issue no repositório com o erro e o contexto.

---

Para dúvidas, sugestões ou melhorias, abra um issue ou contribua com o projeto!
