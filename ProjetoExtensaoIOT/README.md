# AulaMais — projeto de extensão

Protótipo educacional em desenvolvimento. A versão atual funciona com um computador ou celular e um navegador compatível; não exige compra nem instalação de dispositivos IoT dedicados.

## Executar

Instale as dependências e inicie o servidor:

```powershell
pip install -r requirements.txt
python run.py
```

O modo de depuração e recarga automática fica desligado por padrão enquanto o servidor aceita conexões da rede local. Para desenvolvimento no PowerShell, habilite-o apenas em uma rede confiável com `$env:AULAMAIS_DEBUG="1"` antes de `python run.py`.

Para executar as verificações automatizadas do projeto:

```powershell
python -m unittest discover -s tests -v
```

O servidor mostra um endereço HTTPS e um QR code para abrir o sistema em outro aparelho conectado à mesma rede. Para a demonstração, os participantes podem apenas escanear o QR code e usar o site pelo navegador; não precisam instalar o AulaMais. O notebook que executa o servidor precisa permanecer ligado e na mesma rede Wi-Fi.

## O que funciona nesta versão

- Cadastro, login e organização de aulas por conta.
- Fotos do quadro enviadas pelo celular ou computador.
- Transcrição de fala pelo recurso de reconhecimento de voz do navegador. A disponibilidade depende do navegador, aparelho e conexão; a transcrição pode conter erros.
- Consulta e busca nos trechos transcritos, anotações, leitura em voz alta e download dos dados da conta.
- Ajustes de acessibilidade guardados no navegador do aparelho.
- Notificações push de aula iniciada, concluída e foto salva. Ative em Configurações em cada aparelho; o navegador precisa permitir notificações e o servidor precisa estar acessível por HTTPS confiável. No iPhone/iPad, adicione o site à Tela de Início para receber push.

O certificado HTTPS local é de desenvolvimento: quando criado pelo próprio AulaMais, é autoassinado; se você configurou o `mkcert`, ele é assinado por uma autoridade local confiável apenas nos aparelhos em que essa autoridade foi instalada. Por isso, alguns celulares podem bloquear o acesso ou mostrar um aviso de segurança. A navegação pelo site não exige instalar o AulaMais, mas este certificado local não fica confiável automaticamente nos celulares dos participantes. As notificações push exigem HTTPS confiável em cada aparelho e permissão de notificação. Para uma apresentação com vários celulares, a opção mais simples é publicar o sistema em um domínio com certificado HTTPS válido. No iPhone/iPad, também é necessário adicionar o site à Tela de Início para receber push.

O AulaMais não grava arquivos de áudio e ainda não gera resumos por IA, perguntas de revisão ou progresso de estudo. O serviço de reconhecimento de fala do navegador pode processar áudio externamente, conforme o navegador usado.

## Dados e uso em atividades

O banco, fotos e transcrições ficam na pasta `data/` do computador que executa o servidor. O Perfil permite baixar uma cópia ZIP e excluir a conta e seus dados desta instalação. Esta versão não configura cópias de segurança automáticas; quem administra a instalação deve proteger os arquivos e decidir como guardá-los.

A chave privada VAPID das notificações é criada automaticamente em `data/vapid_private.pem`; mantenha esse arquivo junto com o banco e não o publique. Em produção, defina `VAPID_SUBJECT` para um endereço de contato válido no formato `mailto:contato@seudominio.com`.

Antes de registrar uma aula, explique a atividade e obtenha as autorizações e consentimentos pedidos pela escola e pelo projeto de extensão. Evite registrar informações pessoais ou sensíveis. Consulte também a Política de privacidade e os Termos na página inicial.
