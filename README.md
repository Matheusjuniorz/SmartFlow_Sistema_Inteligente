# ⚡ SmartFlow | Sistema Inteligente de Gestão de TI

![Django](https://img.shields.io/badge/django-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

O **SmartFlow** é uma solução completa para gestão de chamados de TI, projetada para oferecer agilidade, segurança e uma interface de usuário de alto nível. Com foco em produtividade, o sistema permite o controle total de ordens de serviço, clientes e pagamentos em um ambiente moderno.



## ✨ Principais Funcionalidades

- 🛡️ **Autenticação de Dois Fatores (2FA):** Camada extra de segurança via QR Code (Google Authenticator/Authy).
- 🎫 **Gestão de Chamados:** Fluxo completo desde a abertura até o fechamento com mudança de status em tempo real.
- 👥 **Controle de Clientes:** Cadastro e histórico detalhado de interações.
- 💰 **Integração com Mercado Pago:** Webhooks para confirmação automática de pagamentos de serviços.
- 📄 **Exportação de Relatórios:** Geração de PDFs de chamados e Ordens de Serviço (OS) profissionais.
- 🎨 **Interface Premium:** Design moderno com modo escuro (Dark Mode), Glassmorphism e detalhes em vermelho.

## 🚀 Tecnologias Utilizadas

- **Backend:** [Django 6.0](https://www.djangoproject.com/)
- **Frontend:** [Tailwind CSS](https://tailwindcss.com/) (UI Customizada)
- **Segurança:** [Django Two-Factor Auth](https://django-two-factor-auth.readthedocs.io/)
- **Banco de Dados:** SQLite (Desenvolvimento) / PostgreSQL (Sugestão para Produção)
- **Pagamentos:** API Mercado Pago

## 📦 Como Instalar e Rodar o Projeto

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/smartflow.git](https://github.com/seu-usuario/smartflow.git)
   cd smartflow

2. Crie e ative seu ambiente virtual:

Bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

3.Instale as dependências:

Bash
pip install -r requirements.txt

4. Configure as variáveis de ambiente:

Crie um arquivo .env na raiz e adicione suas chaves (Secret Key, Mercado Pago Token, etc).

5. Rode as migrações e inicie o servidor:

Bash
python manage.py migrate
python manage.py runserver
Acesse: http://127.0.0.1:8000/account/login/

🎨 Preview da Interface
Atualmente o sistema conta com uma interface Glassmorphism Dark & Red, focada na redução da fadiga visual e destaque em ações críticas.

#### Tela de Login 
![Login SmartFlow](./screenshots/login.png)

#### Dashboard 
![Dashboard SmartFlow](./screenshots/dashboard.png)

### Chamados
![Chamados Registrados SmartFlow](./screenshots/chamados.png)

### Clientes 
![Gerenciamentos de Clientes SmartFlow](./screenshots/clientes.png)

###  Cadastros de Clientes 
![Cadastros de Clientes SmartFlow](./screenshots/cadastro_cliente.png)

###  Novo Chamado 
![Abrir Novo Chamado SmartFlow](./screenshots/novo_chamado.png)


📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

Desenvolvido por Matheus 🚀


