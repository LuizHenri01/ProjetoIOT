# AulaMais — projeto de extensão

Protótipo educacional em desenvolvimento. A versão atual funciona com um computador ou celular e um navegador compatível; não exige compra nem instalação de dispositivos IoT dedicados.

## Executar

Instale as dependências e inicie o servidor:

```powershell
pip install -r requirements.txt
python run.py
```

Para executar as verificações automatizadas do projeto:

```powershell
python -m unittest discover -s tests -v
```

O servidor mostra um endereço HTTPS e um QR code para abrir o sistema em outro aparelho conectado à mesma rede. O certificado local pode gerar um aviso no navegador durante a demonstração.

## O que funciona nesta versão

- Cadastro, login e organização de aulas por conta.
- Fotos do quadro enviadas pelo celular ou computador.
- Transcrição de fala pelo recurso de reconhecimento de voz do navegador. A disponibilidade depende do navegador, aparelho e conexão; a transcrição pode conter erros.
- Consulta e busca nos trechos transcritos, anotações, leitura em voz alta e download dos dados da conta.
- Ajustes de acessibilidade guardados no navegador do aparelho.

O AulaMais não grava arquivos de áudio e ainda não gera resumos por IA, perguntas de revisão ou progresso de estudo. O serviço de reconhecimento de fala do navegador pode processar áudio externamente, conforme o navegador usado.

## Dados e uso em atividades

O banco, fotos e transcrições ficam na pasta `data/` do computador que executa o servidor. O Perfil permite baixar uma cópia ZIP e excluir a conta e seus dados desta instalação. Esta versão não configura cópias de segurança automáticas; quem administra a instalação deve proteger os arquivos e decidir como guardá-los.

Antes de registrar uma aula, explique a atividade e obtenha as autorizações e consentimentos pedidos pela escola e pelo projeto de extensão. Evite registrar informações pessoais ou sensíveis. Consulte também a Política de privacidade e os Termos na página inicial.
