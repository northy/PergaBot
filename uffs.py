#!/usr/bin/env python

import requests, os, sys, argparse, textwrap
from getpass import getpass
from prettytable import PrettyTable
from pergabot import Pergabot, versionStr

if os.name == 'nt':
	os.system("title PergaBot")

class helpFormatter(argparse.RawDescriptionHelpFormatter) :
	def add_usage(self,usage,actions,groups,prefix=None) :
		if prefix is None :
			prefix = "Uso: "
		return super(helpFormatter, self).add_usage(usage,actions,groups,prefix)

def readArgs() :
	helpEpilog = ""
	#leitura e implementação dos argumentos
	parser = argparse.ArgumentParser(description="PergaBot é um programa feito para a interação automática ou semi-automática com o pergamum por meio de CLI", add_help=False, formatter_class=helpFormatter, epilog=textwrap.dedent(helpEpilog))
	parser._positionals.title = "Argumentos posicionais"
	parser._optionals.title = "Argumentos opcionais"
	parser.add_argument("-h","--help",action="help",default=argparse.SUPPRESS,help="Mostra esta mensagem de ajuda e sai")
	parser.add_argument("-v","--version",help="Imprime a versão do PergaBot e sai",action="version", version=f"PergaBot {versionStr}")
	parser.add_argument("-a","--auto",help="Modo automático, renova todos os livros marcados como \"Precisa de atenção\" (padrão: falso)", action="store_true")
	parser.add_argument("-m",help="Argumento para prover a matrícula na inicialização", default='', type=str, dest="mat")
	parser.add_argument("-p",help="Argumento para prover a senha do pergamum na inicialização", default='', type=str, dest="pwd")
	parser.add_argument("-t",help="Tempo em dias para marcar livro como  \"Precisa de atenção\" (padrão: 2)", default=2, type=int, dest="criticalTime")
	parser.add_argument("-s","--status",help="Somente mostra o seu acervo de livros emprestados. (padrão: falso)", action="store_true")
	args=parser.parse_args()
	return args

def main(args) :
	statusMode = args.status
	mat = args.mat
	pwd = args.pwd
	autoMode = args.auto
	criticalTime = args.criticalTime
	
	pb = Pergabot(verbose=True)

	pb.set_login_url("http://consulta.uffs.edu.br/pergamum/biblioteca_s/php/login_usu.php") #URL de login ao pergamum
	pb.set_dashboard_url("http://consulta.uffs.edu.br/pergamum/biblioteca_s/meu_pergamum/index.php") #URL do painel do pergamum (quando o usuário já está logado)

	#Dados para o request
	if (mat=='' or pwd=='') : print("\nInsira os dados para login no pergamum...")
	if (mat=='') : mat=input("Matricula: ")
	if (pwd=='') : pwd=getpass("Senha: ")
	print()
	pb.set_login_password(mat,pwd)
	
	pb.login()
	print()
	
	books = pb.get_books()
	
	print("Livros pendentes:")
	if (books==None) : print("NENHUM"); exit(0) ##
	t = PrettyTable(['Nome', 'Data de expiraçação'])
	for i in range(len(books)) :
		t.add_row([books[i].name, books[i].expiration_day+(' *' if books[i].needs_renew else '')])
	print(t)
	print('"*" = Precisa de atenção para ser renovado')
	
	if (statusMode) : exit(0)
	
	print()
	
	#Confirmação de quais renovar
	if not(autoMode) :
		print("Quais livros deseja renovar? (0=nenhum) ",end='')
		books_to_renew=list(input().split(','))
		print()
		if len(books_to_renew)==0 or books_to_renew.count('0')>0 : print("Nada para renovar, saindo..."); exit(0) ##
		for b in books_to_renew.copy() :
			if b.find('-')!=-1 :
				for i in range(int(b[0])-1,int(b[2])) :
					books_to_renew.append(i)
			else :
				books_to_renew.append(int(b)-1)
			del books_to_renew[books_to_renew.index(b)]
		books_to_renew=list(set(books_to_renew)); books_to_renew.sort()
	else :
		books_to_renew=[i for i in range(len(books)) if books[i].needs_renew]
		if len(books_to_renew)==0 : print("Nada para renovar, saindo..."); exit(0) ##

	pb.renew(books_to_renew)
		
if __name__=="__main__" :
	args = readArgs()
	main(args)
