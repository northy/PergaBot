# PergaBot
PergaBot é um programa feito para a interação automática ou semi-automática com o pergamum por meio de CLI.

## Instalação: 
Para instalar o software, basta clonar o repositório
```sh
$ git clone https://github.com/northy/pergabot.git
```
E baixar as dependências de bibliotecas
```sh
$ pip install -r requirements.txt
$ pipenv sync
```

## Uso:
```sh
$ ./(instituição).py [opções] ... [-d driver | -m matrícula | -p senha] ...
```
### Instituições atualmente implementadas:
* [UFFS]
### Opções e argumentos:
| Argumento | Função |
| ------ | ------ |
| -h  \| --help | Mostra uma mensagem de ajuda e sai |
| -v  \| --version | Imprime a versão do PergaBot e sai |
| -a  \| --auto | modo automático, renova todos os livros marcados como "Precisa de atenção" (padrão: falso) |
| -m  _matrícula_ | Argumento para prover a matrícula na inicialização |
| -p _senha_ | Argumento para prover a senha do pergamum na inicialização |
| -t _tempo_ | Tempo em dias para marcar livro como  "Precisa de atenção" (padrão: 2) |
| -s  \| --status | Somente mostra o seu acervo de livros emprestados. (padrão: falso) |

## Bibliotecas utilizadas:
* [Requests]
* [PrettyTable]
* [BeautifulSoup4]
* [lxml]
* [argparse]

Versão atual: **1.2**

[Requests]: <http://docs.python-requests.org/en/master/>
[PrettyTable]: <https://pypi.org/project/PrettyTable/>
[BeautifulSoup4]: <https://pypi.org/project/beautifulsoup4/>
[lxml]: <https://pypi.org/project/lxml/>
[argparse]: <https://docs.python.org/3/library/argparse.html>
[UFFS]: <http://consulta.uffs.edu.br/pergamum/>