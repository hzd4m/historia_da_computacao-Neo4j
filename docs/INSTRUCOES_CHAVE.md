# Instruções para inserir a OLLAMA API KEY

Peça ao seu irmão para seguir estes passos e enviar o arquivo `.env` preenchido para você (ou colar a chave diretamente no terminal quando solicitado):

1. Abra o arquivo de exemplo `.env.example` que está na raiz do projeto.
2. Crie uma cópia chamada `.env` (no mesmo diretório):

   cp .env.example .env

3. Abra `.env` em um editor e substitua o valor de `OLLAMA_API_KEY` pela chave real fornecida por Ollama (sem aspas):

   OLLAMA_API_KEY=41676338123a4dbbab1b41c24a1f01d2.sIPmeEgQHjSZ-yOMpwe-A3G_

4. Salve o arquivo. NÃO compartilhe esse arquivo por e-mail, chat público ou commit no Git.

5. Opcional: se for enviar o arquivo para você, envie apenas por um canal seguro (ex.: Signal/Telegram/WhatsApp) e depois apague o arquivo recebido do dispositivo intermediário.

6. Como o responsável pelo repositório, você pode carregar as variáveis no seu shell local com o script:

   source scripts/load_env.sh

   Isso carrega `OLLAMA_API_KEY` e outras variáveis definidas em `.env` no seu ambiente atual.

7. Verifique que `.env` está listado em `.gitignore` (já adicionado) para evitar commit acidental.

Segurança:
- A chave é sensível: trate-a como uma credencial privada.
- Se a chave vazar, revogue-a em https://ollama.com/settings/keys e gere uma nova.
