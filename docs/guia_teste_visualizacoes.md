# Guia de Teste das Novas Visualizações

## Como Acessar a Aplicação

1. Abra seu navegador e acesse: http://localhost:8000
2. A aplicação deve carregar com a interface principal

## Novas Funcionalidades Implementadas

### 1. Modo Escuro/Claro
- **Local**: Botão no canto superior direito (ícone de lua/sol)
- **Funcionalidade**: Alterna entre modo claro e escuro
- **Persistência**: A preferência é salva automaticamente

### 2. Dashboard de Visualizações
- **Local**: Na parte inferior da interface, abaixo do grafo
- **Funcionalidade**: Interface por abas com diferentes visualizações
- **Abas disponíveis**:
  - Categorias: Evolução histórica por categorias
  - Geografia: Distribuição geográfica das contribuições
  - Linha do Tempo: Inovações ao longo do tempo
  - Métricas de Rede: Métricas quantitativas da rede
  - Nuvem de Palavras: Palavras mais frequentes nos conteúdos

### 3. Exportação de Grafos
- **Local**: Barra de ferramentas do grafo (botões PNG e SVG)
- **Funcionalidade**: Exporta o grafo atual como imagem PNG ou SVG
- **Como usar**: Clique nos botões PNG ou SVG na barra de ferramentas acima do grafo

### 4. Filtros Avançados
- **Local**: Seção abaixo da linha do tempo
- **Funcionalidade**: Filtra os nós do grafo por:
  - Categoria (Pessoa, Teoria, Tecnologia, Evento)
  - Período (ano inicial e final)
  - Região (por nacionalidade)
- **Como usar**: Marque as opções desejadas e clique em "Aplicar Filtros"

### 5. Comparação de Linhagens
- **Local**: Seção abaixo dos filtros avançados
- **Funcionalidade**: Permite comparar diferentes caminhos históricos
- **Como usar**: 
  1. Clique em "Comparar Linhagens"
  2. Selecione nós no grafo com clique duplo
  3. Clique em "Gerar Comparação" para visualizar

### 6. Notificações Inteligentes
- **Local**: Canto inferior direito da tela
- **Funcionalidade**: Alertas sobre padrões interessantes nos dados
- **Conteúdo**: Informações sobre nós altamente conectados, períodos densos, etc.

## Testes Específicos para Realizar

### Teste 1: Navegação entre Visualizações
1. Acesse o Dashboard de Visualizações
2. Clique em cada aba e verifique se a visualização correspondente é exibida
3. Verifique se todas as visualizações carregam corretamente

### Teste 2: Modo Escuro/Claro
1. Clique no botão de tema no canto superior direito
2. Verifique se a interface muda de modo
3. Recarregue a página e verifique se a preferência é mantida

### Teste 3: Exportação de Grafos
1. Clique no botão PNG ou SVG na barra de ferramentas do grafo
2. Verifique se o download da imagem é iniciado
3. Abra a imagem baixada e verifique sua qualidade

### Teste 4: Filtros Avançados
1. Acesse a seção de filtros avançados
2. Selecione algumas categorias
3. Defina um período
4. Clique em "Aplicar Filtros"
5. Verifique se o grafo é atualizado conforme os filtros

### Teste 5: Responsividade
1. Redimensione a janela do navegador
2. Verifique se todos os elementos se adaptam corretamente
3. Acesse a aplicação em um dispositivo móvel (se possível)

## Problemas Conhecidos e Soluções

### Problema 1: Visualizações não carregam
- **Solução**: Recarregue a página (Ctrl+F5 ou Cmd+Shift+R)

### Problema 2: Filtros não funcionam
- **Solução**: Verifique se há dados no grafo e tente novamente

### Problema 3: Exportação falha
- **Solução**: Verifique se o navegador permite downloads e tente novamente

## Feedback

Por favor, relate qualquer problema ou sugestão através do GitHub ou por e-mail.

## Conclusão

As novas visualizações ampliam significativamente as capacidades analíticas da aplicação, permitindo uma exploração mais rica e detalhada da história da computação através de diferentes perspectivas visuais.